import logging
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product
from app.models.stock import Stock
from app.models.supply import SupplyInvoice, SupplyItem, SupplyStatus
from app.schemas.ocr import MatchedSupplyItem

logger = logging.getLogger(__name__)


class SupplyService:
    """Service handling supply invoices, draft lifecycle, and stock balance crediting."""

    @classmethod
    async def create_supply_draft(
        cls,
        session: AsyncSession,
        photo_file_id: str,
        invoice_number: Optional[str],
        matched_items: List[MatchedSupplyItem],
    ) -> SupplyInvoice:
        """Create a draft supply invoice with line items."""
        invoice = SupplyInvoice(
            photo_file_id=photo_file_id,
            invoice_number=invoice_number,
            status=SupplyStatus.DRAFT,
        )
        session.add(invoice)
        await session.flush()

        for item in matched_items:
            supply_item = SupplyItem(
                invoice_id=invoice.id,
                product_id=item.product_id,
                detected_name=item.raw_name,
                quantity=item.quantity,
                confidence_score=item.confidence_score,
            )
            session.add(supply_item)

        await session.commit()

        # Reload with relationships
        query = (
            select(SupplyInvoice)
            .options(
                selectinload(SupplyInvoice.items).selectinload(SupplyItem.product),
            )
            .where(SupplyInvoice.id == invoice.id)
        )
        res = await session.execute(query)
        return res.scalar_one()

    @classmethod
    async def confirm_supply_invoice(
        cls,
        session: AsyncSession,
        invoice_id: int,
    ) -> SupplyInvoice:
        """Confirm a supply invoice and atomically credit stocks for all matched products."""
        query = (
            select(SupplyInvoice)
            .options(
                selectinload(SupplyInvoice.items).selectinload(SupplyItem.product),
            )
            .where(SupplyInvoice.id == invoice_id)
            .with_for_update()
        )
        res = await session.execute(query)
        invoice = res.scalar_one_or_none()

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Накладная #{invoice_id} не найдена",
            )

        if invoice.status == SupplyStatus.CONFIRMED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Накладная #{invoice_id} уже оприходована!",
            )

        # The invoice row lock makes confirmation single-use. Lock all affected
        # stock rows in a stable order to avoid deadlocks between invoices.
        product_ids = sorted({item.product_id for item in invoice.items if item.product_id})
        stocks = {}
        if product_ids:
            stock_res = await session.execute(
                select(Stock)
                .where(Stock.product_id.in_(product_ids))
                .order_by(Stock.product_id)
                .with_for_update()
            )
            stocks = {stock.product_id: stock for stock in stock_res.scalars().all()}

        # Update stocks for matched items
        for item in invoice.items:
            if item.product_id:
                stock = stocks.get(item.product_id)

                if stock:
                    stock.real_qty += item.quantity
                else:
                    stock = Stock(
                        product_id=item.product_id,
                        real_qty=item.quantity,
                        reserved_qty=0.0,
                    )
                    session.add(stock)
                    stocks[item.product_id] = stock

        invoice.status = SupplyStatus.CONFIRMED
        await session.commit()

        # Refresh invoice
        res = await session.execute(query)
        return res.scalar_one()

    @classmethod
    async def cancel_supply_draft(
        cls,
        session: AsyncSession,
        invoice_id: int,
    ) -> Optional[SupplyInvoice]:
        """Cancel or delete a draft supply invoice."""
        query = (
            select(SupplyInvoice)
            .where(SupplyInvoice.id == invoice_id)
            .with_for_update()
        )
        res = await session.execute(query)
        invoice = res.scalar_one_or_none()

        if not invoice:
            return None

        if invoice.status == SupplyStatus.CONFIRMED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Накладная #{invoice_id} уже оприходована и не может быть отменена",
            )

        await session.delete(invoice)
        await session.commit()
        return invoice
