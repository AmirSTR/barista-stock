import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import CallbackQuery, Chat, Message, User
from aiogram.filters import CommandObject
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.config import bot_settings
from app.bot.handlers.barista import (
    bind_command_handler,
    change_bar_callback,
    select_bar_callback,
    start_handler,
)
from app.bot.handlers.stoplist import stoplist_command_handler
from app.bot.handlers.warehouse import pack_order_callback, ship_order_callback
from app.bot.keyboards.barista import get_barista_main_keyboard, get_bar_selection_keyboard
from app.bot.keyboards.warehouse import get_order_warehouse_keyboard
from app.bot.services.notifier import format_order_message, send_order_to_warehouse
from app.models.bar import Bar
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.stock import Stock
from app.schemas.order import OrderCreateRequest, OrderItemInput
from app.services.order_service import OrderService


def _create_mock_user(user_id: int = 12345, first_name: str = "Иван", username: str = "ivan_barista") -> User:
    user = MagicMock(spec=User)
    user.id = user_id
    user.first_name = first_name
    user.last_name = "Иванов"
    user.full_name = f"{first_name} Иванов"
    user.username = username
    return user


def _create_mock_chat(chat_id: int = 12345) -> Chat:
    chat = MagicMock(spec=Chat)
    chat.id = chat_id
    return chat


def _create_mock_message(user_id: int = 12345, text: str = "/start") -> Message:
    msg = MagicMock(spec=Message)
    msg.message_id = 999
    msg.from_user = _create_mock_user(user_id=user_id)
    msg.chat = _create_mock_chat(chat_id=user_id)
    msg.text = text
    msg.answer = AsyncMock()
    msg.edit_text = AsyncMock()
    return msg


def _create_mock_callback(user_id: int = 12345, data: str = "") -> CallbackQuery:
    cb = MagicMock(spec=CallbackQuery)
    cb.id = "cb_123"
    cb.from_user = _create_mock_user(user_id=user_id)
    cb.data = data
    cb.message = _create_mock_message(user_id=user_id)
    cb.answer = AsyncMock()
    return cb


@pytest.mark.asyncio
async def test_keyboards_structure():
    """Verify inline keyboard generators create correct layouts and URLs."""
    # 1. Barista keyboard
    kb = get_barista_main_keyboard(bar_id=1)
    assert len(kb.inline_keyboard) == 2
    assert "🛒 Сделать заказ" in kb.inline_keyboard[0][0].text
    assert kb.inline_keyboard[0][0].web_app is not None
    assert "bar_id=1" in kb.inline_keyboard[0][0].web_app.url
    assert "🔄 Сменить кофейню" in kb.inline_keyboard[1][0].text

    # 2. Bar selection keyboard
    bar1 = Bar(id=1, name="Центр", is_active=True)
    bar2 = Bar(id=2, name="Север", is_active=True)
    bars_kb = get_bar_selection_keyboard([bar1, bar2])
    assert len(bars_kb.inline_keyboard) == 2
    assert "Центр" in bars_kb.inline_keyboard[0][0].text
    assert bars_kb.inline_keyboard[0][0].callback_data == "barista:select_bar:1"

    # 3. Warehouse keyboard
    wh_pending = get_order_warehouse_keyboard(100, OrderStatus.PENDING)
    assert wh_pending is not None
    assert len(wh_pending.inline_keyboard[0]) == 2
    assert "📦 В сборке" in wh_pending.inline_keyboard[0][0].text
    assert "🚚 Отгружен" in wh_pending.inline_keyboard[0][1].text

    wh_packing = get_order_warehouse_keyboard(100, OrderStatus.PACKING)
    assert wh_packing is not None
    assert len(wh_packing.inline_keyboard[0]) == 1
    assert "🚚 Отгружен" in wh_packing.inline_keyboard[0][0].text

    wh_shipped = get_order_warehouse_keyboard(100, OrderStatus.SHIPPED)
    assert wh_shipped is None


