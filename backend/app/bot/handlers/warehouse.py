from typing import Optional
from aiogram import F, Router
from aiogram.types import CallbackQuery
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.bot.keyboards.warehouse import get_order_warehouse_keyboard
from app.bot.services.notifier import format_order_message
from app.core.database import async_session_maker
from app.models.order import Order, OrderItem, OrderStatus

warehouse_router = Router(name="warehouse")


async def _resolve_db(db: Optional[AsyncSession] = None):
    """Context manager or session resolver for DB sessions in handlers."""
    if db is not None:
        yield db
    else:
        async with async_session_maker() as session:
            yield session


@warehouse_router.callback_query(F.data.startswith("warehouse:pack:"))
async def pack_order_callback(
    callback: CallbackQuery,
    db: Optional[AsyncSession] = None,
):
    """Handler for [ 📦 В сборке ] inline button:

    - Transitions status to `OrderStatus.PACKING`
    - Notes who took the order into packing
    - Updates message and keeps [ 🚚 Отгружен ] button
    """
    try:
        order_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("Неверный ID заказа", show_alert=True)
        return

    async for session in _resolve_db(db):
        query = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.bar),
            )
            .where(Order.id == order_id)
        )
        res = await session.execute(query)
        order = res.scalar_one_or_none()

        if not order:
            await callback.answer(f"Заказ #{order_id} не найден", show_alert=True)
            return

        if order.status == OrderStatus.PACKING:
            await callback.answer(f"Заказ #{order_id} уже находится в сборке!", show_alert=True)
            return
        elif order.status == OrderStatus.SHIPPED:
            await callback.answer(f"Заказ #{order_id} уже отгружен!", show_alert=True)
            return
        elif order.status == OrderStatus.CANCELLED:
            await callback.answer(f"Заказ #{order_id} отменен!", show_alert=True)
            return

        order.status = OrderStatus.PACKING
        await session.commit()
        await session.refresh(order)

        user = callback.from_user
        packer_name = user.full_name
        if user.username:
            packer_name += f" (@{user.username})"

        bar_name = order.bar.name if order.bar else "Кофейня"
        new_text = format_order_message(
            order_id=order.id,
            bar_name=bar_name,
            items=order.items,
            status=OrderStatus.PACKING,
            packer_name=packer_name,
        )
        new_keyboard = get_order_warehouse_keyboard(order.id, status=OrderStatus.PACKING)

        await callback.answer(f"Заказ #{order_id} взят в сборку!")

        if callback.message:
            if callback.message.document:
                await callback.message.edit_caption(
                    caption=new_text,
                    reply_markup=new_keyboard,
                )
            else:
                await callback.message.edit_text(
                    text=new_text,
                    reply_markup=new_keyboard,
                )


@warehouse_router.callback_query(F.data.startswith("warehouse:ship:"))
async def ship_order_callback(
    callback: CallbackQuery,
    db: Optional[AsyncSession] = None,
):
    """Handler for [ 🚚 Отгружен ] inline button:

    - Calls `OrderService.ship_order` to atomically deduct stock
    - Transitions status to `OrderStatus.SHIPPED`
    - Edits message to «✅ Заказ отгружен» and removes inline buttons
    """
    try:
        order_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("Неверный ID заказа", show_alert=True)
        return

    async for session in _resolve_db(db):
        try:
            from app.services.order_service import OrderService

            order = await OrderService.ship_order(session, order_id)
        except HTTPException as e:
            await callback.answer(f"Ошибка: {e.detail}", show_alert=True)
            return
        except Exception as e:
            await callback.answer(f"Ошибка при отгрузке: {e}", show_alert=True)
            return

        user = callback.from_user
        shipped_by = user.full_name
        if user.username:
            shipped_by += f" (@{user.username})"

        bar_name = order.bar.name if order.bar else "Кофейня"
        new_text = format_order_message(
            order_id=order.id,
            bar_name=bar_name,
            items=order.items,
            status=OrderStatus.SHIPPED,
            shipped_by=shipped_by,
        )

        await callback.answer(f"✅ Заказ #{order_id} успешно отгружен!")

        if callback.message:
            if callback.message.document:
                await callback.message.edit_caption(
                    caption=new_text,
                    reply_markup=None,
                )
            else:
                await callback.message.edit_text(
                    text=new_text,
                    reply_markup=None,
                )
