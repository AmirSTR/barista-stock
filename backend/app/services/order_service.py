import asyncio
from contextlib import asynccontextmanager
from typing import Dict, List, Set
import weakref

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.bot.services.notifier import send_order_to_warehouse
from app.models.bar import Bar
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.stock import Stock
from app.schemas.order import (
    OrderConfirmedItem,
    OrderCreateRequest,
    OrderCreateResultResponse,
    OrderResponse,
    OutOfStockItemWarning,
    PartialItemWarning,
)

# Loop-isolated product locks mapping: loop -> product_id -> Lock
_loop_product_locks: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, Dict[int, asyncio.Lock]]" = (
    weakref.WeakKeyDictionary()
)


def _get_product_lock(product_id: int) -> asyncio.Lock:
    loop = asyncio.get_running_loop()
    if loop not in _loop_product_locks:
        _loop_product_locks[loop] = {}
    locks_map = _loop_product_locks[loop]
    if product_id not in locks_map:
        locks_map[product_id] = asyncio.Lock()
    return locks_map[product_id]


@asynccontextmanager
async def _lock_products(product_ids: List[int]):
    """Acquire asyncio locks for products in sorted order to prevent deadlocks."""
    sorted_ids = sorted(list(set(product_ids)))
    acquired_locks: List[asyncio.Lock] = []
    for pid in sorted_ids:
        lock = _get_product_lock(pid)
        await lock.acquire()
        acquired_locks.append(lock)
    try:
        yield
    finally:
        for lock in reversed(acquired_locks):
            lock.release()


