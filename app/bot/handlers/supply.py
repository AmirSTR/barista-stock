import io
import logging
from typing import List, Optional
from aiogram import Bot, F, Router
from aiogram.enums import ChatAction
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.filters.admin import IsAdminFilter
from app.bot.keyboards.supply import get_supply_confirmation_keyboard
from app.core.database import async_session_maker
from app.schemas.ocr import MatchedSupplyItem
from app.services.matching_service import MatchingService
from app.services.ocr_service import OCRService
from app.services.supply_service import SupplyService

logger = logging.getLogger(__name__)

supply_router = Router(name="supply")


async def _resolve_db(db: Optional[AsyncSession] = None):
    """Context manager or session resolver for DB sessions in handlers."""
    if db is not None:
        yield db
    else:
        async with async_session_maker() as session:
            yield session


def format_supply_review_message(
    invoice_number: Optional[str],
    invoice_id: int,
    matched_items: List[MatchedSupplyItem],
) -> str:
    """Format OCR extraction results with confidence icons for admin verification."""
    num_str = invoice_number if invoice_number and invoice_number.strip() else str(invoice_id)
    lines = [
        f"📋 Распознана накладная №{num_str}:",
        "──────────────────────────────",
    ]

    for idx, item in enumerate(matched_items, start=1):
        pct = int(round(item.confidence_score * 100))
        qty_str = f"{int(item.quantity)}" if item.quantity.is_integer() else f"{item.quantity}"
        unit_str = f"{item.unit}." if not item.unit.endswith(".") else item.unit

        if not item.is_uncertain and item.product_name:
            lines.append(f"{idx}. ✅ {item.product_name} — {qty_str} {unit_str} ({pct}%)")
        else:
            cand = item.product_name or "товар не найден"
            lines.append(f"{idx}. ❓ {item.raw_name} — {qty_str} {unit_str} ({pct}% совпадение с \"{cand}\")")

    lines.append("──────────────────────────────")
    lines.append("Нажмите подтвердить для зачисления на баланс склада.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 1. Admin Invoice Photo Processing
# ---------------------------------------------------------------------------


@supply_router.message(F.photo, IsAdminFilter())
async def process_invoice_photo_admin(
    message: Message,
    bot: Bot,
    db: Optional[AsyncSession] = None,
):
    """Handle invoice photo upload by administrator/warehouse manager:

    1. Downloads the highest resolution photo into memory buffer.
    2. Sends typing / processing chat action.
    3. Runs OCR extraction and RapidFuzz catalog matching.
    4. Saves draft in DB.
    5. Sends review message with confirmation inline keyboard.
    """
    # 1. Notify user that processing is starting
    status_msg = await message.answer("⏳ Распознаю накладную и сверяю со складом...")
    try:
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    except Exception:
        pass

    try:
        # 2. Download photo to memory buffer
        photo = message.photo[-1]
        photo_buffer = io.BytesIO()
        await bot.download(photo, destination=photo_buffer)
        image_bytes = photo_buffer.getvalue()

        # 3. Call OCR service
        ocr_result = await OCRService.parse_invoice_photo(image_bytes)

        if not ocr_result.items:
            await status_msg.edit_text(
                "⚠️ На фотографии не удалось распознать товарные позиции. "
                "Пожалуйста, сделайте более чёткое фото накладной при хорошем освещении."
            )
            return

        # 4. Reconcile with catalog products using RapidFuzz
        async for session in _resolve_db(db):
            matched_items = await MatchingService.match_invoice_items(
                session=session,
                ocr_items=ocr_result.items,
            )

            # 5. Save draft in database
            draft = await SupplyService.create_supply_draft(
                session=session,
                photo_file_id=photo.file_id,
                invoice_number=ocr_result.invoice_number,
                matched_items=matched_items,
            )

            # 6. Format and send review message
            invoice_num = draft.invoice_number or str(draft.id)
            review_text = format_supply_review_message(
                invoice_number=invoice_num,
                invoice_id=draft.id,
                matched_items=matched_items,
            )
            keyboard = get_supply_confirmation_keyboard(invoice_id=draft.id)

            await status_msg.edit_text(
                text=review_text,
                reply_markup=keyboard,
            )

    except Exception as e:
        logger.exception(f"Error processing invoice photo: {e}")
        await status_msg.edit_text(f"❌ Ошибка при распознавании накладной: {str(e)}")


# ---------------------------------------------------------------------------
# 2. Non-admin Photo Attempt
# ---------------------------------------------------------------------------


@supply_router.message(F.photo)
async def process_photo_non_admin(message: Message):
    """Polite access rejection for non-admin users sending photos."""
    await message.answer("⛔ У вас нет доступа к приёмке накладных и управлению складом")


# ---------------------------------------------------------------------------
# 3. Admin Supply Confirmation & Cancellation Callbacks
# ---------------------------------------------------------------------------


@supply_router.callback_query(F.data.startswith("confirm_supply:"), IsAdminFilter())
async def confirm_supply_callback(
    callback: CallbackQuery,
    db: Optional[AsyncSession] = None,
):
    """Process supply confirmation by admin:

    - Atomically increments stock balances in DB
    - Marks invoice as confirmed
    - Edits message with success notification
    """
    try:
        invoice_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer("Неверный ID накладной", show_alert=True)
        return

    async for session in _resolve_db(db):
        try:
            confirmed_invoice = await SupplyService.confirm_supply_invoice(
                session=session,
                invoice_id=invoice_id,
            )
            doc_num = confirmed_invoice.invoice_number or str(confirmed_invoice.id)

            await callback.answer("✅ Поставка успешно оприходована!")
            if callback.message:
                await callback.message.edit_text(
                    text=f"✅ Поставка №{doc_num} успешно оприходована! Остатки обновлены, позиции вышли из стоп-листа.",
                    reply_markup=None,
                )
        except Exception as e:
            logger.error(f"Error confirming supply {invoice_id}: {e}")
            await callback.answer(f"Ошибка: {str(e)}", show_alert=True)


@supply_router.callback_query(F.data.startswith("cancel_supply:"), IsAdminFilter())
async def cancel_supply_callback(
    callback: CallbackQuery,
    db: Optional[AsyncSession] = None,
):
    """Process supply rejection/cancellation by admin:

    - Deletes draft supply invoice from DB
    - Edits message with cancellation notification
    """
    try:
        invoice_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer("Неверный ID накладной", show_alert=True)
        return

    async for session in _resolve_db(db):
        try:
            cancelled = await SupplyService.cancel_supply_draft(
                session=session,
                invoice_id=invoice_id,
            )
            doc_num = (cancelled.invoice_number if cancelled else None) or str(invoice_id)

            await callback.answer("Приёмка накладной отклонена")
            if callback.message:
                await callback.message.edit_text(
                    text=f"❌ Приёмка накладной №{doc_num} отклонена.",
                    reply_markup=None,
                )
        except Exception as e:
            logger.error(f"Error cancelling supply {invoice_id}: {e}")
            await callback.answer(f"Ошибка: {str(e)}", show_alert=True)


# ---------------------------------------------------------------------------
# 4. Non-admin Supply Callbacks
# ---------------------------------------------------------------------------


@supply_router.callback_query(F.data.startswith("confirm_supply:") | F.data.startswith("cancel_supply:"))
async def supply_callback_non_admin(callback: CallbackQuery):
    """Deny non-admin access to supply confirmation/cancellation buttons."""
    await callback.answer(
        "⛔ У вас нет доступа к приёмке накладных и управлению складом",
        show_alert=True,
    )
