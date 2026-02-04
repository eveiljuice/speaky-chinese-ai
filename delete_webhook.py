"""Delete webhook and switch to polling mode."""
import asyncio
from aiogram import Bot
from bot.config import settings


async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    try:
        # Get current webhook info
        info = await bot.get_webhook_info()
        print(f"Current webhook URL: {info.url or 'None'}")

        if info.url:
            print("\nDeleting webhook...")
            await bot.delete_webhook(drop_pending_updates=True)
            print("✅ Webhook deleted successfully!")
            print("You can now run bot in polling mode: python -m bot.main")
        else:
            print("\n✅ No webhook set. Bot is ready for polling mode.")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
