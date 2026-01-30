"""Settings handler."""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from bot.database.models import User
from bot.keyboards.inline import get_settings_keyboard
from bot.keyboards.reply import get_main_keyboard

router = Router()


@router.message(Command("settings"))
async def cmd_settings(message: Message, user: User):
    """Handle /settings command."""
    await show_settings(message, user)


@router.message(F.text == "⚙️ Настройки")
async def btn_settings(message: Message, user: User):
    """Handle settings button."""
    await show_settings(message, user)


@router.message(Command("level"))
async def cmd_level(message: Message, user: User):
    """Handle /level command."""
    from bot.keyboards.inline import get_level_keyboard

    await message.answer(
        f"📊 <b>Выберите уровень HSK</b>\n\n"
        f"Текущий уровень: <b>HSK {user.hsk_level}</b>\n\n"
        f"• <b>HSK 1</b> — ~150 слов, базовая грамматика\n"
        f"• <b>HSK 2</b> — ~300 слов, простые конструкции\n"
        f"• <b>HSK 3</b> — ~600 слов, средний уровень",
        reply_markup=get_level_keyboard(user.hsk_level),
        parse_mode="HTML"
    )


async def show_settings(message: Message, user: User):
    """Show settings menu."""
    speed_names = {
        "slow": "🐢 Медленная",
        "normal": "🚶 Нормальная",
        "fast": "🏃 Быстрая"
    }

    topic_names = {
        "travel": "✈️ Путешествия",
        "food": "🍜 Еда",
        "work": "💼 Работа",
        "daily": "🏠 Быт",
        "study": "📚 Учёба",
        "health": "🏥 Здоровье",
        "free": "💬 Свободный диалог"
    }

    await message.answer(
        f"⚙️ <b>Настройки</b>\n\n"
        f"📊 Уровень HSK: <b>{user.hsk_level}</b>\n"
        f"🔊 Скорость речи: {speed_names.get(user.speech_speed, 'Нормальная')}\n"
        f"🎯 Тема: {topic_names.get(user.current_topic, 'Быт')}",
        reply_markup=get_settings_keyboard(),
        parse_mode="HTML"
    )
