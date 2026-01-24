"""Main entry point for the bot."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.database import init_db
from bot.handlers import setup_routers
from bot.middlewares import AuthMiddleware, SubscriptionMiddleware, ThrottlingMiddleware


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to start the bot."""
    logger.info("Starting SpeakyChinese bot...")
    
    # Initialize database
    logger.info("Initializing database...")
    await init_db()
    
    # Create bot instance
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Create dispatcher
    dp = Dispatcher()
    
    # Register middlewares (order matters!)
    dp.message.middleware(ThrottlingMiddleware(rate_limit=1.0))
    dp.message.middleware(AuthMiddleware())
    dp.message.middleware(SubscriptionMiddleware())
    
    dp.callback_query.middleware(ThrottlingMiddleware(rate_limit=0.5))
    dp.callback_query.middleware(AuthMiddleware())
    
    # Register handlers
    router = setup_routers()
    dp.include_router(router)
    
    # Start polling
    logger.info("Bot started! Polling for updates...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
