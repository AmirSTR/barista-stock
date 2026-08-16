import io
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import CallbackQuery, Chat, Message, PhotoSize, User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.filters.admin import IsAdminFilter
from app.bot.handlers.supply import (
    cancel_supply_callback,
    confirm_supply_callback,
    format_supply_review_message,
    process_invoice_photo_admin,
    process_photo_non_admin,
    supply_callback_non_admin,
)
from app.bot.keyboards.supply import get_supply_confirmation_keyboard
from app.core.config import settings
from app.models.product import Product
from app.models.stock import Stock
from app.models.supply import SupplyInvoice, SupplyItem, SupplyStatus
from app.schemas.ocr import InvoiceItemOCR, InvoiceOCRResponse, MatchedSupplyItem
from app.services.matching_service import MatchingService
from app.services.ocr_service import OCRConfigurationError, OCRService, parse_invoice_photo
from app.services.supply_service import SupplyService


# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------

def _create_mock_user(user_id: int = 12345, first_name: str = "Admin") -> User:
    user = MagicMock(spec=User)
    user.id = user_id
    user.first_name = first_name
    user.last_name = "User"
    user.full_name = f"{first_name} User"
    user.username = "admin_user"
    return user


def _create_mock_photo_message(user_id: int = 12345, file_id: str = "photo_abc123") -> Message:
    msg = MagicMock(spec=Message)
    msg.message_id = 1001
    msg.from_user = _create_mock_user(user_id=user_id)
    msg.chat = MagicMock(spec=Chat)
    msg.chat.id = user_id
    
    photo_size = MagicMock(spec=PhotoSize)
    photo_size.file_id = file_id
    msg.photo = [photo_size]

    msg.answer = AsyncMock()
    msg.edit_text = AsyncMock()
    return msg


def _create_mock_callback(user_id: int = 12345, data: str = "") -> CallbackQuery:
    cb = MagicMock(spec=CallbackQuery)
    cb.id = "cb_test"
    cb.from_user = _create_mock_user(user_id=user_id)
    cb.data = data
    cb.message = MagicMock(spec=Message)
    cb.message.edit_text = AsyncMock()
    cb.answer = AsyncMock()
    return cb


# ---------------------------------------------------------------------------
# 1. IsAdminFilter Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_is_admin_filter():
    """Verify IsAdminFilter correctly identifies admin and non-admin users."""
    admin_filter = IsAdminFilter()

    with patch.object(settings, "ADMIN_TELEGRAM_IDS", [111, 222, 333]):
        # 1. Admin user message
        msg_admin = _create_mock_photo_message(user_id=222)
        assert await admin_filter(msg_admin) is True

        # 2. Non-admin user message
        msg_non_admin = _create_mock_photo_message(user_id=999)
        assert await admin_filter(msg_non_admin) is False

        # 3. Callback from admin
        cb_admin = _create_mock_callback(user_id=111, data="confirm_supply:1")
        assert await admin_filter(cb_admin) is True

        # 4. Callback from non-admin
        cb_non_admin = _create_mock_callback(user_id=555, data="confirm_supply:1")
        assert await admin_filter(cb_non_admin) is False

        # 5. Object without user
        empty_obj = MagicMock()
        empty_obj.from_user = None
        assert await admin_filter(empty_obj) is False


def test_admin_telegram_ids_parsing():
    """Test various formats of ADMIN_TELEGRAM_IDS in config."""
    from app.core.config import Settings
    
    # Comma-separated string
    s1 = Settings(ADMIN_TELEGRAM_IDS="12345, 67890, 99999")
    assert s1.ADMIN_TELEGRAM_IDS == [12345, 67890, 99999]

    # JSON list string
    s2 = Settings(ADMIN_TELEGRAM_IDS="[111, 222]")
    assert s2.ADMIN_TELEGRAM_IDS == [111, 222]

    # Int
    s3 = Settings(ADMIN_TELEGRAM_IDS=555)
    assert s3.ADMIN_TELEGRAM_IDS == [555]

    # Empty
    s4 = Settings(ADMIN_TELEGRAM_IDS="")
    assert s4.ADMIN_TELEGRAM_IDS == []


