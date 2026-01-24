"""Start command handler with onboarding."""

from aiogram import Router, F
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import Message

from bot.database.models import User
from bot.database.repositories import UserRepository, ReferralRepository
from bot.keyboards.reply import get_main_keyboard

router = Router()


@router.message(CommandStart(deep_link=True))
async def cmd_start_with_referral(
    message: Message, 
    command: CommandObject,
    user: User
):
    """Handle /start with referral deep link (e.g., /start ref_abc123)."""
    referral_code = command.args
    
    # Check if it's a referral link
    if referral_code and referral_code.startswith("ref_"):
        code = referral_code[4:]  # Remove "ref_" prefix
        
        user_repo = UserRepository()
        referrer = await user_repo.get_by_referral_code(code)
        
        if referrer and referrer.id != user.id:
            # Check if this is a new user (created just now by middleware)
            # We can check if user has no referrer yet
            if not user.referrer_id:
                # Update user's referrer
                await user_repo.update(user.id, referrer_id=referrer.id)
                
                # Create referral record
                referral_repo = ReferralRepository()
                created = await referral_repo.create(referrer.id, user.id)
                
                if created:
                    # Give bonus days to both users (+7 days each)
                    await user_repo.add_premium_days(referrer.id, 7)
                    await user_repo.add_premium_days(user.id, 7)
                    
                    # Notify referrer
                    try:
                        await message.bot.send_message(
                            referrer.id,
                            f"🎉 Ваш друг {user.first_name} зарегистрировался по вашей ссылке!\n"
                            f"Вам начислено +7 дней Premium"
                        )
                    except Exception:
                        pass  # Referrer might have blocked the bot
    
    # Show welcome message
    await show_welcome(message, user)


@router.message(CommandStart())
async def cmd_start(message: Message, user: User):
    """Handle /start command."""
    await show_welcome(message, user)


async def show_welcome(message: Message, user: User):
    """Show welcome/onboarding message."""
    welcome_text = f"""🎉 <b>Добро пожаловать в SpeakyChinese!</b>

Привет, <b>{user.first_name}</b>! Я помогу тебе практиковать разговорный китайский язык.

<b>🎁 У тебя 3 дня бесплатного Premium!</b>
<i>Полный доступ ко всем функциям</i>

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
        parse_mode="HTML"
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
        "health": "🏥 Здоровье"
    }
    return topics.get(topic, "🏠 Быт")


def _get_speed_name(speed: str) -> str:
    """Get Russian speed name."""
    speeds = {
        "slow": "🐢 Медленная",
        "normal": "🚶 Нормальная",
        "fast": "🏃 Быстрая"
    }
    return speeds.get(speed, "🚶 Нормальная")
