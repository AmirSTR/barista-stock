from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.bar import Bar
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.stock import Stock
from app.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate

router = APIRouter()


@router.get("/", response_model=List[OrderResponse], summary="List orders")
async def list_orders(
    bar_id: Optional[int] = Query(None, description="Filter by bar ID"),
    order_status: Optional[OrderStatus] = Query(None, alias="status", description="Filter by order status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product)
        )
        .order_by(Order.created_at.desc())
    )

    if bar_id is not None:
        query = query.where(Order.bar_id == bar_id)
    if order_status is not None:
        query = query.where(Order.status == order_status)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{order_id}", response_model=OrderResponse, summary="Get order details")
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .where(Order.id == order_id)
    )
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order with ID {order_id} not found")
    return order


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED, summary="Create a new bar order")
async def create_order(
    order_in: OrderCreate,
    db: AsyncSession = Depends(get_db),
):
    # Verify bar existence
    bar_result = await db.execute(select(Bar).where(Bar.id == order_in.bar_id))
    bar = bar_result.scalar_one_or_none()
    if not bar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bar with ID {order_in.bar_id} not found")

    order = Order(
        bar_id=order_in.bar_id,
        status=OrderStatus.PENDING,
    )
    db.add(order)
    await db.flush()

    for item_in in order_in.items:
        # Check product
        prod_result = await db.execute(select(Product).where(Product.id == item_in.product_id))
        product = prod_result.scalar_one_or_none()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {item_in.product_id} not found",
            )

        # Update stock reserved_qty
        stock_result = await db.execute(select(Stock).where(Stock.product_id == item_in.product_id))
        stock = stock_result.scalar_one_or_none()
        if stock:
            stock.reserved_qty += item_in.requested_qty

        order_item = OrderItem(
            order_id=order.id,
            product_id=item_in.product_id,
            requested_qty=item_in.requested_qty,
            confirmed_qty=item_in.requested_qty,
        )
        db.add(order_item)

    await db.commit()

    # Reload with relationships
    return await get_order(order.id, db)


@router.patch("/{order_id}/status", response_model=OrderResponse, summary="Update order status")
async def update_order_status(
    order_id: int,
    status_in: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order with ID {order_id} not found")

    old_status = order.status
    new_status = status_in.status

    # Handle transitions
    if old_status != new_status:
        if new_status == OrderStatus.SHIPPED:
            # Deduct from real_qty and release reserved_qty
            for item in order.items:
                stock_result = await db.execute(select(Stock).where(Stock.product_id == item.product_id))
                stock = stock_result.scalar_one_or_none()
                if stock:
                    qty = item.confirmed_qty if item.confirmed_qty is not None else item.requested_qty
                    stock.real_qty = max(0.0, stock.real_qty - qty)
                    stock.reserved_qty = max(0.0, stock.reserved_qty - item.requested_qty)
        elif new_status == OrderStatus.CANCELLED:
            # Release reserved_qty
            if old_status in [OrderStatus.PENDING, OrderStatus.PACKING]:
                for item in order.items:
                    stock_result = await db.execute(select(Stock).where(Stock.product_id == item.product_id))
                    stock = stock_result.scalar_one_or_none()
                    if stock:
                        stock.reserved_qty = max(0.0, stock.reserved_qty - item.requested_qty)

        order.status = new_status

    await db.commit()
    return await get_order(order_id, db)