def test_railway_environment_value_parsing(monkeypatch):
    """Railway-style strings must be parsed before Pydantic's JSON decoder."""
    from app.core.config import Settings

    monkeypatch.setenv("ADMIN_TELEGRAM_IDS", "12345, 67890")
    monkeypatch.setenv("TELEGRAM_WAREHOUSE_CHAT_ID", "")
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://frontend.example.com,http://localhost:5173/",
    )

    parsed = Settings(_env_file=None)

    assert parsed.ADMIN_TELEGRAM_IDS == [12345, 67890]
    assert parsed.TELEGRAM_WAREHOUSE_CHAT_ID is None
    assert parsed.CORS_ORIGINS == [
        "https://frontend.example.com",
        "http://localhost:5173",
    ]


# ---------------------------------------------------------------------------
# 2. OCRService & Schema Validation Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ocr_service_clean_json_and_validation():
    """Test OCR response cleaning, JSON markdown fence extraction, and Pydantic validation."""
    raw_markdown_json = """
    ```json
    {
      "invoice_number": "4892",
      "items": [
        {"raw_name": "Сироп «Солёная карамель»", "quantity": 12.0, "unit": "бут"},
        {"raw_name": "Молоко кокосовое", "quantity": 24.0, "unit": "шт"},
        {"raw_name": "Порошок «Манго»", "quantity": 5.0, "unit": "уп"}
      ]
    }
    ```
    """
    cleaned = OCRService._clean_json_response(raw_markdown_json)
    assert cleaned.startswith("{") and cleaned.endswith("}")

    parsed = InvoiceOCRResponse.model_validate_json(cleaned)
    assert parsed.invoice_number == "4892"
    assert len(parsed.items) == 3
    assert parsed.items[0].raw_name == "Сироп «Солёная карамель»"
    assert parsed.items[0].quantity == 12.0
    assert parsed.items[0].unit == "бут"


@pytest.mark.asyncio
async def test_ocr_service_demo_mode_is_explicit():
    """Demo invoice data is returned only when the opt-in flag is enabled."""
    with (
        patch.object(settings, "GEMINI_API_KEY", None),
        patch.object(settings, "OPENAI_API_KEY", None),
        patch.object(settings, "OCR_DEMO_MODE", True),
    ):
        res = await OCRService.parse_invoice_photo(b"dummy_bytes")
        assert res.invoice_number is not None
        assert len(res.items) >= 2

        # Test convenience function
        res_dict = await parse_invoice_photo(b"dummy_bytes")
        assert isinstance(res_dict, dict)
        assert "items" in res_dict


@pytest.mark.asyncio
async def test_ocr_service_rejects_missing_production_key():
    with (
        patch.object(settings, "GEMINI_API_KEY", None),
        patch.object(settings, "OPENAI_API_KEY", None),
        patch.object(settings, "OCR_PROVIDER", "gemini"),
        patch.object(settings, "OCR_DEMO_MODE", False),
    ):
        with pytest.raises(OCRConfigurationError, match="GEMINI_API_KEY"):
            await OCRService.parse_invoice_photo(b"dummy_bytes")


# ---------------------------------------------------------------------------
# 3. MatchingService Tests (Fuzzy RapidFuzz Reconcile)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_matching_service_logic():
    """Test fuzzy matching with >=85% auto-matching and <85% uncertain flagging."""
    prod1 = Product(id=1, sku="SKU-0001", name="Сироп «Солёная карамель»", category="Сиропы", unit="бут.", is_active=True)
    prod2 = Product(id=2, sku="SKU-0002", name="Молоко кокосовое", category="Молоко", unit="шт.", is_active=True)
    prod3 = Product(id=3, sku="SKU-0003", name="Порошок манго-личи", category="Сухие смеси", unit="уп.", is_active=True)
    products = [prod1, prod2, prod3]

    ocr_items = [
        InvoiceItemOCR(raw_name="Сироп Солёная карамель", quantity=12.0, unit="бут"),
        InvoiceItemOCR(raw_name="Молоко кокос", quantity=24.0, unit="шт"),
        InvoiceItemOCR(raw_name="Порошок Манго", quantity=5.0, unit="уп"),
    ]

    results = MatchingService.match_items(products=products, ocr_items=ocr_items, threshold=85.0)
    assert len(results) == 3

    # Item 1: High match
    item1 = results[0]
    assert item1.product_id == prod1.id
    assert item1.product_name == prod1.name
    assert item1.confidence_score >= 0.85
    assert item1.is_uncertain is False

    # Item 2: High match
    item2 = results[1]
    assert item2.product_id == prod2.id
    assert item2.product_name == prod2.name
    assert item2.confidence_score >= 0.85
    assert item2.is_uncertain is False

    # Item 3: Low match ("Порошок Манго" vs "Порошок манго-личи" -> < 85%)
    item3 = results[2]
    assert item3.product_id == prod3.id
    assert item3.product_name == prod3.name
    assert item3.confidence_score < 0.85
    assert item3.is_uncertain is True


