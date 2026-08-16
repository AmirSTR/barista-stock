from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.product import Product
from app.models.supply import SupplyInvoice, SupplyItem, SupplyStatus
from app.schemas.supply import (
    SupplyInvoiceCreate,
    SupplyInvoiceResponse,
    SupplyItemResponse,
    SupplyItemUpdate,
)
from app.services.supply_service import SupplyService

router = APIRouter()


@router.get("/", response_model=List[SupplyInvoiceResponse], summary="List supply invoices")
async def list_invoices(
    status_filter: Optional[SupplyStatus] = Query(None, alias="status", description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(SupplyInvoice)
        .options(selectinload(SupplyInvoice.items).selectinload(SupplyItem.product))
        .order_by(SupplyInvoice.created_at.desc())
    )
    if status_filter is not None:
        query = query.where(SupplyInvoice.status == status_filter)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{invoice_id}", response_model=SupplyInvoiceResponse, summary="Get supply invoice details")
async def get_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(SupplyInvoice)
        .options(selectinload(SupplyInvoice.items).selectinload(SupplyItem.product))
        .where(SupplyInvoice.id == invoice_id)
    )
    result = await db.execute(query)
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Supply invoice {invoice_id} not found")
    return invoice


@router.post("/", response_model=SupplyInvoiceResponse, status_code=status.HTTP_201_CREATED, summary="Create a supply invoice from OCR")
async def create_invoice(
    invoice_in: SupplyInvoiceCreate,
    db: AsyncSession = Depends(get_db),
):
    invoice = SupplyInvoice(
        photo_file_id=invoice_in.photo_file_id,
        invoice_number=invoice_in.invoice_number,
        status=SupplyStatus.DRAFT,
    )
    db.add(invoice)
    await db.flush()

    for item_in in invoice_in.items:
        # Validate product_id if provided
        if item_in.product_id:
            p_res = await db.execute(select(Product).where(Product.id == item_in.product_id))
            if not p_res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product with ID {item_in.product_id} not found",
                )

        item = SupplyItem(
            invoice_id=invoice.id,
            product_id=item_in.product_id,
            detected_name=item_in.detected_name,
            quantity=item_in.quantity,
            confidence_score=item_in.confidence_score,
        )
        db.add(item)

    await db.commit()
    return await get_invoice(invoice.id, db)


@router.patch("/items/{item_id}", response_model=SupplyItemResponse, summary="Update supply item (link product or edit quantity)")
async def update_supply_item(
    item_id: int,
    item_in: SupplyItemUpdate,
    db: AsyncSession = Depends(get_db),
):
    query = select(SupplyItem).options(selectinload(SupplyItem.product)).where(SupplyItem.id == item_id)
    result = await db.execute(query)
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Supply item {item_id} not found")

    if item_in.product_id is not None:
        p_res = await db.execute(select(Product).where(Product.id == item_in.product_id))
        if not p_res.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product ID {item_in.product_id} not found")
        item.product_id = item_in.product_id

    if item_in.quantity is not None:
        item.quantity = item_in.quantity
    if item_in.detected_name is not None:
        item.detected_name = item_in.detected_name

    await db.commit()
    await db.refresh(item)
    return item


@router.post("/{invoice_id}/confirm", response_model=SupplyInvoiceResponse, summary="Confirm supply invoice and add to warehouse stock")
async def confirm_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await SupplyService.confirm_supply_invoice(db, invoice_id)
