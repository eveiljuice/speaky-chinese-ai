"""Callback query handlers for inline buttons."""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.database.models import User
from bot.database.repositories import UserRepository, MessageRepository
from bot.keyboards.inline import (
    get_topic_keyboard,
    get_level_keyboard,
    get_speed_keyboard,
    get_settings_keyboard
)

router = Router()


# Topic selection
@router.callback_query(F.data.startswith("topic:"))
async def callback_topic(callback: CallbackQuery, user: User):
    """Handle topic selection."""
    topic = callback.data.split(":")[1]

    topics = {
        "travel": "✈️ Путешествия",
        "food": "🍜 Еда",
        "work": "💼 Работа",
        "daily": "🏠 Быт",
        "study": "📚 Учёба",
        "health": "🏥 Здоровье",
        "free": "💬 Свободный диалог"
    }

    if topic not in topics:
        await callback.answer("Неизвестная тема")
        return

    # Update user's topic
    repo = UserRepository()
    await repo.update(user.id, current_topic=topic)

    await callback.answer(f"✅ Тема изменена на: {topics[topic]}")
    await callback.message.edit_text(
        f"🎯 <b>Выберите тему для диалога</b>\n\n"
        f"Текущая тема: <b>{topics[topic]}</b>\n\n"
        f"<i>Выбранная тема влияет на контекст и словарный запас в диалогах.</i>",
        reply_markup=get_topic_keyboard(topic),
        parse_mode="HTML"
    )


# Level selection
@router.callback_query(F.data.startswith("level:"))
async def callback_level(callback: CallbackQuery, user: User):
    """Handle HSK level selection."""
    level = int(callback.data.split(":")[1])

    if level not in [1, 2, 3]:
        await callback.answer("Неверный уровень")
        return

    # Update user's level
    repo = UserRepository()
    await repo.update(user.id, hsk_level=level)

    await callback.answer(f"✅ Уровень изменён на HSK {level}")
    await callback.message.edit_text(
        f"📊 <b>Выберите уровень HSK</b>\n\n"
        f"Текущий уровень: <b>HSK {level}</b>\n\n"
        f"• <b>HSK 1</b> — ~150 слов, базовая грамматика\n"
        f"• <b>HSK 2</b> — ~300 слов, простые конструкции\n"
        f"• <b>HSK 3</b> — ~600 слов, средний уровень",
        reply_markup=get_level_keyboard(level),
        parse_mode="HTML"
    )


# Speed selection
@router.callback_query(F.data.startswith("speed:"))
async def callback_speed(callback: CallbackQuery, user: User):
    """Handle speech speed selection."""
    speed = callback.data.split(":")[1]

    speeds = {
        "slow": "🐢 Медленная",
        "normal": "🚶 Нормальная",
        "fast": "🏃 Быстрая"
    }

    if speed not in speeds:
        await callback.answer("Неверная скорость")
        return

    # Update user's speed
    repo = UserRepository()
    await repo.update(user.id, speech_speed=speed)

    await callback.answer(f"✅ Скорость изменена на: {speeds[speed]}")
    await callback.message.edit_text(
        f"🔊 <b>Выберите скорость речи</b>\n\n"
        f"Текущая скорость: <b>{speeds[speed]}</b>\n\n"
        f"<b>🐢 Медленно</b> — для начинающих\n"
        f"<b>🚶 Нормально</b> — естественная речь\n"
        f"<b>🏃 Быстро</b> — как носители языка",
        reply_markup=get_speed_keyboard(speed),
        parse_mode="HTML"
    )


