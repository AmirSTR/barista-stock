from collections import defaultdict
from typing import Dict, List, Optional
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import async_session_maker
from app.models.product import Product
from app.models.stock import Stock

stoplist_router = Router(name="stoplist")


async def _resolve_db(db: Optional[AsyncSession] = None):
    """Context manager or session resolver for DB sessions in handlers."""
    if db is not None:
        yield db
    else:
        async with async_session_maker() as session:
            yield session


@stoplist_router.message(Command("stoplist", "stop"))
async def stoplist_command_handler(
    message: Message,
    db: Optional[AsyncSession] = None,
):
    """Handler for /stoplist command:

    - Finds all catalog products where available_qty <= 0
    - Groups them by product category
    - Formats clear breakdown
    """
    async for session in _resolve_db(db):
        query = (
            select(Product, Stock)
            .outerjoin(Stock, Product.id == Stock.product_id)
            .where(Product.is_active.is_(True))
            .order_by(Product.category, Product.name)
        )
        res = await session.execute(query)
        rows = res.all()

        # Filter out of stock items (available_qty <= 0 or missing stock row)
        out_of_stock_by_category: Dict[str, List[Product]] = defaultdict(list)
        for prod, stock in rows:
            if stock is None:
                out_of_stock_by_category[prod.category].append(prod)
            else:
                available = stock.real_qty - stock.reserved_qty
                if available <= 0:
                    out_of_stock_by_category[prod.category].append(prod)

        if not out_of_stock_by_category:
            await message.answer("✅ Стоп-лист пуст! Все товары доступны к заказу.")
            return

        lines: List[str] = [
            "🚫 **Стоп-лист товаров на складе (нет в наличии):**",
            "",
        ]

        total_oos = 0
        for category, items in out_of_stock_by_category.items():
            lines.append(f"📁 **{category}**")
            for item in items:
                lines.append(f"• {item.name} — 0 {item.unit}")
                total_oos += 1
            lines.append("")

        lines.append(f"Всего позиций в стопе: **{total_oos}**")

        await message.answer("\n".join(lines))