class OrderService:
    @staticmethod
    async def create_order(db: AsyncSession, order_in: OrderCreateRequest) -> OrderCreateResultResponse:
        """Atomically create an order with row-level stock locking (FOR UPDATE)

        and handle full, partial, or out-of-stock reservations.
        """
        # 1. Verify bar
        bar_result = await db.execute(select(Bar).where(Bar.id == order_in.bar_id))
        bar = bar_result.scalar_one_or_none()
        if not bar:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bar with ID {order_in.bar_id} not found",
            )
        if not bar.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bar '{bar.name}' is currently inactive",
            )

        if not order_in.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order must contain at least one item",
            )

        # 2. Extract and sort unique product IDs to prevent deadlocks across concurrent requests
        product_ids: List[int] = sorted(list(set(item.product_id for item in order_in.items)))

        async with _lock_products(product_ids):
            # 3. Lock stock rows with SELECT ... FOR UPDATE
            stocks_query = (
                select(Stock)
                .where(Stock.product_id.in_(product_ids))
                .with_for_update()
            )
            stocks_res = await db.execute(stocks_query)
            stocks_map: Dict[int, Stock] = {s.product_id: s for s in stocks_res.scalars().all()}

            # 4. Fetch Products for metadata
            prods_res = await db.execute(select(Product).where(Product.id.in_(product_ids)))
            prods_map: Dict[int, Product] = {p.id: p for p in prods_res.scalars().all()}

            # Validate that all requested products exist
            for pid in product_ids:
                if pid not in prods_map:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Product with ID {pid} not found in catalog",
                    )

            # 5. Create Order record
            order = Order(
                bar_id=order_in.bar_id,
                status=OrderStatus.PENDING,
            )
            db.add(order)
            await db.flush()

            confirmed_items_list: List[OrderConfirmedItem] = []
            partial_items_list: List[PartialItemWarning] = []
            out_of_stock_list: List[OutOfStockItemWarning] = []

            # 6. Process items and calculate available stock
            for item_in in order_in.items:
                prod = prods_map[item_in.product_id]
                stock = stocks_map.get(item_in.product_id)

                if stock is None:
                    # If stock row missing, create it
                    stock = Stock(product_id=prod.id, real_qty=0.0, reserved_qty=0.0)
                    db.add(stock)
                    await db.flush()
                    stocks_map[prod.id] = stock

                available = stock.real_qty - stock.reserved_qty
                req_qty = item_in.quantity

                if available >= req_qty:
                    # Case 1: Full reservation
                    stock.reserved_qty += req_qty
                    conf_qty = req_qty
                elif available > 0:
                    # Case 2: Partial reservation
                    stock.reserved_qty += available
                    conf_qty = available
                    partial_items_list.append(
                        PartialItemWarning(
                            product_id=prod.id,
                            name=prod.name,
                            sku=prod.sku,
                            requested_qty=req_qty,
                            confirmed_qty=conf_qty,
                            available_before=available,
                            message=f"Запрошено {req_qty} {prod.unit}, подтверждено {conf_qty} {prod.unit} из-за остатка на складе",
                        )
                    )
                else:
                    # Case 3: Out of stock (available <= 0)
                    conf_qty = 0.0
                    out_of_stock_list.append(
                        OutOfStockItemWarning(
                            product_id=prod.id,
                            name=prod.name,
                            sku=prod.sku,
                            requested_qty=req_qty,
                            available_before=max(0.0, available),
                            message=f"Товар '{prod.name}' закончился на складе (в стоп-листе)",
                        )
                    )

                # Create OrderItem
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=prod.id,
                    requested_qty=req_qty,
                    confirmed_qty=conf_qty,
                )
                db.add(order_item)
                await db.flush()

                confirmed_items_list.append(
                    OrderConfirmedItem(
                        id=order_item.id,
                        product_id=prod.id,
                        name=prod.name,
                        sku=prod.sku,
                        unit=prod.unit,
                        requested_qty=req_qty,
                        confirmed_qty=conf_qty,
                    )
                )

            # 7. Commit atomic transaction
            await db.commit()
            await db.refresh(order)

            # 8. Dispatch notification to warehouse Telegram chat
            try:
                await send_order_to_warehouse(
                    order_id=order.id,
                    bar_name=bar.name,
                    items=confirmed_items_list,
                    out_of_stock_items=out_of_stock_list,
                )
            except Exception:
                # Notifications should never block or fail the order creation transaction
                pass

            return OrderCreateResultResponse(
                id=order.id,
                order_id=order.id,
                bar_id=order.bar_id,
                status=order.status,
                created_at=order.created_at,
                items=confirmed_items_list,
                partial_items=partial_items_list,
                out_of_stock_items=out_of_stock_list,
            )

    @staticmethod
    async def ship_order(db: AsyncSession, order_id: int) -> OrderResponse:
        """Ship order: deduct confirmed quantities from real_qty and release reserved_qty."""
        query = (
            select(Order)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
            .where(Order.id == order_id)
            .with_for_update()
        )
        res = await db.execute(query)
        order = res.scalar_one_or_none()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with ID {order_id} not found",
            )

        if order.status == OrderStatus.SHIPPED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order {order_id} has already been shipped",
            )
        if order.status == OrderStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order {order_id} is cancelled and cannot be shipped",
            )

        product_ids = sorted(list(set(item.product_id for item in order.items if item.confirmed_qty)))
        async with _lock_products(product_ids):
            if product_ids:
                stocks_res = await db.execute(
                    select(Stock).where(Stock.product_id.in_(product_ids)).with_for_update()
                )
                stocks_map = {s.product_id: s for s in stocks_res.scalars().all()}

                for item in order.items:
                    if item.confirmed_qty and item.confirmed_qty > 0:
                        stock = stocks_map.get(item.product_id)
                        if stock:
                            stock.real_qty = max(0.0, stock.real_qty - item.confirmed_qty)
                            stock.reserved_qty = max(0.0, stock.reserved_qty - item.confirmed_qty)

            order.status = OrderStatus.SHIPPED
            await db.commit()
            await db.refresh(order)
            return order

    @staticmethod
    async def cancel_order(db: AsyncSession, order_id: int) -> OrderResponse:
        """Cancel order: release reserved_qty back to warehouse."""
        query = (
            select(Order)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
            .where(Order.id == order_id)
            .with_for_update()
        )
        res = await db.execute(query)
        order = res.scalar_one_or_none()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with ID {order_id} not found",
            )

        if order.status == OrderStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order {order_id} is already cancelled",
            )
        if order.status == OrderStatus.SHIPPED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order {order_id} has already been shipped and cannot be cancelled",
            )

        product_ids = sorted(list(set(item.product_id for item in order.items if item.confirmed_qty)))
        async with _lock_products(product_ids):
            if product_ids:
                stocks_res = await db.execute(
                    select(Stock).where(Stock.product_id.in_(product_ids)).with_for_update()
                )
                stocks_map = {s.product_id: s for s in stocks_res.scalars().all()}

                for item in order.items:
                    if item.confirmed_qty and item.confirmed_qty > 0:
                        stock = stocks_map.get(item.product_id)
                        if stock:
                            stock.reserved_qty = max(0.0, stock.reserved_qty - item.confirmed_qty)

            order.status = OrderStatus.CANCELLED
            await db.commit()
            await db.refresh(order)
            return order
