"""Start command handler with onboarding."""

from aiogram import Router
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import Message

from bot.database.models import User
from bot.database.repositories import (
    UserRepository,
    ReferralRepository,
    GiftLinkRepository,
    PaymentRepository,
)
from bot.keyboards.reply import get_main_keyboard

router = Router()


@router.message(CommandStart(deep_link=True))
async def cmd_start_with_deeplink(
    message: Message,
    command: CommandObject,
    user: User,
):
    """Handle /start with deep link (gift_ or ref_)."""
    args = command.args
    gift_granted = False

    if args and args.startswith("gift_"):
        gift_granted = await _redeem_gift_link(message, user, args[5:])

    if args and args.startswith("ref_"):
        await _process_referral(message, user, args[4:])

    await show_welcome(message, user, gift_granted=gift_granted)


async def _redeem_gift_link(message: Message, user: User, token: str) -> bool:
    """Redeem one-time gift link. Returns True if premium was granted."""
    gift_repo = GiftLinkRepository()
    status, gift = await gift_repo.redeem(token, user.id)

    if status == "ok" and gift:
        user_repo = UserRepository()
        new_until = await user_repo.add_premium_days(user.id, gift.days_granted)

        payment_repo = PaymentRepository()
        await payment_repo.create(
            user_id=user.id,
            amount=0,
            days_granted=gift.days_granted,
            source="promo",
        )

        days_label = (
            "♾️ навсегда" if gift.days_granted >= 36500
            else f"{gift.days_granted} дней"
        )
        await message.answer(
            f"🎁 <b>Premium активирован!</b>\n\n"
            f"Вам выдан Premium на <b>{days_label}</b>\n"
            f"Активен до: {new_until.strftime('%d.%m.%Y')}",
            parse_mode="HTML",
        )
        return True

    if status == "used":
        await message.answer(
            "⚠️ Эта gift-ссылка уже была использована.",
            parse_mode="HTML",
        )
    elif status == "expired":
        await message.answer(
            "⚠️ Срок действия этой gift-ссылки истёк.",
            parse_mode="HTML",
        )
    elif status == "not_found":
        await message.answer(
            "⚠️ Gift-ссылка не найдена.",
            parse_mode="HTML",
        )

    return False


async def _process_referral(message: Message, user: User, code: str) -> None:
    """Process referral deep link."""
    user_repo = UserRepository()
    referrer = await user_repo.get_by_referral_code(code)

    if referrer and referrer.id != user.id and not user.referrer_id:
        await user_repo.update(user.id, referrer_id=referrer.id)

        referral_repo = ReferralRepository()
        created = await referral_repo.create(referrer.id, user.id)

        if created:
            await user_repo.add_premium_days(referrer.id, 7)
            await user_repo.add_premium_days(user.id, 7)

            try:
                await message.bot.send_message(
                    referrer.id,
                    f"🎉 Ваш друг {user.first_name} зарегистрировался по вашей ссылке!\n"
                    f"Вам начислено +7 дней Premium",
                )
            except Exception:
                pass


@router.message(CommandStart())
async def cmd_start(message: Message, user: User):
    """Handle /start command."""
    await show_welcome(message, user)


async def show_welcome(message: Message, user: User, gift_granted: bool = False):
    """Show welcome/onboarding message."""
    premium_note = ""
    if gift_granted:
        premium_note = "\n<b>💎 Premium уже активирован по gift-ссылке!</b>\n"
    else:
        premium_note = "\n<b>🎁 У тебя 3 дня бесплатного Premium!</b>\n<i>Полный доступ ко всем функциям</i>\n"

    welcome_text = f"""🎉 <b>Добро пожаловать в SpeakyChinese!</b>

Привет, <b>{user.first_name}</b>! Я помогу тебе практиковать разговорный китайский язык.
{premium_note}
<b>Как это работает:</b>
<b>1️⃣</b> Отправь голосовое сообщение на китайском
<b>2️⃣</b> Я отвечу голосом и исправлю ошибки
<b>3️⃣</b> Нажми кнопки под сообщением для текста/перевода

<b>Команды:</b>
• <code>/topic</code> — выбрать тему диалога
• <code>/level</code> — изменить уровень HSK
• <code>/settings</code> — настройки
• <code>/invite</code> — пригласить друга
• <code>/premium</code> — информация о подписке
• <code>/help</code> — справка

<b>Текущие настройки:</b>
📊 Уровень: <b>HSK {user.hsk_level}</b>
🎯 Тема: {_get_topic_name(user.current_topic)}
🔊 Скорость: {_get_speed_name(user.speech_speed)}

<b>Начни говорить! 🎤</b>"""

    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message, user: User):
    """Handle /help command."""
    help_text = """📚 <b>Справка по SpeakyChinese</b>

<b>Основные функции:</b>
• Отправляй голосовые сообщения на китайском
• Получай ответы голосом с текстом и переводом
• Автоматическое исправление ошибок

<b>Кнопки под ответом:</b>
<b>📝 Текст</b> — показать иероглифы и пиньинь
<b>❓ Помощь</b> — варианты ответа
<b>🔄 Перевод</b> — перевод на русский
<b>💡 Объяснить</b> — объяснение ошибки

<b>Команды:</b>
• <code>/start</code> — начать сначала
• <code>/topic</code> — выбрать тему (путешествия, еда, работа...)
• <code>/level</code> — изменить уровень HSK (1-3)
• <code>/settings</code> — все настройки
• <code>/invite</code> — реферальная программа
• <code>/premium</code> — информация о подписке
• <code>/help</code> — эта справка

<b>Уровни HSK:</b>
• <b>HSK 1</b> — ~150 слов, базовая грамматика
• <b>HSK 2</b> — ~300 слов, простые конструкции
• <b>HSK 3</b> — ~600 слов, средний уровень

<b>Лимиты Free версии:</b>
• 20 текстовых сообщений/день
• 5 голосовых сообщений/день

💎 <b>Premium</b> — безлимитный доступ!"""

    await message.answer(help_text, parse_mode="HTML")


def _get_topic_name(topic: str) -> str:
    """Get Russian topic name."""
    topics = {
        "travel": "✈️ Путешествия",
        "food": "🍜 Еда",
        "work": "💼 Работа",
        "daily": "🏠 Быт",
        "study": "📚 Учёба",
        "health": "🏥 Здоровье",
    }
    return topics.get(topic, "🏠 Быт")


def _get_speed_name(speed: str) -> str:
    """Get Russian speed name."""
    speeds = {
        "slow": "🐢 Медленная",
        "normal": "🚶 Нормальная",
        "fast": "🏃 Быстрая",
    }
    return speeds.get(speed, "🚶 Нормальная")
