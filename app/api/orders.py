from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.order import (
    OrderCreateRequest,
    OrderCreateResultResponse,
    OrderResponse,
    OrderStatusUpdate,
)
from app.services.order_service import OrderService

router = APIRouter()


@router.post(
    "",
    response_model=OrderCreateResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new bar order with atomic row-level locking",
)
@router.post(
    "/",
    response_model=OrderCreateResultResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def create_order(
    order_in: OrderCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Place an order for a coffee bar.

    - Uses `SELECT ... FOR UPDATE` row-level stock locks in an isolated transaction.
    - If `available >= quantity`: reserves full quantity.
    - If `0 < available < quantity`: reserves remainder and returns warning in `partial_items`.
    - If `available <= 0`: does not reserve and returns warning in `out_of_stock_items`.
    """
    return await OrderService.create_order(db, order_in)


@router.post(
    "/{order_id}/ship",
    response_model=OrderResponse,
    summary="Ship order and deduct physical stock",
)
async def ship_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Transitions order status to `shipped` and atomically deducts confirmed quantities

    from physical stock (`real_qty -= confirmed_qty`, `reserved_qty -= confirmed_qty`).
    """
    return await OrderService.ship_order(db, order_id)


@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    summary="Cancel order and release reserved stock",
)
async def cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Transitions order status to `cancelled` and releases reserved stock back to warehouse

    (`reserved_qty -= confirmed_qty`).
    """
    return await OrderService.cancel_order(db, order_id)


@router.get(
    "",
    response_model=List[OrderResponse],
    summary="List orders",
)
@router.get(
    "/",
    response_model=List[OrderResponse],
    include_in_schema=False,
)
async def list_orders(
    bar_id: Optional[int] = Query(None, description="Filter by bar ID"),
    order_status: Optional[OrderStatus] = Query(None, alias="status", description="Filter by order status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .order_by(Order.created_at.desc())
    )
    if bar_id is not None:
        query = query.where(Order.bar_id == bar_id)
    if order_status is not None:
        query = query.where(Order.status == order_status)

    query = query.offset(skip).limit(limit)
    res = await db.execute(query)
    return res.scalars().all()


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order by ID",
)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .where(Order.id == order_id)
    )
    res = await db.execute(query)
    order = res.scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found",
        )
    return order


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Update order status (compatible helper)",
)
async def update_order_status(
    order_id: int,
    status_in: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    if status_in.status == OrderStatus.SHIPPED:
        return await OrderService.ship_order(db, order_id)
    elif status_in.status == OrderStatus.CANCELLED:
        return await OrderService.cancel_order(db, order_id)
    else:
        order = await get_order(order_id, db)
        order.status = status_in.status
        await db.commit()
        await db.refresh(order)
        return order
