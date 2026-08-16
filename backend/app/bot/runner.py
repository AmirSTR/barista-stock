import asyncio
import logging
import sys
from app.bot.bot import create_bot, create_dispatcher
from app.bot.config import bot_settings
from app.core.database import engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
)
logger = logging.getLogger("app.bot")


async def main():
    if not bot_settings.TOKEN:
        logger.error(
            "TELEGRAM_BOT_TOKEN is not set! Please set TELEGRAM_BOT_TOKEN in .env or environment variables."
        )
        sys.exit(1)

    logger.info("Starting Telegram Bot for Coffee Chain Inventory...")
    bot = create_bot()
    dp = create_dispatcher()

    try:
        # Drop pending updates to avoid processing stale backlog on startup
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot started successfully. Waiting for updates...")
        await dp.start_polling(bot)
    finally:
        logger.info("Shutting down bot...")
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
