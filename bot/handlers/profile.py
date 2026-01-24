"""Profile handler."""

from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import Message

from bot.config import settings
from bot.database.models import User
from bot.database.repositories import MessageRepository, DailyUsageRepository
from bot.keyboards.inline import get_profile_subscription_keyboard
from bot.middlewares.subscription import get_subscription_status, SubscriptionType

router = Router()


@router.message(F.text == "👤 Профиль")
async def btn_profile(message: Message, user: User):
    """Handle profile button."""
    # Get subscription status
    status = get_subscription_status(user)

    # Format subscription info
    if status == SubscriptionType.PREMIUM:
        days_left = (user.premium_until - datetime.utcnow()).days
        sub_text = f"💎 Premium (осталось {days_left} дн.)"
    elif status == SubscriptionType.TRIAL:
        trial_end = user.created_at + timedelta(days=settings.TRIAL_DAYS)
        days_left = (trial_end - datetime.utcnow()).days
        sub_text = f"🎁 Триал (осталось {days_left} дн.)"
    else:
        sub_text = "📊 Free"

    # Get usage for today
    usage_repo = DailyUsageRepository()
    usage = await usage_repo.get_or_create(user.id)

    # Format limits for free users
    limits_text = ""
    if status == SubscriptionType.FREE:
        limits_text = (
            f"\n\n📈 <b>Использовано сегодня:</b>\n"
            f"• Текст: {usage.text_count}/{settings.FREE_TEXT_LIMIT}\n"
            f"• Голос: {usage.voice_count}/{settings.FREE_VOICE_LIMIT}"
        )

    topic_names = {
        "travel": "✈️ Путешествия",
        "food": "🍜 Еда",
        "work": "💼 Работа",
        "daily": "🏠 Быт",
        "study": "📚 Учёба",
        "health": "🏥 Здоровье"
    }

    speed_names = {
        "slow": "🐢 Медленная",
        "normal": "🚶 Нормальная",
        "fast": "🏃 Быстрая"
    }

    # Get subscription keyboard based on premium status
    has_premium = status == SubscriptionType.PREMIUM
    keyboard = get_profile_subscription_keyboard(has_premium)

    await message.answer(
        f"👤 <b>Профиль</b>\n\n"
        f"<b>Имя:</b> {user.first_name}\n"
        f"<b>Username:</b> @{user.username or 'не указан'}\n"
        f"<b>ID:</b> <code>{user.id}</code>\n\n"
        f"<b>Подписка:</b> {sub_text}\n"
        f"<b>Регистрация:</b> {user.created_at.strftime('%d.%m.%Y')}\n\n"
        f"<b>Настройки:</b>\n"
        f"• Уровень: HSK {user.hsk_level}\n"
        f"• Тема: {topic_names.get(user.current_topic, 'Быт')}\n"
        f"• Скорость: {speed_names.get(user.speech_speed, 'Нормальная')}"
        f"{limits_text}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
