"""Subscription middleware - checks limits for free users."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message

from bot.config import settings
from bot.database.models import User
from bot.database.repositories import DailyUsageRepository
from bot.keyboards.inline import get_premium_keyboard


class SubscriptionType(Enum):
    """Subscription types."""
    TRIAL = "trial"
    FREE = "free"
    PREMIUM = "premium"


def get_subscription_status(user: User) -> SubscriptionType:
    """Determine user's subscription status."""
    now = datetime.utcnow()
    
    # 1. Check Premium
    if user.premium_until and user.premium_until > now:
        return SubscriptionType.PREMIUM
    
    # 2. Check Trial (3 days from registration)
    trial_end = user.created_at + timedelta(days=settings.TRIAL_DAYS)
    if now < trial_end:
        return SubscriptionType.TRIAL
    
    # 3. Otherwise Free
    return SubscriptionType.FREE


class SubscriptionMiddleware(BaseMiddleware):
    """Middleware that checks subscription limits."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Only check for messages (not callbacks)
        if not isinstance(event, Message):
            return await handler(event, data)
        
        user: User = data.get("user")
        if not user:
            return await handler(event, data)
        
        # Get subscription status
        status = get_subscription_status(user)
        data["subscription_status"] = status
        
        # Trial and Premium - no limits
        if status in (SubscriptionType.TRIAL, SubscriptionType.PREMIUM):
            return await handler(event, data)
        
        # Free tier - check limits
        usage_repo = DailyUsageRepository()
        usage = await usage_repo.get_or_create(user.id)
        
        # Check if this is a voice or text message
        is_voice = event.voice is not None
        
        if is_voice:
            if usage.voice_count >= settings.FREE_VOICE_LIMIT:
                await event.answer(
                    f"📊 <b>Дневной лимит достигнут</b>\n\n"
                    f"Вы использовали {usage.voice_count}/{settings.FREE_VOICE_LIMIT} "
                    f"голосовых сообщений сегодня.\n"
                    f"Лимит сбросится в 00:00 по МСК.\n\n"
                    f"💎 Хотите безлимитный доступ?",
                    reply_markup=get_premium_keyboard(),
                    parse_mode="HTML"
                )
                return None
        elif event.text and not event.text.startswith("/"):
            # Text message (not a command)
            if usage.text_count >= settings.FREE_TEXT_LIMIT:
                await event.answer(
                    f"📊 <b>Дневной лимит достигнут</b>\n\n"
                    f"Вы использовали {usage.text_count}/{settings.FREE_TEXT_LIMIT} "
                    f"текстовых сообщений сегодня.\n"
                    f"Лимит сбросится в 00:00 по МСК.\n\n"
                    f"💎 Хотите безлимитный доступ?",
                    reply_markup=get_premium_keyboard(),
                    parse_mode="HTML"
                )
                return None
        
        return await handler(event, data)
