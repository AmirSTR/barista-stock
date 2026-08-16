from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.product import Product
from app.models.stock import Stock
from app.schemas.product import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    ProductWithStockResponse,
)

router = APIRouter()


@router.get("/", response_model=List[ProductWithStockResponse], summary="List products with stock")
async def list_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search query in product name or SKU"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    query = select(Product).options(selectinload(Product.stock))

    if category:
        query = query.where(Product.category == category)
    if is_active is not None:
        query = query.where(Product.is_active == is_active)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Product.name.ilike(search_pattern)) | (Product.sku.ilike(search_pattern))
        )

    query = query.order_by(Product.id).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/categories", response_model=List[str], summary="List all distinct product categories")
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product.category).distinct().order_by(Product.category))
    return result.scalars().all()


@router.get("/{product_id}", response_model=ProductWithStockResponse, summary="Get product details")
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    query = select(Product).options(selectinload(Product.stock)).where(Product.id == product_id)
    result = await db.execute(query)
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with ID {product_id} not found")
    return product


@router.post("/", response_model=ProductWithStockResponse, status_code=status.HTTP_201_CREATED, summary="Create product")
async def create_product(
    product_in: ProductCreate,
    db: AsyncSession = Depends(get_db),
):
    # Check if SKU already exists
    existing = await db.execute(select(Product).where(Product.sku == product_in.sku))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with SKU '{product_in.sku}' already exists",
        )

    product = Product(
        sku=product_in.sku,
        name=product_in.name,
        category=product_in.category,
        unit=product_in.unit,
        is_active=product_in.is_active,
    )
    stock = Stock(
        real_qty=product_in.initial_real_qty or 0.0,
        reserved_qty=0.0,
    )
    product.stock = stock

    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.patch("/{product_id}", response_model=ProductWithStockResponse, summary="Update product")
async def update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: AsyncSession = Depends(get_db),
):
    query = select(Product).options(selectinload(Product.stock)).where(Product.id == product_id)
    result = await db.execute(query)
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with ID {product_id} not found")

    update_data = product_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(product, field, val)

    await db.commit()
    await db.refresh(product)
    return product
