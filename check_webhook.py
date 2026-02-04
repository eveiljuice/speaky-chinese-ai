"""Check current webhook status."""
import asyncio
from aiogram import Bot
from bot.config import settings


async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    try:
        info = await bot.get_webhook_info()
        print(f"Webhook URL: {info.url}")
        print(f"Has custom certificate: {info.has_custom_certificate}")
        print(f"Pending update count: {info.pending_update_count}")
        print(f"Last error date: {info.last_error_date}")
        print(f"Last error message: {info.last_error_message}")
        print(f"Max connections: {info.max_connections}")
        print(f"IP address: {info.ip_address}")

        if info.url:
            print("\n⚠️  WEBHOOK IS SET! This conflicts with polling mode.")
            print("To remove webhook, run: python delete_webhook.py")
        else:
            print("\n✅ No webhook set. Polling mode should work.")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