@pytest.mark.asyncio
async def test_matching_service_db_query(db_session: AsyncSession):
    """Test MatchingService against database catalog."""
    p1 = Product(sku="S1", name="Сироп Ваниль", category="Сиропы", unit="бут.", is_active=True)
    p2 = Product(sku="S2", name="Сироп Лесной Орех", category="Сиропы", unit="бут.", is_active=True)
    db_session.add_all([p1, p2])
    await db_session.commit()

    ocr_items = [
        InvoiceItemOCR(raw_name="Сироп «Ваниль» 1л", quantity=6.0, unit="бут"),
    ]

    matched = await MatchingService.match_invoice_items(session=db_session, ocr_items=ocr_items)
    assert len(matched) == 1
    assert matched[0].product_id == p1.id
    assert matched[0].is_uncertain is False


# ---------------------------------------------------------------------------
# 4. Message Formatting Test
# ---------------------------------------------------------------------------

def test_format_supply_review_message():
    """Verify formatted supply review message contains required icons, percentages and candidate hints."""
    matched = [
        MatchedSupplyItem(
            raw_name="Сироп «Солёная карамель»",
            quantity=12.0,
            unit="бут",
            product_id=1,
            product_name="Сироп «Солёная карамель»",
            confidence_score=1.0,
            is_uncertain=False,
        ),
        MatchedSupplyItem(
            raw_name="Молоко кокосовое",
            quantity=24.0,
            unit="шт",
            product_id=2,
            product_name="Молоко кокосовое",
            confidence_score=0.94,
            is_uncertain=False,
        ),
        MatchedSupplyItem(
            raw_name="Порошок «Манго»",
            quantity=5.0,
            unit="уп",
            product_id=3,
            product_name="Порошок манго-личи",
            confidence_score=0.68,
            is_uncertain=True,
        ),
    ]

    msg = format_supply_review_message(
        invoice_number="4892",
        invoice_id=1,
        matched_items=matched,
    )

    assert "📋 Распознана накладная №4892:" in msg
    assert "1. ✅ Сироп «Солёная карамель» — 12 бут. (100%)" in msg
    assert "2. ✅ Молоко кокосовое — 24 шт. (94%)" in msg
    assert "3. ❓ Порошок «Манго» — 5 уп. (68% совпадение с \"Порошок манго-личи\")" in msg
    assert "Нажмите подтвердить для зачисления на баланс склада." in msg


