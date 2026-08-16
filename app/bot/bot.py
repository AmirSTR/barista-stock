import logging
from typing import Any, Awaitable, Callable, Dict, Optional
from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.bot.config import bot_settings
from app.bot.handlers.barista import barista_router
from app.bot.handlers.stoplist import stoplist_router
from app.bot.handlers.supply import supply_router
from app.bot.handlers.warehouse import warehouse_router
from app.core.database import async_session_maker

logger = logging.getLogger(__name__)


class DbSessionMiddleware(BaseMiddleware):
    """Outer middleware that provides an isolated AsyncSession to every Telegram handler."""

    def __init__(self, session_maker: async_sessionmaker):
        super().__init__()
        self.session_maker = session_maker

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with self.session_maker() as session:
            data["db"] = session
            return await handler(event, data)


def create_bot(token: Optional[str] = None) -> Bot:
    """Create an aiogram Bot instance with Markdown parse mode."""
    bot_token = token or bot_settings.TOKEN
    if not bot_token:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN is not configured. Please set it in environment or .env file."
        )
    return Bot(
        token=bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )


def create_dispatcher(session_maker: Optional[async_sessionmaker] = None) -> Dispatcher:
    """Create and configure the aiogram Dispatcher with all application routers."""
    dp = Dispatcher()

    # Register database middleware
    maker = session_maker or async_session_maker
    dp.update.outer_middleware(DbSessionMiddleware(maker))

    # Register sub-routers
    dp.include_router(barista_router)
    dp.include_router(warehouse_router)
    dp.include_router(stoplist_router)
    dp.include_router(supply_router)

    return dp