@pytest.mark.asyncio
async def test_format_order_message_all_sections():
    """Verify message formatting matches the exact specification."""
    items = [
        {"name": "Стакан 0,3", "confirmed_qty": 50.0, "unit": "шт."},
        {"name": "Сироп «Солёная карамель»", "confirmed_qty": 2.0, "unit": "бут."},
        {"name": "Молоко кокосовое", "confirmed_qty": 6.0, "unit": "шт."},
        {"name": "Салфетки простые", "confirmed_qty": 4.0, "unit": "уп."},
    ]
    out_of_stock = [
        {"name": "Сахар в стиках", "unit": "шт."},
    ]

    msg = format_order_message(
        order_id=1042,
        bar_name="Кофейня «Центр»",
        items=items,
        out_of_stock_items=out_of_stock,
        status=OrderStatus.PENDING,
    )

    assert "📦 Новый заказ #1042 — Кофейня «Центр»" in msg
    assert "• Стакан 0,3 — 50 шт." in msg
    assert "• Сироп «Солёная карамель» — 2 бут." in msg
    assert "• Молоко кокосовое — 6 шт." in msg
    assert "• Салфетки простые — 4 уп." in msg
    assert "⚠️ В стопе (не вошло):" in msg
    assert "• Сахар в стиках — 0 шт." in msg

    # Test packing status
    msg_pack = format_order_message(
        order_id=1042,
        bar_name="Центр",
        items=items,
        out_of_stock_items=out_of_stock,
        status=OrderStatus.PACKING,
        packer_name="Иван Иванов (@ivan)",
    )
    assert "👨‍🍳 В сборке: Иван Иванов (@ivan)" in msg_pack

    # Test shipped status
    msg_ship = format_order_message(
        order_id=1042,
        bar_name="Центр",
        items=items,
        status=OrderStatus.SHIPPED,
        shipped_by="Иван Иванов (@ivan)",
    )
    assert "✅ Заказ #1042 отгружен" in msg_ship
    assert "Кофейня: «Центр»" in msg_ship
    assert "Отгрузил: Иван Иванов (@ivan)" in msg_ship


@pytest.mark.asyncio
async def test_barista_start_unbound_and_bind_flow(db_session: AsyncSession):
    """Test /start when barista is not yet bound, followed by bar selection."""
    bar1 = Bar(name="Кофейня Арбат", is_active=True)
    bar2 = Bar(name="Кофейня Центр", is_active=True)
    db_session.add_all([bar1, bar2])
    await db_session.commit()
    await db_session.refresh(bar1)
    await db_session.refresh(bar2)

    # 1. Unbound user sends /start
    msg = _create_mock_message(user_id=111222, text="/start")
    await start_handler(message=msg, command=None, db=db_session)

    msg.answer.assert_called_once()
    answer_text = msg.answer.call_args[0][0]
    answer_kb = msg.answer.call_args[1]["reply_markup"]
    assert "выберите вашу кофейню" in answer_text
    assert len(answer_kb.inline_keyboard) == 2

    # 2. User clicks select bar callback
    cb = _create_mock_callback(user_id=111222, data=f"barista:select_bar:{bar1.id}")
    await select_bar_callback(callback=cb, db=db_session)

    cb.answer.assert_called_once()
    assert f"«{bar1.name}»" in cb.answer.call_args[0][0]
    cb.message.edit_text.assert_called_once()
    edit_text = cb.message.edit_text.call_args[0][0]
    assert f"«{bar1.name}»" in edit_text

    # Verify DB was updated
    await db_session.refresh(bar1)
    assert bar1.telegram_chat_id == 111222

    # 3. User sends /start again when already bound
    msg2 = _create_mock_message(user_id=111222, text="/start")
    await start_handler(message=msg2, command=None, db=db_session)
    msg2.answer.assert_called_once()
    answer_text2 = msg2.answer.call_args[0][0]
    assert f"«{bar1.name}»" in answer_text2
    assert "открыть накладную" in answer_text2