# Settings menu navigation
@router.callback_query(F.data.startswith("settings:"))
async def callback_settings(callback: CallbackQuery, user: User):
    """Handle settings menu navigation."""
    action = callback.data.split(":")[1]

    if action == "level":
        await callback.message.edit_text(
            f"📊 <b>Выберите уровень HSK</b>\n\n"
            f"Текущий уровень: <b>HSK {user.hsk_level}</b>\n\n"
            f"• <b>HSK 1</b> — ~150 слов, базовая грамматика\n"
            f"• <b>HSK 2</b> — ~300 слов, простые конструкции\n"
            f"• <b>HSK 3</b> — ~600 слов, средний уровень",
            reply_markup=get_level_keyboard(user.hsk_level),
            parse_mode="HTML"
        )

    elif action == "speed":
        speeds = {
            "slow": "🐢 Медленная",
            "normal": "🚶 Нормальная",
            "fast": "🏃 Быстрая"
        }
        await callback.message.edit_text(
            f"🔊 <b>Выберите скорость речи</b>\n\n"
            f"Текущая скорость: <b>{speeds.get(user.speech_speed, 'Нормальная')}</b>\n\n"
            f"<b>🐢 Медленно</b> — для начинающих\n"
            f"<b>🚶 Нормально</b> — естественная речь\n"
            f"<b>🏃 Быстро</b> — как носители языка",
            reply_markup=get_speed_keyboard(user.speech_speed),
            parse_mode="HTML"
        )

    elif action == "topic":
        from bot.handlers.topic import TOPICS
        current_topic_name = TOPICS.get(user.current_topic, "🏠 Быт")
        await callback.message.edit_text(
            f"🎯 <b>Выберите тему для диалога</b>\n\n"
            f"Текущая тема: <b>{current_topic_name}</b>\n\n"
            f"<i>Выбранная тема влияет на контекст и словарный запас в диалогах.</i>",
            reply_markup=get_topic_keyboard(user.current_topic),
            parse_mode="HTML"
        )

    elif action == "close":
        # Close settings menu by deleting the message
        await callback.message.delete()
        await callback.answer("Настройки закрыты")
        return

    elif action == "back":
        # Return to main settings menu
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

        await callback.message.edit_text(
            f"⚙️ <b>Настройки</b>\n\n"
            f"📊 Уровень HSK: <b>{user.hsk_level}</b>\n"
            f"🔊 Скорость речи: {speed_names.get(user.speech_speed, 'Нормальная')}\n"
            f"🎯 Тема: {topic_names.get(user.current_topic, 'Быт')}",
            reply_markup=get_settings_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    await callback.answer()


# Message-related callbacks (text, help, translate, explain)
@router.callback_query(F.data.startswith("text:"))
async def callback_text(callback: CallbackQuery, user: User):
    """Show message text (Chinese + Pinyin)."""
    message_id = int(callback.data.split(":")[1])

    msg_repo = MessageRepository()
    msg = await msg_repo.get(message_id)

    if not msg:
        await callback.answer("Сообщение не найдено", show_alert=True)
        return

    # Show Chinese text with pinyin
    text = f"📝 <b>Текст:</b>\n\n<b>{msg.content}</b>"
    if msg.pinyin:
        text += f"\n\n<i>{msg.pinyin}</i>"

    await callback.answer()
    await callback.message.reply(text, parse_mode="HTML")


@router.callback_query(F.data.startswith("help:"))
async def callback_help(callback: CallbackQuery, user: User):
    """Show help/suggestions for continuing dialogue."""
    message_id = int(callback.data.split(":")[1])

    msg_repo = MessageRepository()
    msg = await msg_repo.get(message_id)

    if not msg:
        await callback.answer("Сообщение не найдено", show_alert=True)
        return

    # Generate suggestions based on the message
    from bot.services.ai import generate_response

    # Get conversation history for context
    history = await msg_repo.get_history(user.id, limit=10, topic=user.current_topic)
    history_for_ai = [{"role": m.role, "content": m.content} for m in history]

    await callback.answer("Генерирую подсказки...")

    # Ask for suggestions
    try:
        result = await generate_response(
            user_message="请给我2-3个简单的回复建议",
            history=history_for_ai,
            topic=user.current_topic,
            hsk_level=user.hsk_level
        )

        suggestions = result.get("suggestions", [])
        if suggestions:
            text = "💬 <b>Варианты ответа:</b>\n\n"
            for i, s in enumerate(suggestions[:3], 1):
                # Handle both old format (string) and new format (dict with text and pinyin)
                if isinstance(s, dict):
                    chinese_text = s.get("text", "")
                    pinyin = s.get("pinyin", "")
                    if pinyin:
                        text += f"<b>{i}.</b> {chinese_text} - {pinyin}\n"
                    else:
                        text += f"<b>{i}.</b> {chinese_text}\n"
                else:
                    # Fallback for old string format
                    text += f"<b>{i}.</b> {s}\n"
            await callback.message.reply(text, parse_mode="HTML")
        else:
            await callback.message.reply(
                "💬 <i>Попробуйте ответить на вопрос или задать свой.</i>",
                parse_mode="HTML"
            )
    except Exception:
        await callback.message.reply(
            "💬 <i>Попробуйте ответить на вопрос или продолжить тему диалога.</i>",
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("translate:"))
async def callback_translate(callback: CallbackQuery, user: User):
    """Show translation to Russian."""
    message_id = int(callback.data.split(":")[1])

    msg_repo = MessageRepository()
    msg = await msg_repo.get(message_id)

    if not msg:
        await callback.answer("Сообщение не найдено", show_alert=True)
        return

    if msg.translation:
        text = f"🔄 <b>Перевод:</b>\n\n<i>{msg.translation}</i>"
    else:
        # Generate translation on the fly
        from bot.services.ai import get_word_info
        try:
            info = await get_word_info(msg.content)
            text = f"🔄 <b>Перевод:</b>\n\n<i>{info.get('translation', 'Перевод недоступен')}</i>"
        except Exception:
            text = "🔄 <b>Перевод недоступен</b>"

    await callback.answer()
    await callback.message.reply(text, parse_mode="HTML")


@router.callback_query(F.data.startswith("explain:"))
async def callback_explain(callback: CallbackQuery, user: User):
    """Show detailed error explanation."""
    message_id = int(callback.data.split(":")[1])

    msg_repo = MessageRepository()
    msg = await msg_repo.get(message_id)

    if not msg or not msg.correction:
        await callback.answer("Нет исправлений для объяснения", show_alert=True)
        return

    correction = msg.correction

    # Check if there's already an explanation
    explanation = correction.get("explanation", "")

    if explanation and len(explanation) > 50:
        # Use existing explanation
        text = f"💡 <b>Объяснение:</b>\n\n<i>{explanation}</i>"
    else:
        # Generate detailed explanation
        from bot.services.ai import explain_correction
        await callback.answer("Генерирую объяснение...")

        try:
            detailed = await explain_correction(
                original=correction.get("original", ""),
                corrected=correction.get("corrected", ""),
                hsk_level=user.hsk_level
            )
            text = f"💡 <b>Объяснение:</b>\n\n<i>{detailed}</i>"
        except Exception:
            text = f"💡 <b>Объяснение:</b>\n\n<i>{explanation or 'Объяснение недоступно'}</i>"

    await callback.answer()
    await callback.message.reply(text, parse_mode="HTML")


# Noop callback (for pagination current page indicator)
@router.callback_query(F.data == "noop")
async def callback_noop(callback: CallbackQuery):
    """Do nothing."""
    await callback.answer()
