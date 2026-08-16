import asyncio
from typing import List
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cli.seed import seed_database
from app.core.database import Base
from app.db.seed_data import PRODUCTS_DATA
from app.models import Bar, Order, OrderItem, OrderStatus, Product, Stock
from app.schemas.order import OrderCreateRequest, OrderItemInput
from app.services.catalog_service import CatalogService
from app.services.order_service import OrderService
from tests.conftest import test_engine, async_test_session_maker


@pytest.mark.asyncio
async def test_concurrent_orders_no_oversell(db_session: AsyncSession):
    """Simulate parallel concurrent submission of two orders for the same product

    when available stock is exactly 1.0 item. Verifies zero oversell.
    """
    # 1. Setup Bar
    bar = Bar(name="Кофейня Тест Конкурентности", telegram_chat_id=-100111222333, is_active=True)
    db_session.add(bar)

    # 2. Setup Product with real_qty = 1.0, reserved_qty = 0.0
    product = Product(
        sku="SKU-CONC-01",
        name="Эксклюзивный кофе Geisha 1кг",
        category="Кофе, Чай, Дрипы",
        unit="кг",
        is_active=True,
    )
    stock = Stock(real_qty=1.0, reserved_qty=0.0)
    product.stock = stock

    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(bar)
    await db_session.refresh(product)
    product_id = product.id
    bar_id = bar.id

    # 3. Define concurrent worker function with separate sessions
    async def place_order_task():
        async with async_test_session_maker() as session:
            req = OrderCreateRequest(
                bar_id=bar_id,
                items=[OrderItemInput(product_id=product_id, quantity=1.0)],
            )
            return await OrderService.create_order(session, req)

    # 4. Run two order requests simultaneously
    result1, result2 = await asyncio.gather(
        place_order_task(),
        place_order_task(),
    )

    # 5. Analyze results
    results = [result1, result2]
    total_confirmed = sum(item.confirmed_qty for res in results for item in res.items)
    
    # Must never oversell: exactly 1.0 confirmed across both orders
    assert total_confirmed == 1.0, f"Oversell detected! Total confirmed is {total_confirmed}"

    # Exactly one order got confirmed 1.0, the other got 0.0 (out of stock)
    confirmed_counts = [sum(item.confirmed_qty for item in res.items) for res in results]
    assert 1.0 in confirmed_counts
    assert 0.0 in confirmed_counts

    # Check that out-of-stock warning was generated for the second order
    zero_order = next(res for res in results if sum(i.confirmed_qty for i in res.items) == 0.0)
    assert len(zero_order.out_of_stock_items) == 1
    assert zero_order.out_of_stock_items[0].product_id == product_id

    # Check database stock state
    async with async_test_session_maker() as session:
        st_res = await session.execute(select(Stock).where(Stock.product_id == product_id))
        st = st_res.scalar_one()
        assert st.real_qty == 1.0
        assert st.reserved_qty == 1.0
        assert st.available_qty == 0.0


@pytest.mark.asyncio
async def test_concurrent_partial_and_multi_orders(db_session: AsyncSession):
    """Simulate 4 concurrent orders each requesting 2.0 units when total stock is 5.0 units.

    Total requested: 8.0 units. Total confirmed must be exactly 5.0 units with zero oversell.
    """
    bar = Bar(name="Кофейня Мульти-Заказ", is_active=True)
    db_session.add(bar)

    product = Product(
        sku="SKU-CONC-02",
        name="Сироп Соленая карамель 1л",
        category="Сиропы",
        unit="бут",
        is_active=True,
    )
    stock = Stock(real_qty=5.0, reserved_qty=0.0)
    product.stock = stock

    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(bar)
    await db_session.refresh(product)
    product_id = product.id
    bar_id = bar.id

    async def place_order_worker():
        async with async_test_session_maker() as session:
            req = OrderCreateRequest(
                bar_id=bar_id,
                items=[OrderItemInput(product_id=product_id, quantity=2.0)],
            )
            return await OrderService.create_order(session, req)

    # Run 4 simultaneous orders (4 x 2.0 = 8.0 requested vs 5.0 available)
    orders_results = await asyncio.gather(
        place_order_worker(),
        place_order_worker(),
        place_order_worker(),
        place_order_worker(),
    )

    total_confirmed = sum(item.confirmed_qty for res in orders_results for item in res.items)
    assert total_confirmed == 5.0, f"Expected total 5.0 confirmed, got {total_confirmed}"

    # Verify database stock state
    async with async_test_session_maker() as session:
        st_res = await session.execute(select(Stock).where(Stock.product_id == product_id))
        st = st_res.scalar_one()
        assert st.real_qty == 5.0
        assert st.reserved_qty == 5.0
        assert st.available_qty == 0.0


