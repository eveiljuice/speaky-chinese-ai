"""Start both bot and webhook server."""
import asyncio
import subprocess
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
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info("🚀 Starting SpeakyChinese Bot + Webhook Server...")
    logger.info("Press Ctrl+C to stop all services\n")
    
    # Start webhook server
    logger.info("📡 Starting webhook server on port 8080...")
    webhook_proc = subprocess.Popen(
        [sys.executable, "webhook_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    processes.append(webhook_proc)
    
    # Wait a bit for webhook to start
    await asyncio.sleep(2)
    
    # Start telegram bot
    logger.info("🤖 Starting Telegram bot...")
    bot_proc = subprocess.Popen(
        [sys.executable, "-m", "bot.main"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    processes.append(bot_proc)
    
    logger.info("\n✅ All services started!")
    logger.info("Webhook: http://localhost:8080/health")
    logger.info("Bot: Running in polling mode\n")
    
    # Keep running and show logs
    try:
        while True:
            # Read webhook logs
            if webhook_proc.poll() is None:
                line = webhook_proc.stdout.readline()
                if line:
                    print(f"[WEBHOOK] {line.strip()}")
            
            # Read bot logs
            if bot_proc.poll() is None:
                line = bot_proc.stdout.readline()
                if line:
                    print(f"[BOT] {line.strip()}")
            
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
