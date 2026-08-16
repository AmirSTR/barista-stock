import re
from typing import Optional
from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.barista import (
    get_bar_selection_keyboard,
    get_barista_main_keyboard,
)
from app.core.database import async_session_maker
from app.models.bar import Bar

barista_router = Router(name="barista")


async def _resolve_db(db: Optional[AsyncSession] = None):
    """Context manager or session resolver for DB sessions in handlers."""
    if db is not None:
        yield db
    else:
        async with async_session_maker() as session:
            yield session


@barista_router.message(Command("start"))
async def start_handler(
    message: Message,
    command: Optional[CommandObject] = None,
    db: Optional[AsyncSession] = None,
):
    """Handle /start command for baristas:

    - With deep-link argument (e.g. /start 1 or /start bar_1): binds user to bar.
    - If user is already bound: displays greeting and WebApp order button.
    - If user is not bound: displays list of coffee bars to choose from.
    """
    user_id = message.from_user.id if message.from_user else 0
    first_name = message.from_user.first_name if message.from_user else "Бариста"

    async for session in _resolve_db(db):
        # 1. Check if deep link argument was provided
        if command and command.args:
            raw_arg = command.args.strip()
            # Extract digits from arg like 'bar_1', '1', 'bar-1'
            digits = re.findall(r"\d+", raw_arg)
            if digits:
                bar_id = int(digits[0])
                bar_res = await session.execute(select(Bar).where(Bar.id == bar_id))
                bar = bar_res.scalar_one_or_none()

                if bar and bar.is_active:
                    bar.telegram_chat_id = user_id
                    await session.commit()
                    await session.refresh(bar)

                    await message.answer(
                        f"✅ Вы успешно привязаны к кофейне «{bar.name}»!\n\n"
                        f"Нажмите кнопку ниже, чтобы открыть накладную и сделать заказ расходников:",
                        reply_markup=get_barista_main_keyboard(bar_id=bar.id),
                    )
                    return

        # 2. Check if user is already bound to any bar
        user_bar_res = await session.execute(
            select(Bar).where(Bar.telegram_chat_id == user_id, Bar.is_active.is_(True))
        )
        user_bar = user_bar_res.scalar_one_or_none()

        if user_bar:
            await message.answer(
                f"👋 Привет, {first_name}!\n\n"
                f"☕️ Ваша кофейня: **«{user_bar.name}»**\n\n"
                f"Нажмите кнопку ниже, чтобы открыть накладную и оформить заказ:",
                reply_markup=get_barista_main_keyboard(bar_id=user_bar.id),
            )
            return

        # 3. User is not yet bound: fetch active bars for selection
        bars_res = await session.execute(
            select(Bar).where(Bar.is_active.is_(True)).order_by(Bar.id)
        )
        bars = bars_res.scalars().all()

        if not bars:
            await message.answer(
                f"👋 Привет, {first_name}!\n\n"
                f"В системе пока нет активных кофеен. Обратитесь к администратору склада.",
            )
            return

        await message.answer(
            f"👋 Привет, {first_name}!\n\n"
            f"Для начала работы выберите вашу кофейню из списка ниже:",
            reply_markup=get_bar_selection_keyboard(bars),
        )


@barista_router.message(Command("bind", "bars", "bar"))
async def bind_command_handler(
    message: Message,
    db: Optional[AsyncSession] = None,
):
    """Handle /bind or /bars command to let barista switch or set their coffee bar."""
    async for session in _resolve_db(db):
        bars_res = await session.execute(
            select(Bar).where(Bar.is_active.is_(True)).order_by(Bar.id)
        )
        bars = bars_res.scalars().all()

        if not bars:
            await message.answer("В системе нет доступных кофеен.")
            return

        await message.answer(
            "Выберите вашу кофейню из списка для привязки аккаунта:",
            reply_markup=get_bar_selection_keyboard(bars),
        )


@barista_router.callback_query(F.data.startswith("barista:select_bar:"))
async def select_bar_callback(
    callback: CallbackQuery,
    db: Optional[AsyncSession] = None,
):
    """Process selection of a coffee bar by the barista."""
    user_id = callback.from_user.id if callback.from_user else 0
    bar_id = int(callback.data.split(":")[2])

    async for session in _resolve_db(db):
        bar_res = await session.execute(select(Bar).where(Bar.id == bar_id))
        bar = bar_res.scalar_one_or_none()

        if not bar or not bar.is_active:
            await callback.answer("Кофейня не найдена или неактивна", show_alert=True)
            return

        bar.telegram_chat_id = user_id
        await session.commit()
        await session.refresh(bar)

        await callback.answer(f"Привязано: «{bar.name}»")

        if callback.message:
            await callback.message.edit_text(
                f"✅ Вы успешно привязаны к кофейне «{bar.name}»!\n\n"
                f"Нажмите кнопку ниже, чтобы открыть накладную и сделать заказ:",
                reply_markup=get_barista_main_keyboard(bar_id=bar.id),
            )


@barista_router.callback_query(F.data == "barista:change_bar")
async def change_bar_callback(
    callback: CallbackQuery,
    db: Optional[AsyncSession] = None,
):
    """Prompt barista to choose another coffee bar."""
    async for session in _resolve_db(db):
        bars_res = await session.execute(
            select(Bar).where(Bar.is_active.is_(True)).order_by(Bar.id)
        )
        bars = bars_res.scalars().all()

        await callback.answer()
        if callback.message:
            await callback.message.edit_text(
                "Выберите вашу новую кофейню из списка:",
                reply_markup=get_bar_selection_keyboard(bars),
            )
