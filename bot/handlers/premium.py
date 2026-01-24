"""Premium subscription handler."""

from datetime import datetime, timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import settings
from bot.database.models import User
from bot.keyboards.inline import get_premium_keyboard, get_profile_subscription_keyboard
from bot.middlewares.subscription import get_subscription_status, SubscriptionType

router = Router()


@router.message(Command("premium"))
async def cmd_premium(message: Message, user: User):
    """Handle /premium command."""
    status = get_subscription_status(user)
    
    if status == SubscriptionType.PREMIUM:
        days_left = (user.premium_until - datetime.utcnow()).days
        text = (
            f"💎 <b>Premium активен!</b>\n\n"
            f"Осталось дней: <b>{days_left}</b>\n"
            f"Активен до: {user.premium_until.strftime('%d.%m.%Y')}\n\n"
            f"✅ Безлимитные голосовые сообщения\n"
            f"✅ Безлимитные текстовые сообщения\n"
            f"✅ Приоритетная поддержка"
        )
        await message.answer(
            text,
            reply_markup=get_profile_subscription_keyboard(has_premium=True),
            parse_mode="HTML"
        )
    
    elif status == SubscriptionType.TRIAL:
        trial_end = user.created_at + timedelta(days=settings.TRIAL_DAYS)
        days_left = (trial_end - datetime.utcnow()).days
        text = (
            f"🎁 <b>Триал активен!</b>\n\n"
            f"Осталось дней: <b>{days_left}</b>\n"
            f"Триал заканчивается: {trial_end.strftime('%d.%m.%Y')}\n\n"
            f"После окончания триала:\n"
            f"• 20 текстовых сообщений/день\n"
            f"• 5 голосовых сообщений/день\n\n"
            f"💎 <b>Premium — ₽{settings.PREMIUM_PRICE // 100}/мес</b>\n"
            f"Безлимитный доступ ко всем функциям!"
        )
        await message.answer(
            text, 
            reply_markup=get_premium_keyboard(),
            parse_mode="HTML"
        )
    
    else:  # FREE
        text = (
            f"📊 <b>Free версия</b>\n\n"
            f"Ваши текущие лимиты:\n"
            f"• {settings.FREE_TEXT_LIMIT} текстовых сообщений/день\n"
            f"• {settings.FREE_VOICE_LIMIT} голосовых сообщений/день\n\n"
            f"💎 <b>Premium — ₽{settings.PREMIUM_PRICE // 100}/мес</b>\n\n"
            f"✅ Безлимитные голосовые сообщения\n"
            f"✅ Безлимитные текстовые сообщения\n"
            f"✅ Приоритетная поддержка"
        )
        await message.answer(
            text, 
            reply_markup=get_premium_keyboard(),
            parse_mode="HTML"
        )
