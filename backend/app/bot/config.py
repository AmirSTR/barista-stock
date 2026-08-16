from typing import Optional
from app.core.config import settings


class BotConfig:
    @property
    def TOKEN(self) -> Optional[str]:
        return settings.TELEGRAM_BOT_TOKEN

    @property
    def WAREHOUSE_CHAT_ID(self) -> Optional[int]:
        return settings.TELEGRAM_WAREHOUSE_CHAT_ID

    @property
    def WEBAPP_URL(self) -> str:
        return settings.WEBAPP_URL

    @property
    def ADMIN_TELEGRAM_IDS(self) -> list[int]:
        return settings.ADMIN_TELEGRAM_IDS


bot_settings = BotConfig()
