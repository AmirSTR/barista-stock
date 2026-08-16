import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Bar,
    Order,
    OrderItem,
    OrderStatus,
    Product,
    Stock,
    SupplyInvoice,
    SupplyItem,
    SupplyStatus,
)


@pytest.mark.asyncio
async def test_create_bar_and_order(db_session: AsyncSession):
    # Create Bar
    bar = Bar(name="Кофейня на Невском", telegram_chat_id=-100987654321, is_active=True)
    db_session.add(bar)
    await db_session.commit()
    await db_session.refresh(bar)

    assert bar.id is not None
    assert bar.name == "Кофейня на Невском"
    assert bar.telegram_chat_id == -100987654321
    assert bar.is_active is True

    # Create Product
    product = Product(
        sku="SKU-TEST-01",
        name="Эспрессо бленд",
        category="Кофе, Чай, Дрипы",
        unit="кг",
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    # Create Order and OrderItem
    order = Order(bar_id=bar.id, status=OrderStatus.PENDING)
    db_session.add(order)
    await db_session.flush()

    item = OrderItem(order_id=order.id, product_id=product.id, requested_qty=5.0, confirmed_qty=5.0)
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(order)

    assert order.id is not None
    assert order.status == OrderStatus.PENDING
    assert len(order.items) == 1
    assert order.items[0].requested_qty == 5.0


@pytest.mark.asyncio
async def test_stock_hybrid_property(db_session: AsyncSession):
    product = Product(
        sku="SKU-TEST-02",
        name="Сироп Карамель",
        category="Сиропы",
        unit="бут",
        is_active=True,
    )
    stock = Stock(real_qty=50.0, reserved_qty=15.0)
    product.stock = stock

    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(stock)

    # Test Python object property
    assert stock.available_qty == 35.0

    # Test SQL expression in WHERE query
    query = select(Stock).where(Stock.available_qty >= 30.0)
    result = await db_session.execute(query)
    found_stock = result.scalar_one_or_none()
    assert found_stock is not None
    assert found_stock.id == stock.id

    # Test SQL expression where available_qty is filtered out
    query_empty = select(Stock).where(Stock.available_qty > 40.0)
    result_empty = await db_session.execute(query_empty)
    assert result_empty.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_supply_invoice_and_items(db_session: AsyncSession):
    product = Product(
        sku="SKU-TEST-03",
        name="Молоко коровье 3.2%",
        category="Молоко и напитки",
        unit="л",
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    invoice = SupplyInvoice(photo_file_id="tg_photo_file_id_999", status=SupplyStatus.DRAFT)
    db_session.add(invoice)
    await db_session.flush()

    item = SupplyItem(
        invoice_id=invoice.id,
        product_id=product.id,
        detected_name="Молоко 3.2% 1л пастеризованное",
        quantity=60.0,
        confidence_score=0.96,
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(invoice)

    assert invoice.id is not None
    assert invoice.status == SupplyStatus.DRAFT
    assert len(invoice.items) == 1
    assert invoice.items[0].detected_name == "Молоко 3.2% 1л пастеризованное"
    assert invoice.items[0].confidence_score == 0.96


@pytest.mark.asyncio
async def test_ensure_schema_execution(db_session: AsyncSession):
    from app.db.ensure_schema import ensure_schema
    # Should execute without errors on active engine
    await ensure_schema(db_session.bind)