@pytest.mark.asyncio
async def test_barista_start_deep_link(db_session: AsyncSession):
    """Test /start with deep link parameter (e.g. /start bar_2)."""
    bar = Bar(name="Кофейня Тверская", is_active=True)
    db_session.add(bar)
    await db_session.commit()
    await db_session.refresh(bar)

    cmd = MagicMock(spec=CommandObject)
    cmd.args = f"bar_{bar.id}"

    msg = _create_mock_message(user_id=333444, text=f"/start bar_{bar.id}")
    await start_handler(message=msg, command=cmd, db=db_session)

    msg.answer.assert_called_once()
    answer_text = msg.answer.call_args[0][0]
    assert f"«{bar.name}»" in answer_text

    await db_session.refresh(bar)
    assert bar.telegram_chat_id == 333444


@pytest.mark.asyncio
async def test_barista_bind_command_and_change_bar(db_session: AsyncSession):
    """Test /bind command and change_bar callback."""
    bar = Bar(name="Кофейня Невский", is_active=True)
    db_session.add(bar)
    await db_session.commit()

    msg = _create_mock_message(user_id=555666, text="/bind")
    await bind_command_handler(message=msg, db=db_session)
    msg.answer.assert_called_once()
    assert "Выберите вашу кофейню" in msg.answer.call_args[0][0]

    cb = _create_mock_callback(user_id=555666, data="barista:change_bar")
    await change_bar_callback(callback=cb, db=db_session)
    cb.message.edit_text.assert_called_once()
    assert "новую кофейню" in cb.message.edit_text.call_args[0][0]


@pytest.mark.asyncio
async def test_warehouse_pack_and_ship_flow(db_session: AsyncSession):
    """Test warehouse order lifecycle: taking into packing and shipping order."""
    # 1. Setup Bar, Product, Stock, Order
    bar = Bar(name="Кофейня Центр", is_active=True)
    prod1 = Product(sku="CUP-03", name="Стакан 0,3", category="Расходники", unit="шт.", is_active=True)
    prod2 = Product(sku="SYR-CAR", name="Сироп Карамель", category="Сиропы", unit="бут.", is_active=True)
    db_session.add_all([bar, prod1, prod2])
    await db_session.commit()
    await db_session.refresh(bar)
    await db_session.refresh(prod1)
    await db_session.refresh(prod2)

    stock1 = Stock(product_id=prod1.id, real_qty=100.0, reserved_qty=0.0)
    stock2 = Stock(product_id=prod2.id, real_qty=10.0, reserved_qty=0.0)
    db_session.add_all([stock1, stock2])
    await db_session.commit()

    # Create order via OrderService
    req = OrderCreateRequest(
        bar_id=bar.id,
        items=[
            OrderItemInput(product_id=prod1.id, quantity=50.0),
            OrderItemInput(product_id=prod2.id, quantity=2.0),
        ],
    )
    res = await OrderService.create_order(db_session, req)
    order_id = res.id

    # Verify initial stock state
    await db_session.refresh(stock1)
    await db_session.refresh(stock2)
    assert stock1.real_qty == 100.0
    assert stock1.reserved_qty == 50.0
    assert stock2.real_qty == 10.0
    assert stock2.reserved_qty == 2.0

    # 2. Warehouse worker clicks [ 📦 В сборке ]
    pack_cb = _create_mock_callback(user_id=777888, data=f"warehouse:pack:{order_id}")
    await pack_order_callback(callback=pack_cb, db=db_session)

    pack_cb.answer.assert_called_once()
    assert "взят в сборку" in pack_cb.answer.call_args[0][0]
    pack_cb.message.edit_text.assert_called_once()
    edit_pack_text = pack_cb.message.edit_text.call_args[1]["text"]
    assert "👨‍🍳 В сборке: Иван Иванов (@ivan_barista)" in edit_pack_text
    pack_kb = pack_cb.message.edit_text.call_args[1]["reply_markup"]
    assert len(pack_kb.inline_keyboard[0]) == 1
    assert "🚚 Отгружен" in pack_kb.inline_keyboard[0][0].text

    # Verify Order status changed to PACKING
    order_res = await db_session.execute(select(Order).where(Order.id == order_id))
    order = order_res.scalar_one()
    assert order.status == OrderStatus.PACKING

    # 3. Warehouse worker clicks [ 🚚 Отгружен ]
    ship_cb = _create_mock_callback(user_id=777888, data=f"warehouse:ship:{order_id}")
    await ship_order_callback(callback=ship_cb, db=db_session)

    ship_cb.answer.assert_called_once()
    assert "успешно отгружен" in ship_cb.answer.call_args[0][0]
    ship_cb.message.edit_text.assert_called_once()
    edit_ship_text = ship_cb.message.edit_text.call_args[1]["text"]
    assert f"✅ Заказ #{order_id} отгружен" in edit_ship_text
    assert "Отгрузил: Иван Иванов (@ivan_barista)" in edit_ship_text
    assert ship_cb.message.edit_text.call_args[1]["reply_markup"] is None

    # Verify physical stock was deducted
    await db_session.refresh(stock1)
    await db_session.refresh(stock2)
    assert stock1.real_qty == 50.0  # 100 - 50
    assert stock1.reserved_qty == 0.0  # 50 - 50
    assert stock2.real_qty == 8.0  # 10 - 2
    assert stock2.reserved_qty == 0.0  # 2 - 2

    await db_session.refresh(order)
    assert order.status == OrderStatus.SHIPPED


