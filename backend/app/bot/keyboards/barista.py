from typing import List, Optional
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from app.bot.config import bot_settings
from app.models.bar import Bar


def get_barista_main_keyboard(bar_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Create main barista inline keyboard with WebApp launch button and switch bar option."""
    base_url = bot_settings.WEBAPP_URL
    if bar_id is not None:
        separator = "&" if "?" in base_url else "?"
        webapp_url = f"{base_url}{separator}bar_id={bar_id}"
    else:
        webapp_url = base_url

    buttons = [
        [
            InlineKeyboardButton(
                text="🛒 Сделать заказ",
                web_app=WebAppInfo(url=webapp_url),
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Сменить кофейню",
                callback_data="barista:change_bar",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_bar_selection_keyboard(bars: List[Bar]) -> InlineKeyboardMarkup:
    """Create inline keyboard with active coffee bars for initial or updated binding."""
    keyboard: List[List[InlineKeyboardButton]] = []
    for bar in bars:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"☕️ {bar.name}",
                    callback_data=f"barista:select_bar:{bar.id}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
