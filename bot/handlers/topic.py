"""Topic selection handler."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.database.models import User
from bot.keyboards.inline import get_topic_keyboard

router = Router()


TOPICS = {
    "travel": "✈️ Путешествия (旅游)",
    "food": "🍜 Еда (美食)",
    "work": "💼 Работа (工作)",
    "daily": "🏠 Быт (日常生活)",
    "study": "📚 Учёба (学习)",
    "health": "🏥 Здоровье (健康)"
}


@router.message(Command("topic"))
async def cmd_topic(message: Message, user: User):
    """Handle /topic command."""
    current_topic_name = TOPICS.get(user.current_topic, "🏠 Быт")
    
    await message.answer(
        f"🎯 <b>Выберите тему для диалога</b>\n\n"
        f"Текущая тема: <b>{current_topic_name}</b>\n\n"
        f"<i>Выбранная тема влияет на контекст и словарный запас в диалогах.</i>",
        reply_markup=get_topic_keyboard(user.current_topic),
        parse_mode="HTML"
    )