@pytest.mark.asyncio
async def test_warehouse_ship_already_shipped_handling(db_session: AsyncSession):
    """Test clicking ship when already shipped shows alert."""
    bar = Bar(name="Кофейня", is_active=True)
    prod = Product(sku="COF", name="Кофе", category="Кофе", unit="кг", is_active=True)
    db_session.add_all([bar, prod])
    await db_session.commit()
    await db_session.refresh(bar)
    await db_session.refresh(prod)

    stock = Stock(product_id=prod.id, real_qty=10.0, reserved_qty=0.0)
    db_session.add(stock)
    await db_session.commit()

    req = OrderCreateRequest(bar_id=bar.id, items=[OrderItemInput(product_id=prod.id, quantity=1.0)])
    res = await OrderService.create_order(db_session, req)
    order_id = res.id

    # Ship first time
    await OrderService.ship_order(db_session, order_id)

    # Click ship button on already shipped order
    cb = _create_mock_callback(user_id=123, data=f"warehouse:ship:{order_id}")
    await ship_order_callback(callback=cb, db=db_session)
    cb.answer.assert_called_once()
    assert "Ошибка" in cb.answer.call_args[0][0]
    assert cb.answer.call_args[1]["show_alert"] is True


@pytest.mark.asyncio
async def test_stoplist_handler(db_session: AsyncSession):
    """Test /stoplist command with out-of-stock items and when stoplist is empty."""
    # 1. Initially empty stoplist
    p1 = Product(sku="P1", name="Кофе Зерно", category="Кофе", unit="кг", is_active=True)
    p2 = Product(sku="P2", name="Молоко Овсяное", category="Молоко", unit="л", is_active=True)
    db_session.add_all([p1, p2])
    await db_session.commit()
    await db_session.refresh(p1)
    await db_session.refresh(p2)

    s1 = Stock(product_id=p1.id, real_qty=10.0, reserved_qty=0.0)
    s2 = Stock(product_id=p2.id, real_qty=5.0, reserved_qty=0.0)
    db_session.add_all([s1, s2])
    await db_session.commit()

    msg = _create_mock_message(text="/stoplist")
    await stoplist_command_handler(message=msg, db=db_session)
    msg.answer.assert_called_once()
    assert "✅ Стоп-лист пуст!" in msg.answer.call_args[0][0]

    # 2. Add out-of-stock items (available_qty <= 0)
    p3 = Product(sku="P3", name="Сироп Карамель", category="Сиропы", unit="бут.", is_active=True)
    p4 = Product(sku="P4", name="Сироп Ваниль", category="Сиропы", unit="бут.", is_active=True)
    db_session.add_all([p3, p4])
    await db_session.commit()
    await db_session.refresh(p3)
    await db_session.refresh(p4)

    s3 = Stock(product_id=p3.id, real_qty=0.0, reserved_qty=0.0)
    s4 = Stock(product_id=p4.id, real_qty=2.0, reserved_qty=2.0)  # available = 0
    db_session.add_all([s3, s4])
    await db_session.commit()

    msg2 = _create_mock_message(text="/stoplist")
    await stoplist_command_handler(message=msg2, db=db_session)
    msg2.answer.assert_called_once()
    ans = msg2.answer.call_args[0][0]
    assert "🚫 **Стоп-лист товаров на складе (нет в наличии):**" in ans
    assert "📁 **Сиропы**" in ans
    assert "• Сироп Карамель — 0 бут." in ans
    assert "• Сироп Ваниль — 0 бут." in ans
    assert "Всего позиций в стопе: **2**" in ans