# ---------------------------------------------------------------------------
# 5. SupplyService Lifecycle & Balance Crediting Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_supply_service_draft_and_confirmation(db_session: AsyncSession):
    """Test full lifecycle: creating supply draft, confirming, and updating stocks."""
    prod1 = Product(sku="P1", name="Кофе Арабика", category="Зерно", unit="кг", is_active=True)
    prod2 = Product(sku="P2", name="Чай Зеленый", category="Чай", unit="уп", is_active=True)
    db_session.add_all([prod1, prod2])
    await db_session.commit()
    await db_session.refresh(prod1)
    await db_session.refresh(prod2)

    # Initial stocks
    stock1 = Stock(product_id=prod1.id, real_qty=10.0, reserved_qty=0.0)
    stock2 = Stock(product_id=prod2.id, real_qty=5.0, reserved_qty=0.0)
    db_session.add_all([stock1, stock2])
    await db_session.commit()

    matched_items = [
        MatchedSupplyItem(
            raw_name="Кофе Арабика",
            quantity=15.0,
            unit="кг",
            product_id=prod1.id,
            product_name=prod1.name,
            confidence_score=1.0,
            is_uncertain=False,
        ),
        MatchedSupplyItem(
            raw_name="Чай Зеленый",
            quantity=10.0,
            unit="уп",
            product_id=prod2.id,
            product_name=prod2.name,
            confidence_score=1.0,
            is_uncertain=False,
        ),
    ]

    # 1. Create draft
    draft = await SupplyService.create_supply_draft(
        session=db_session,
        photo_file_id="photo_xyz",
        invoice_number="INV-1001",
        matched_items=matched_items,
    )
    assert draft.id is not None
    assert draft.status == SupplyStatus.DRAFT
    assert len(draft.items) == 2

    # Stock should NOT change yet
    await db_session.refresh(stock1)
    await db_session.refresh(stock2)
    assert stock1.real_qty == 10.0
    assert stock2.real_qty == 5.0

    # 2. Confirm invoice
    confirmed = await SupplyService.confirm_supply_invoice(session=db_session, invoice_id=draft.id)
    assert confirmed.status == SupplyStatus.CONFIRMED

    # Verify physical stocks were incremented
    await db_session.refresh(stock1)
    await db_session.refresh(stock2)
    assert stock1.real_qty == 25.0  # 10.0 + 15.0
    assert stock2.real_qty == 15.0  # 5.0 + 10.0

    # 3. Confirming again should raise error
    with pytest.raises(Exception):
        await SupplyService.confirm_supply_invoice(session=db_session, invoice_id=draft.id)


@pytest.mark.asyncio
async def test_supply_service_cancel_draft(db_session: AsyncSession):
    """Test cancelling a draft invoice."""
    matched_items = [
        MatchedSupplyItem(
            raw_name="Кофе",
            quantity=5.0,
            unit="кг",
            product_id=None,
            product_name=None,
            confidence_score=0.0,
            is_uncertain=True,
        )
    ]
    draft = await SupplyService.create_supply_draft(
        session=db_session,
        photo_file_id="photo_cancel",
        invoice_number="INV-CANCEL",
        matched_items=matched_items,
    )
    invoice_id = draft.id

    cancelled = await SupplyService.cancel_supply_draft(session=db_session, invoice_id=invoice_id)
    assert cancelled is not None

    # Check DB
    res = await db_session.execute(select(SupplyInvoice).where(SupplyInvoice.id == invoice_id))
    assert res.scalar_one_or_none() is None


# ---------------------------------------------------------------------------
# 6. Aiogram Bot Handlers & Permissions Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_process_invoice_photo_admin_handler(db_session: AsyncSession):
    """Test admin photo reception handler creates draft and sends formatted review message."""
    # Setup product catalog
    p1 = Product(sku="SYR-01", name="Сироп «Солёная карамель»", category="Сиропы", unit="бут.", is_active=True)
    p2 = Product(sku="MLK-01", name="Молоко кокосовое", category="Молоко", unit="шт.", is_active=True)
    db_session.add_all([p1, p2])
    await db_session.commit()

    # Mock Bot and Message
    bot = MagicMock()
    bot.download = AsyncMock()
    bot.send_chat_action = AsyncMock()

    msg = _create_mock_photo_message(user_id=12345)
    status_msg = MagicMock(spec=Message)
    status_msg.edit_text = AsyncMock()
    msg.answer.return_value = status_msg

    # Mock OCR response
    ocr_resp = InvoiceOCRResponse(
        invoice_number="4892",
        items=[
            InvoiceItemOCR(raw_name="Сироп «Солёная карамель»", quantity=12.0, unit="бут"),
            InvoiceItemOCR(raw_name="Молоко кокосовое", quantity=24.0, unit="шт"),
        ],
    )

    with patch.object(OCRService, "parse_invoice_photo", new_callable=AsyncMock) as mock_ocr:
        mock_ocr.return_value = ocr_resp

        await process_invoice_photo_admin(message=msg, bot=bot, db=db_session)

        # Verify bot actions
        msg.answer.assert_called_once_with("⏳ Распознаю накладную и сверяю со складом...")
        bot.download.assert_called_once()
        status_msg.edit_text.assert_called_once()

        edit_text = status_msg.edit_text.call_args[1]["text"]
        edit_kb = status_msg.edit_text.call_args[1]["reply_markup"]

        assert "📋 Распознана накладная №4892:" in edit_text
        assert "Сироп «Солёная карамель» — 12 бут. (100%)" in edit_text
        assert "Молоко кокосовое — 24 шт. (100%)" in edit_text
        assert len(edit_kb.inline_keyboard[0]) == 2
        assert "confirm_supply:" in edit_kb.inline_keyboard[0][0].callback_data
        assert "cancel_supply:" in edit_kb.inline_keyboard[0][1].callback_data

        # Verify draft was created in DB
        inv_res = await db_session.execute(select(SupplyInvoice).where(SupplyInvoice.invoice_number == "4892"))
        invoice = inv_res.scalar_one()
        assert invoice.status == SupplyStatus.DRAFT
        assert len(invoice.items) == 2


