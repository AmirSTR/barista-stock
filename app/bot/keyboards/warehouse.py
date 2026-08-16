from typing import Optional
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.models.order import OrderStatus


def get_order_warehouse_keyboard(
    order_id: int,
    status: OrderStatus = OrderStatus.PENDING,
) -> Optional[InlineKeyboardMarkup]:
    """Generate interactive inline keyboard for warehouse order status transitions.

    - PENDING: [ 📦 В сборке ] and [ 🚚 Отгружен ]
    - PACKING: [ 🚚 Отгружен ]
    - SHIPPED / CANCELLED: None (buttons removed)
    """
    if status == OrderStatus.PENDING:
        buttons = [
            [
                InlineKeyboardButton(
                    text="📦 В сборке",
                    callback_data=f"warehouse:pack:{order_id}",
                ),
                InlineKeyboardButton(
                    text="🚚 Отгружен",
                    callback_data=f"warehouse:ship:{order_id}",
                ),
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    elif status == OrderStatus.PACKING:
        buttons = [
            [
                InlineKeyboardButton(
                    text="🚚 Отгружен",
                    callback_data=f"warehouse:ship:{order_id}",
                ),
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    return None