@pytest.mark.asyncio
async def test_send_order_to_warehouse_mock_bot():
    """Test send_order_to_warehouse with mock Bot instance."""
    bot = MagicMock()
    bot.send_message = AsyncMock()

    with patch("app.bot.services.notifier.bot_settings") as mock_settings:
        mock_settings.TOKEN = "test_token"
        mock_settings.WAREHOUSE_CHAT_ID = -100999

        await send_order_to_warehouse(
            order_id=555,
            bar_name="Кофейня Центр",
            items=[{"name": "Стакан 0,3", "confirmed_qty": 50, "unit": "шт."}],
            out_of_stock_items=[{"name": "Сахар в стиках", "unit": "шт."}],
            bot=bot,
            chat_id=-100999,
        )

        bot.send_message.assert_called_once()
        call_kwargs = bot.send_message.call_args[1]
        assert call_kwargs["chat_id"] == -100999
        assert "📦 Новый заказ #555 — Кофейня «Центр»" in call_kwargs["text"]
        assert "• Стакан 0,3 — 50 шт." in call_kwargs["text"]
        assert "⚠️ В стопе (не вошло):" in call_kwargs["text"]
        assert "• Сахар в стиках — 0 шт." in call_kwargs["text"]


@pytest.mark.asyncio
async def test_create_dispatcher_setup():
    """Verify create_dispatcher initializes routers and middleware."""
    from app.bot.bot import create_dispatcher
    dp = create_dispatcher()
    assert dp is not None
    assert len(dp.sub_routers) == 4


@pytest.mark.asyncio
async def test_api_order_triggers_warehouse_notification(client, db_session: AsyncSession):
    """End-to-end test verifying API order creation calls notification dispatcher."""
    bar = Bar(name="Кофейня Пресня", is_active=True)
    prod = Product(sku="PR-1", name="Кофе Арабика", category="Зерно", unit="кг", is_active=True)
    db_session.add_all([bar, prod])
    await db_session.commit()
    await db_session.refresh(bar)
    await db_session.refresh(prod)

    stock = Stock(product_id=prod.id, real_qty=20.0, reserved_qty=0.0)
    db_session.add(stock)
    await db_session.commit()

    with patch("app.services.order_service.send_order_to_warehouse", new_callable=AsyncMock) as mock_send:
        resp = await client.post(
            "/api/orders",
            json={
                "bar_id": bar.id,
                "items": [{"product_id": prod.id, "quantity": 5.0}],
            },
        )
        assert resp.status_code == 201
        mock_send.assert_called_once()
        assert mock_send.call_args[1]["order_id"] == resp.json()["id"]
        assert mock_send.call_args[1]["bar_name"] == "Кофейня Пресня"
