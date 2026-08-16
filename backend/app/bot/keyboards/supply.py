from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_supply_confirmation_keyboard(invoice_id: int) -> InlineKeyboardMarkup:
    """Generate inline keyboard for reviewing recognized supply invoice."""
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Зачислить на склад",
                callback_data=f"confirm_supply:{invoice_id}",
            ),
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"cancel_supply:{invoice_id}",
            ),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
