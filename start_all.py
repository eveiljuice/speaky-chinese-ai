"""Start both bot and webhook server."""
import asyncio
import subprocess
import os
import sys
import signal
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

processes = []


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    logger.info("\n🛑 Stopping all services...")
    for proc in processes:
        try:
            proc.terminate()
        except:
            pass
    sys.exit(0)


async def main():
    """Run both bot and webhook server."""
    # Safety: never run polling bundle on Railway
    if (
        os.environ.get("RAILWAY_STATIC_URL")
        or os.environ.get("RAILWAY_ENVIRONMENT")
        or os.environ.get("RAILWAY_PROJECT_ID")
        or os.environ.get("RAILWAY_SERVICE_ID")
    ):
        logger.error(
            "start_all.py is for local dev only. On Railway use railway_start.py."
        )
        return

    signal.signal(signal.SIGINT, signal_handler)

    logger.info("🚀 Starting SpeakyChinese Bot + Webhook Server...")
    logger.info("Press Ctrl+C to stop all services\n")

    # Start webhook server
    logger.info("📡 Starting webhook server on port 8080...")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    webhook_proc = subprocess.Popen(
        [sys.executable, "-u", "webhook_server.py"],
        env=env
    )
    processes.append(webhook_proc)

    # Wait a bit for webhook to start
    await asyncio.sleep(2)

    # Start telegram bot
    logger.info("🤖 Starting Telegram bot...")
    bot_proc = subprocess.Popen(
        [sys.executable, "-u", "-m", "bot.main"],
        env=env
    )
    processes.append(bot_proc)

    logger.info("\n✅ All services started!")
    logger.info("Webhook: http://localhost:8080/health")
    logger.info("Bot: Running in polling mode\n")

    # Keep running and watch child processes
    try:
        while True:
            # Check if processes are still running
            if webhook_proc.poll() is not None:
                logger.error("❌ Webhook server stopped!")
                break
            if bot_proc.poll() is not None:
                logger.error("❌ Bot stopped!")
                break

            await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
