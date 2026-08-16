from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from app.core.config import settings


class IsAdminFilter(BaseFilter):
    """Aiogram 3 custom filter checking if the sender is registered in ADMIN_TELEGRAM_IDS."""

    async def __call__(self, event: TelegramObject) -> bool:
        user = getattr(event, "from_user", None)
        if not user:
            return False
        return user.id in settings.ADMIN_TELEGRAM_IDS
