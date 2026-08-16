from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.stock import Stock
from app.schemas.stock import StockAdjustment, StockResponse, StockUpdate

router = APIRouter()


@router.get("/", response_model=List[StockResponse], summary="List all stock levels")
async def list_stocks(
    min_available: Optional[float] = Query(None, description="Filter stocks where available_qty >= min_available"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Stock)
    if min_available is not None:
        query = query.where(Stock.available_qty >= min_available)
    query = query.order_by(Stock.product_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{product_id}", response_model=StockResponse, summary="Get stock for product")
async def get_stock(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Stock).where(Stock.product_id == product_id))
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Stock for product ID {product_id} not found")
    return stock


@router.patch("/{product_id}", response_model=StockResponse, summary="Set stock values explicitly")
async def update_stock(
    product_id: int,
    stock_in: StockUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Stock).where(Stock.product_id == product_id))
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Stock for product ID {product_id} not found")

    if stock_in.real_qty is not None:
        stock.real_qty = stock_in.real_qty
    if stock_in.reserved_qty is not None:
        stock.reserved_qty = stock_in.reserved_qty

    await db.commit()
    await db.refresh(stock)
    return stock


@router.post("/{product_id}/adjust", response_model=StockResponse, summary="Adjust stock values by delta")
async def adjust_stock(
    product_id: int,
    adj: StockAdjustment,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Stock).where(Stock.product_id == product_id))
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Stock for product ID {product_id} not found")

    if adj.delta_real_qty:
        if stock.real_qty + adj.delta_real_qty < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Resulting real_qty cannot be negative (current: {stock.real_qty}, delta: {adj.delta_real_qty})",
            )
        stock.real_qty += adj.delta_real_qty

    if adj.delta_reserved_qty:
        if stock.reserved_qty + adj.delta_reserved_qty < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Resulting reserved_qty cannot be negative (current: {stock.reserved_qty}, delta: {adj.delta_reserved_qty})",
            )
        stock.reserved_qty += adj.delta_reserved_qty

    await db.commit()
    await db.refresh(stock)
    return stock
