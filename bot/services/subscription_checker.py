"""Background service that checks for expired trials/premiums and notifies users."""

import asyncio
import logging
from datetime import datetime

from aiogram import Bot

from bot.config import settings
from bot.database.repositories import UserRepository

logger = logging.getLogger(__name__)

# Check interval: every 1 hour
CHECK_INTERVAL_SECONDS = 3600


def _get_premium_keyboard_markup():
    """Build inline keyboard with Tribute payment button."""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    buttons = []
    if settings.TRIBUTE_PAYMENT_LINK:
        buttons.append([
            InlineKeyboardButton(
                text="💎 Купить Premium — ₽770/мес",
                url=settings.TRIBUTE_PAYMENT_LINK
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None


async def _notify_trial_expired(bot: Bot, user_repo: UserRepository) -> int:
    """Notify users whose trial period has ended. Returns count of notified users."""
    users = await user_repo.get_expired_trial_users()
    notified = 0

    for user in users:
        try:
            keyboard = _get_premium_keyboard_markup()
            await bot.send_message(
                user.id,
                "⏰ <b>Ваш бесплатный триал закончился!</b>\n\n"
                "Вы использовали 3 дня полного доступа.\n"
                "Теперь действуют лимиты Free-версии:\n\n"
                f"• {settings.FREE_TEXT_LIMIT} текстовых сообщений/день\n"
                f"• {settings.FREE_VOICE_LIMIT} голосовых сообщений/день\n\n"
                "💎 <b>Хотите продолжить без ограничений?</b>\n"
                f"Подписка Premium — всего ₽{settings.PREMIUM_PRICE // 100}/мес\n\n"
                "✅ Безлимитные голосовые и текстовые сообщения\n"
                "✅ Приоритетная поддержка",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            notified += 1
        except Exception as e:
            logger.warning(f"Failed to notify user {user.id} about trial expiry: {e}")

        # Always mark as notified to avoid retrying failed sends forever
        await user_repo.mark_trial_notified(user.id)

    return notified


async def _notify_premium_expired(bot: Bot, user_repo: UserRepository) -> int:
    """Notify users whose premium subscription has expired. Returns count of notified users."""
    users = await user_repo.get_expired_premium_users()
    notified = 0

    for user in users:
        try:
            keyboard = _get_premium_keyboard_markup()
            await bot.send_message(
                user.id,
                "⏰ <b>Ваша подписка Premium истекла!</b>\n\n"
                "К сожалению, срок действия вашей Premium-подписки закончился.\n"
                "Теперь действуют лимиты Free-версии:\n\n"
                f"• {settings.FREE_TEXT_LIMIT} текстовых сообщений/день\n"
                f"• {settings.FREE_VOICE_LIMIT} голосовых сообщений/день\n\n"
                "💎 <b>Продлите подписку, чтобы продолжить без ограничений!</b>\n"
                f"Premium — ₽{settings.PREMIUM_PRICE // 100}/мес",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            notified += 1
        except Exception as e:
            logger.warning(f"Failed to notify user {user.id} about premium expiry: {e}")

        # Always mark as notified to avoid retrying failed sends forever
        await user_repo.mark_premium_expired_notified(user.id)

    return notified


async def check_subscriptions(bot: Bot) -> None:
    """Run a single check for expired trials and premiums."""
    user_repo = UserRepository()

    trial_count = await _notify_trial_expired(bot, user_repo)
    premium_count = await _notify_premium_expired(bot, user_repo)

    if trial_count or premium_count:
        logger.info(
            f"Subscription check: {trial_count} trial expiry notifications, "
            f"{premium_count} premium expiry notifications sent."
        )


async def start_subscription_checker(bot: Bot) -> None:
    """Start the periodic subscription checker as a background task.
    
    Runs check_subscriptions every CHECK_INTERVAL_SECONDS (1 hour).
    """
    logger.info(f"Subscription checker started (interval: {CHECK_INTERVAL_SECONDS}s)")

    while True:
        try:
            await check_subscriptions(bot)
        except Exception as e:
            logger.error(f"Subscription checker error: {e}", exc_info=True)

        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