@pytest.mark.asyncio
async def test_catalog_api_grouped_and_is_stop(client: AsyncClient, db_session: AsyncSession):
    """Test GET /api/catalog returns 8 categories and correctly marks is_stop."""
    await seed_database(initial_qty=50.0, create_sample_bars=True, session=db_session)

    # Set one product to 0 stock
    st_res = await db_session.execute(select(Stock).where(Stock.product_id == 1))
    stock1 = st_res.scalar_one()
    stock1.real_qty = 0.0
    stock1.reserved_qty = 0.0
    await db_session.commit()

    resp = await client.get("/api/catalog")
    assert resp.status_code == 200
    catalog = resp.json()

    assert catalog["total_categories"] == 8
    assert catalog["total_products"] == len(PRODUCTS_DATA)

    # Check categories structure
    cat_names = [c["category"] for c in catalog["categories"]]
    assert "Стаканы и крышки" in cat_names
    assert "Кофе, Чай, Дрипы" in cat_names
    assert "Сиропы" in cat_names
    assert "Основы и порошки" in cat_names
    assert "Молоко и напитки" in cat_names
    assert "Десерты и выпечка" in cat_names
    assert "Расходники и упаковка" in cat_names
    assert "Химия и хозтовары" in cat_names

    # Check product 1 has is_stop == True
    first_cat = catalog["categories"][0]
    p1 = next(item for item in first_cat["items"] if item["id"] == 1)
    assert p1["available_qty"] == 0.0
    assert p1["is_stop"] is True

    # Other product has is_stop == False
    p2 = next(item for item in first_cat["items"] if item["id"] != 1)
    assert p2["available_qty"] == 50.0
    assert p2["is_stop"] is False


@pytest.mark.asyncio
async def test_order_ship_and_cancel_api_endpoints(client: AsyncClient, db_session: AsyncSession):
    """Test POST /api/orders, /ship, and /cancel endpoints."""
    await seed_database(initial_qty=50.0, create_sample_bars=True, session=db_session)

    # 1. Create order
    order_req = {
        "bar_id": 1,
        "items": [
            {"product_id": 1, "quantity": 10.0},
            {"product_id": 2, "quantity": 5.0},
        ],
    }
    create_resp = await client.post("/api/orders", json=order_req)
    assert create_resp.status_code == 201
    order_data = create_resp.json()
    order_id = order_data["order_id"]
    assert order_data["status"] == "pending"
    assert len(order_data["items"]) == 2
    assert order_data["items"][0]["confirmed_qty"] == 10.0

    # Verify reserved stock
    st_resp = await client.get("/api/v1/stocks/1")
    assert st_resp.json()["reserved_qty"] == 10.0
    assert st_resp.json()["available_qty"] == 40.0

    # 2. Ship order
    ship_resp = await client.post(f"/api/orders/{order_id}/ship")
    assert ship_resp.status_code == 200
    assert ship_resp.json()["status"] == "shipped"

    # Verify real_qty decreased by 10 and reserved cleared
    st_after_ship = await client.get("/api/v1/stocks/1")
    assert st_after_ship.json()["real_qty"] == 40.0
    assert st_after_ship.json()["reserved_qty"] == 0.0
    assert st_after_ship.json()["available_qty"] == 40.0

    # 3. Create second order to test cancellation
    order2_resp = await client.post(
        "/api/orders",
        json={"bar_id": 1, "items": [{"product_id": 1, "quantity": 15.0}]},
    )
    order2_id = order2_resp.json()["order_id"]

    # Verify reservation of 15
    st2_before = await client.get("/api/v1/stocks/1")
    assert st2_before.json()["reserved_qty"] == 15.0
    assert st2_before.json()["available_qty"] == 25.0

    # Cancel second order
    cancel_resp = await client.post(f"/api/orders/{order2_id}/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"

    # Verify reservation was released
    st2_after = await client.get("/api/v1/stocks/1")
    assert st2_after.json()["real_qty"] == 40.0
    assert st2_after.json()["reserved_qty"] == 0.0
    assert st2_after.json()["available_qty"] == 40.0