@pytest.mark.asyncio
async def test_process_photo_non_admin_handler():
    """Test non-admin user sending photo receives polite access rejection."""
    msg = _create_mock_photo_message(user_id=99999)
    await process_photo_non_admin(message=msg)

    msg.answer.assert_called_once()
    assert "⛔ У вас нет доступа к приёмке накладных и управлению складом" in msg.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_confirm_supply_callback_handler(db_session: AsyncSession):
    """Test admin clicking [ ✅ Зачислить на склад ] credits stock and updates message."""
    p1 = Product(sku="SYR-01", name="Сироп Карамель", category="Сиропы", unit="бут.", is_active=True)
    db_session.add(p1)
    await db_session.commit()
    await db_session.refresh(p1)

    s1 = Stock(product_id=p1.id, real_qty=5.0, reserved_qty=0.0)
    db_session.add(s1)
    await db_session.commit()

    draft = await SupplyService.create_supply_draft(
        session=db_session,
        photo_file_id="p123",
        invoice_number="4892",
        matched_items=[
            MatchedSupplyItem(
                raw_name="Сироп Карамель",
                quantity=10.0,
                unit="бут",
                product_id=p1.id,
                product_name=p1.name,
                confidence_score=1.0,
                is_uncertain=False,
            )
        ],
    )

    cb = _create_mock_callback(user_id=12345, data=f"confirm_supply:{draft.id}")
    await confirm_supply_callback(callback=cb, db=db_session)

    cb.answer.assert_called_once()
    cb.message.edit_text.assert_called_once()
    edit_text = cb.message.edit_text.call_args[1]["text"]
    assert "✅ Поставка №4892 успешно оприходована! Остатки обновлены, позиции вышли из стоп-листа." in edit_text

    # Verify stock balance was increased
    await db_session.refresh(s1)
    assert s1.real_qty == 15.0  # 5.0 + 10.0


@pytest.mark.asyncio
async def test_cancel_supply_callback_handler(db_session: AsyncSession):
    """Test admin clicking [ ❌ Отклонить ] cancels draft invoice."""
    draft = await SupplyService.create_supply_draft(
        session=db_session,
        photo_file_id="p456",
        invoice_number="4892",
        matched_items=[],
    )

    cb = _create_mock_callback(user_id=12345, data=f"cancel_supply:{draft.id}")
    await cancel_supply_callback(callback=cb, db=db_session)

    cb.answer.assert_called_once()
    cb.message.edit_text.assert_called_once()
    edit_text = cb.message.edit_text.call_args[1]["text"]
    assert "❌ Приёмка накладной №4892 отклонена." in edit_text


@pytest.mark.asyncio
async def test_supply_callbacks_non_admin_alert():
    """Test non-admin clicking confirm/cancel button gets alert popup."""
    cb = _create_mock_callback(user_id=99999, data="confirm_supply:10")
    await supply_callback_non_admin(callback=cb)

    cb.answer.assert_called_once()
    assert "⛔ У вас нет доступа к приёмке накладных и управлению складом" in cb.answer.call_args[0][0]
    assert cb.answer.call_args[1]["show_alert"] is True
