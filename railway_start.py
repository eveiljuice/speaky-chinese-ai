"""Start bot in webhook mode for Railway deployment."""
import asyncio
import logging
import sys
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from bot.config import settings
from bot.database import init_db
from bot.handlers import setup_routers
from bot.middlewares import AuthMiddleware, SubscriptionMiddleware, ThrottlingMiddleware

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Railway provides PORT env variable
PORT = int(os.environ.get("PORT", 8080))
# Railway provides public URL
RAILWAY_STATIC_URL = os.environ.get("RAILWAY_STATIC_URL", "")


async def on_startup(bot: Bot):
    """Set webhook on startup."""
    # Delete any existing webhook first
    await bot.delete_webhook(drop_pending_updates=True)

    if RAILWAY_STATIC_URL:
        webhook_url = f"{RAILWAY_STATIC_URL}/webhook"
        logger.info(f"Setting webhook: {webhook_url}")
        await bot.set_webhook(webhook_url)
    else:
        logger.warning(
            "⚠️  RAILWAY_STATIC_URL not set! Bot will not receive updates.")


async def on_shutdown(bot: Bot):
    """Remove webhook on shutdown."""
    logger.info("Removing webhook...")
    await bot.delete_webhook()
    await bot.session.close()


async def health_check(request):
    """Health check endpoint for Railway."""
    return web.json_response({
        'status': 'ok',
        'service': 'speaky-chinese-bot',
        'mode': 'webhook'
    })


async def main():
    """Run bot in webhook mode."""
    logger.info("🚀 Starting SpeakyChinese Bot (Railway Webhook Mode)...")

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

    # Register middlewares
    dp.message.middleware(ThrottlingMiddleware(rate_limit=1.0))
    dp.message.middleware(AuthMiddleware())
    dp.message.middleware(SubscriptionMiddleware())

    dp.callback_query.middleware(ThrottlingMiddleware(rate_limit=0.5))
    dp.callback_query.middleware(AuthMiddleware())

    # Register handlers
    router = setup_routers()
    dp.include_router(router)

    # Register startup/shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Create aiohttp app
    app = web.Application()

    # Setup webhook handler
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_handler.register(app, path="/webhook")

    # Add health check
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)

    # Setup application
    setup_application(app, dp, bot=bot)

    logger.info(f"✅ Webhook server starting on port {PORT}")
    logger.info(f"Webhook URL: {RAILWAY_STATIC_URL}/webhook")

    # Run app
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()

    logger.info("✅ Bot is running!")

    # Keep running
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
