"""Dialog handler - processes voice and text messages."""

import io
import logging
from typing import Optional

from aiogram import Router, F, Bot
from aiogram.types import Message, BufferedInputFile

from bot.config import settings
from bot.database.models import User
from bot.database.repositories import MessageRepository, DailyUsageRepository
from bot.keyboards.inline import get_message_keyboard
from bot.services.ai import transcribe, generate_response, synthesize

router = Router()
logger = logging.getLogger(__name__)

# Menu button texts to ignore
MENU_BUTTONS = {"👤 Профиль", "⚙️ Настройки"}


@router.message(F.voice)
async def handle_voice(message: Message, user: User, bot: Bot):
    """Handle voice messages - full AI processing."""
    voice = message.voice
    
    # Check voice duration limit
    if voice.duration > settings.MAX_VOICE_DURATION:
        await message.answer(
            f"⚠️ Голосовое сообщение слишком длинное.\n"
            f"Максимум: {settings.MAX_VOICE_DURATION} секунд.\n"
            f"Ваше: {voice.duration} секунд."
        )
        return
    
    # Show typing indicator
    await bot.send_chat_action(chat_id=message.chat.id, action="record_voice")
    
    try:
        # 1. Download audio
        file = await bot.get_file(voice.file_id)
        audio_bytes = await bot.download_file(file.file_path)
        audio_data = audio_bytes.read()
        
        # 2. Transcribe with Whisper
        chinese_text = await transcribe(audio_data)
        
        if not chinese_text.strip():
            await message.answer(
                "🤔 Не удалось распознать речь.\n"
                "Попробуйте говорить чётче или ближе к микрофону."
            )
            return
        
        # Process the Chinese text (removed transcription message display)
        await process_chinese_message(
            message=message,
            user=user,
            chinese_text=chinese_text,
            is_voice=True
        )
        
        # Increment voice counter
        usage_repo = DailyUsageRepository()
        await usage_repo.increment_voice(user.id)
        
    except Exception as e:
        logger.error(f"Voice processing error: {e}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка при обработке голосового сообщения.\n"
            "Пожалуйста, попробуйте ещё раз."
        )


@router.message(F.text)
async def handle_text(message: Message, user: User, bot: Bot):
    """Handle text messages - full AI processing."""
    text = message.text
    
    # Skip if it's a command
    if text.startswith("/"):
        return
    
    # Skip menu buttons (handled by other handlers)
    if text in MENU_BUTTONS:
        return
    
    # Check text length limit
    if len(text) > settings.MAX_TEXT_LENGTH:
        await message.answer(
            f"⚠️ Сообщение слишком длинное.\n"
            f"Максимум: {settings.MAX_TEXT_LENGTH} символов.\n"
            f"Ваше: {len(text)} символов."
        )
        return
    
    # Show typing indicator
    await bot.send_chat_action(chat_id=message.chat.id, action="record_voice")
    
    try:
        # Process the text (assuming Chinese input)
        await process_chinese_message(
            message=message,
            user=user,
            chinese_text=text,
            is_voice=False
        )
        
        # Increment text counter
        usage_repo = DailyUsageRepository()
        await usage_repo.increment_text(user.id)
        
    except Exception as e:
        logger.error(f"Text processing error: {e}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка при обработке сообщения.\n"
            "Пожалуйста, попробуйте ещё раз."
        )


async def process_chinese_message(
    message: Message,
    user: User,
    chinese_text: str,
    is_voice: bool
) -> None:
    """
    Process Chinese text and send AI response.
    
    Args:
        message: Original Telegram message
        user: User model
        chinese_text: Chinese text to process
        is_voice: Whether the original message was voice
    """
    msg_repo = MessageRepository()
    
    # Get conversation history
    history = await msg_repo.get_history(user.id, limit=10, topic=user.current_topic)
    
    # Convert to OpenAI format
    history_for_ai = [
        {"role": msg.role, "content": msg.content}
        for msg in history
    ]
    
    # 3. Generate AI response
    ai_result = await generate_response(
        user_message=chinese_text,
        history=history_for_ai,
        topic=user.current_topic,
        hsk_level=user.hsk_level
    )
    
    # 4. Save user message to DB
    user_msg_id = await msg_repo.create(
        user_id=user.id,
        role="user",
        content=chinese_text,
        correction=ai_result.get("correction"),
        topic=user.current_topic
    )
    
    # 5. If there's a correction, show it first
    if ai_result.get("correction"):
        correction = ai_result["correction"]
        await message.answer(
            f"✏️ <b>Исправление:</b>\n\n"
            f"<s>{correction.get('original', chinese_text)}</s>\n\n"
            f"✅ <b>{correction.get('corrected', '')}</b>",
            parse_mode="HTML"
        )
    
    # 6. Synthesize response audio
    response_text = ai_result.get("response", "对不起，我不明白。")
    audio_bytes = await synthesize(response_text, speed=user.speech_speed)
    
    # 7. Save assistant message to DB
    assistant_msg_id = await msg_repo.create(
        user_id=user.id,
        role="assistant",
        content=response_text,
        pinyin=ai_result.get("pinyin", ""),
        translation=ai_result.get("translation", ""),
        topic=user.current_topic
    )
    
    # 8. Send voice message with inline keyboard (ONLY voice, no auto-text)
    voice_file = BufferedInputFile(audio_bytes, filename="response.opus")
    
    has_correction = ai_result.get("correction") is not None
    keyboard = get_message_keyboard(assistant_msg_id, has_correction=has_correction)
    
    await message.answer_voice(
        voice=voice_file,
        reply_markup=keyboard
    )
