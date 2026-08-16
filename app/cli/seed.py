"""CLI tool to reset and seed the coffee chain database.

Usage:
    python -m app.cli.seed [--initial-qty 50.0] [--no-bars]
"""

import argparse
import asyncio
from typing import List

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker, engine
from app.db.seed_data import PRODUCTS_DATA, SAMPLE_BARS
from app.models import (
    Bar,
    Order,
    OrderItem,
    Product,
    Stock,
    SupplyInvoice,
    SupplyItem,
)


async def clear_database(session: AsyncSession) -> None:
    """Clear all records from database tables in correct dependency order."""
    print("🧹 Cleaning database tables...")
    await session.execute(delete(SupplyItem))
    await session.execute(delete(SupplyInvoice))
    await session.execute(delete(OrderItem))
    await session.execute(delete(Order))
    await session.execute(delete(Stock))
    await session.execute(delete(Product))
    await session.execute(delete(Bar))
    await session.commit()
    print("✅ All tables cleared.")


async def seed_database(
    initial_qty: float = 50.0,
    create_sample_bars: bool = True,
    session: AsyncSession = None,
) -> int:
    """Seed products, stocks, and sample bars."""
    close_session_at_end = False
    if session is None:
        session = async_session_maker()
        close_session_at_end = True

    try:
        await clear_database(session)

        # 1. Seed Bars
        if create_sample_bars:
            print(f"🏢 Creating {len(SAMPLE_BARS)} sample coffee bars...")
            for bar_data in SAMPLE_BARS:
                bar = Bar(
                    name=bar_data["name"],
                    telegram_chat_id=bar_data["telegram_chat_id"],
                    is_active=bar_data["is_active"],
                )
                session.add(bar)
            await session.flush()
            print(f"✅ {len(SAMPLE_BARS)} bars created.")

        # 2. Seed Products and Stocks
        print(f"📦 Seeding {len(PRODUCTS_DATA)} catalog items with initial stock {initial_qty}...")
        
        products_to_add: List[Product] = []
        for idx, item in enumerate(PRODUCTS_DATA, start=1):
            sku = f"SKU-{idx:04d}"
            product = Product(
                sku=sku,
                name=item["name"],
                category=item["category"],
                unit=item["unit"],
                is_active=True,
            )
            # Create corresponding stock with real_qty = 50.0, reserved_qty = 0.0
            stock = Stock(
                real_qty=initial_qty,
                reserved_qty=0.0,
            )
            product.stock = stock
            products_to_add.append(product)

        session.add_all(products_to_add)
        await session.commit()

        # 3. Verification
        count_result = await session.execute(select(Product))
        products_count = len(count_result.scalars().all())

        stock_result = await session.execute(select(Stock))
        stocks_count = len(stock_result.scalars().all())

        print("--------------------------------------------------")
        print(f"🎉 Successfully seeded {products_count} products (SKU-0001 ... SKU-{products_count:04d})")
        print(f"📊 Created {stocks_count} stock records with real_qty={initial_qty:.1f}, reserved_qty=0.0, available_qty={initial_qty:.1f}")
        print("--------------------------------------------------")
        return products_count

    finally:
        if close_session_at_end:
            await session.close()


async def main():
    parser = argparse.ArgumentParser(description="Seed the coffee chain database")
    parser.add_argument(
        "--initial-qty",
        type=float,
        default=50.0,
        help="Initial stock quantity for each product (default: 50.0)",
    )
    parser.add_argument(
        "--no-bars",
        action="store_true",
        help="Do not seed sample bars",
    )
    args = parser.parse_args()

    print(f"🚀 Starting database seeding...")
    await seed_database(
        initial_qty=args.initial_qty,
        create_sample_bars=not args.no_bars,
    )
    await engine.dispose()
    print("✨ Database seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())
