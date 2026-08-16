import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cli.seed import seed_database
from app.db.seed_data import PRODUCTS_DATA, CATEGORIES
from app.models import Bar, Order, OrderStatus, Product, Stock, SupplyInvoice, SupplyStatus


@pytest.mark.asyncio
async def test_seed_database_execution(db_session: AsyncSession):
    # Test seeding into test database
    count = await seed_database(initial_qty=50.0, create_sample_bars=True, session=db_session)
    assert count == len(PRODUCTS_DATA)

    # Check products
    products_res = await db_session.execute(select(Product))
    products = products_res.scalars().all()
    assert len(products) == len(PRODUCTS_DATA)

    # Check SKUs format
    assert products[0].sku == "SKU-0001"
    assert products[-1].sku == f"SKU-{len(PRODUCTS_DATA):04d}"

    # Check Stocks
    stocks_res = await db_session.execute(select(Stock))
    stocks = stocks_res.scalars().all()
    assert len(stocks) == len(PRODUCTS_DATA)
    for s in stocks:
        assert s.real_qty == 50.0
        assert s.reserved_qty == 0.0
        assert s.available_qty == 50.0

    # Check Bars
    bars_res = await db_session.execute(select(Bar))
    bars = bars_res.scalars().all()
    assert len(bars) > 0


@pytest.mark.asyncio
async def test_bars_api_crud(client: AsyncClient):
    # 1. Create Bar
    create_resp = await client.post(
        "/api/v1/bars/",
        json={"name": "Тестовая Кофейня", "telegram_chat_id": -100555666777, "is_active": True},
    )
    assert create_resp.status_code == 201
    bar_data = create_resp.json()
    bar_id = bar_data["id"]
    assert bar_data["name"] == "Тестовая Кофейня"

    # 2. List Bars
    list_resp = await client.get("/api/v1/bars/")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # 3. Patch Bar
    patch_resp = await client.patch(
        f"/api/v1/bars/{bar_id}",
        json={"name": "Обновленная Кофейня"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "Обновленная Кофейня"

    # 4. Get Bar
    get_resp = await client.get(f"/api/v1/bars/{bar_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Обновленная Кофейня"

    # 5. Delete Bar
    del_resp = await client.delete(f"/api/v1/bars/{bar_id}")
    assert del_resp.status_code == 204


@pytest.mark.asyncio
async def test_products_and_stocks_api(client: AsyncClient, db_session: AsyncSession):
    # Seed products
    await seed_database(initial_qty=50.0, create_sample_bars=True, session=db_session)

    # 1. List Products
    list_resp = await client.get("/api/v1/products/")
    assert list_resp.status_code == 200
    products = list_resp.json()
    assert len(products) == len(PRODUCTS_DATA)
    assert products[0]["stock"]["real_qty"] == 50.0
    assert products[0]["stock"]["available_qty"] == 50.0

    # 2. Filter by category
    cat_resp = await client.get("/api/v1/products/?category=Сиропы")
    assert cat_resp.status_code == 200
    syrups = cat_resp.json()
    assert len(syrups) == 16
    for s in syrups:
        assert s["category"] == "Сиропы"

    # 3. Search query
    search_resp = await client.get("/api/v1/products/?search=Cafiza")
    assert search_resp.status_code == 200
    cafiza_items = search_resp.json()
    assert len(cafiza_items) >= 1

    # 4. Adjust Stock
    product_id = products[0]["id"]
    adj_resp = await client.post(
        f"/api/v1/stocks/{product_id}/adjust",
        json={"delta_real_qty": 25.0, "delta_reserved_qty": 5.0},
    )
    assert adj_resp.status_code == 200
    stock_data = adj_resp.json()
    assert stock_data["real_qty"] == 75.0
    assert stock_data["reserved_qty"] == 5.0
    assert stock_data["available_qty"] == 70.0


@pytest.mark.asyncio
async def test_orders_flow(client: AsyncClient, db_session: AsyncSession):
    await seed_database(initial_qty=50.0, create_sample_bars=True, session=db_session)

    # Fetch bars and products
    bars_res = await client.get("/api/v1/bars/")
    bar_id = bars_res.json()[0]["id"]

    prods_res = await client.get("/api/v1/products/?limit=2")
    p1 = prods_res.json()[0]["id"]
    p2 = prods_res.json()[1]["id"]

    # 1. Create Order
    order_create_resp = await client.post(
        "/api/v1/orders/",
        json={
            "bar_id": bar_id,
            "items": [
                {"product_id": p1, "requested_qty": 10.0},
                {"product_id": p2, "requested_qty": 5.0},
            ],
        },
    )
    assert order_create_resp.status_code == 201
    order_data = order_create_resp.json()
    order_id = order_data["id"]
    assert order_data["status"] == "pending"
    assert len(order_data["items"]) == 2

    # Check stock reserved_qty increased
    s1_resp = await client.get(f"/api/v1/stocks/{p1}")
    assert s1_resp.json()["reserved_qty"] == 10.0
    assert s1_resp.json()["available_qty"] == 40.0

    # 2. Update status to SHIPPED
    status_resp = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"status": "shipped"},
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "shipped"

    # Check real_qty decreased by 10 and reserved released
    s1_shipped = await client.get(f"/api/v1/stocks/{p1}")
    assert s1_shipped.json()["real_qty"] == 40.0
    assert s1_shipped.json()["reserved_qty"] == 0.0
    assert s1_shipped.json()["available_qty"] == 40.0


@pytest.mark.asyncio
async def test_supply_invoice_flow(client: AsyncClient, db_session: AsyncSession):
    await seed_database(initial_qty=50.0, create_sample_bars=True, session=db_session)

    prods_res = await client.get("/api/v1/products/?limit=1")
    product_id = prods_res.json()[0]["id"]

    # 1. Create Invoice with OCR items
    inv_create = await client.post(
        "/api/v1/supplies/",
        json={
            "photo_file_id": "file_telegram_invoice_123",
            "items": [
                {
                    "product_id": product_id,
                    "detected_name": "Стакан 0,1",
                    "quantity": 100.0,
                    "confidence_score": 0.98,
                }
            ],
        },
    )
    assert inv_create.status_code == 201
    invoice = inv_create.json()
    inv_id = invoice["id"]
    assert invoice["status"] == "draft"

    # 2. Confirm Invoice -> Stock should increase from 50 to 150
    confirm_resp = await client.post(f"/api/v1/supplies/{inv_id}/confirm")
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["status"] == "confirmed"

    stock_resp = await client.get(f"/api/v1/stocks/{product_id}")
    assert stock_resp.json()["real_qty"] == 150.0
    assert stock_resp.json()["available_qty"] == 150.0
