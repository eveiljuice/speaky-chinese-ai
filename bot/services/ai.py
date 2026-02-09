"""AI services - OpenAI integration for STT, LLM, and TTS."""

import json
import logging
from typing import Optional

from openai import AsyncOpenAI

from bot.config import settings

logger = logging.getLogger(__name__)

# OpenAI client - uses OPENAI_API_KEY from env
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# Topic definitions for prompts
TOPICS = {
    "travel": "旅游 (путешествия)",
    "food": "美食 (еда)",
    "work": "工作 (работа)",
    "daily": "日常生活 (быт)",
    "study": "学习 (учёба)",
    "health": "健康 (здоровье)",
    "free": "自由对话 (свободный диалог на любую тему)"
}

# Speed mapping for TTS
SPEED_MAP = {"slow": 0.8, "normal": 1.0, "fast": 1.2}


async def transcribe(audio_bytes: bytes, filename: str = "audio.ogg") -> str:
    """
    Transcribe audio to Chinese text using Whisper.

    Args:
        audio_bytes: Audio data in bytes
        filename: Name hint for the file (default: audio.ogg)

    Returns:
        Transcribed text in Chinese
    """
    logger.debug(f"Transcribing audio, size: {len(audio_bytes)} bytes")

    transcript = await client.audio.transcriptions.create(
        model="whisper-1",
        file=(filename, audio_bytes, "audio/ogg"),
        language="zh"  # Chinese
    )

    logger.debug(f"Transcription result: {transcript.text[:100]}...")
    return transcript.text


async def generate_response(
    user_message: str,
    history: list[dict],
    topic: str,
    hsk_level: int
) -> dict:
    """
    Generate bot response with corrections using GPT-4o-mini.

    Args:
        user_message: User's message in Chinese
        history: Conversation history (list of {"role": "user"|"assistant", "content": str})
        topic: Current dialogue topic
        hsk_level: User's HSK level (1-3)

    Returns:
        dict with keys:
        - correction: dict with original, corrected, corrected_pinyin, explanation (or None)
        - response: Bot's response in Chinese
        - pinyin: Pinyin transcription
        - translation: Russian translation
        - suggestions: List of dicts with "text" (Chinese) and "pinyin" keys
    """
    topic_name = TOPICS.get(topic, TOPICS["daily"])

    system_prompt = f"""你是一个中文老师，帮助学生练习汉语口语。

当前话题: {topic_name}
学生水平: HSK {hsk_level}

规则:
1. 只用HSK{hsk_level}词汇回复（可加10-15%新词）
2. 保持对话自然，围绕话题
3. 如果学生有语法/词汇错误，先纠正再回复
4. 回复简短（1-3句话）

回复格式（JSON）:
{{
    "correction": {{"original": "错误文本", "corrected": "正确文本", "corrected_pinyin": "正确文本的拼音", "explanation": "解释（俄语）"}} 或 null,
    "response": "你的回复（中文）",
    "pinyin": "拼音",
    "translation": "перевод на русский",
    "suggestions": [
        {{"text": "中文回复", "pinyin": "拼音"}},
        {{"text": "中文回复2", "pinyin": "拼音2"}}
    ]
}}"""

    # Build messages list
    messages = [
        {"role": "system", "content": system_prompt},
        *history[-10:],  # Last 10 messages for context
        {"role": "user", "content": user_message}
    ]

    logger.debug(f"Generating response for: {user_message[:50]}...")

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=500
    )

    content = response.choices[0].message.content
    logger.debug(f"LLM response: {content[:200]}...")

    result = json.loads(content)

    # Ensure all required fields exist
    result.setdefault("correction", None)
    result.setdefault("response", "对不起，我不明白。")
    result.setdefault("pinyin", "")
    result.setdefault("translation", "")
    result.setdefault("suggestions", [])

    return result


async def synthesize(text: str, speed: str = "normal") -> bytes:
    """
    Synthesize speech from Chinese text using OpenAI TTS.

    Args:
        text: Text to synthesize (Chinese)
        speed: Speech speed - "slow", "normal", or "fast"

    Returns:
        Audio data in opus format (bytes)
    """
    tts_speed = SPEED_MAP.get(speed, 1.0)

    logger.debug(f"Synthesizing: {text[:50]}... (speed: {speed})")

    response = await client.audio.speech.create(
        model="tts-1",
        voice="nova",  # Good for Chinese
        input=text,
        speed=tts_speed,
        response_format="opus"  # Telegram voice messages
    )

    audio_bytes = response.content
    logger.debug(f"Synthesized audio size: {len(audio_bytes)} bytes")

    return audio_bytes


async def get_word_info(hanzi: str, context: Optional[str] = None) -> dict:
    """
    Get pinyin and translation for a Chinese word/phrase.

    Args:
        hanzi: Chinese characters
        context: Optional context where the word was used

    Returns:
        dict with pinyin and translation
    """
    prompt = f"""Дай пиньинь и перевод для:
汉字: {hanzi}
{"Контекст: " + context if context else ""}

Ответь JSON:
{{"pinyin": "пиньинь", "translation": "перевод на русский"}}"""

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=100
    )

    return json.loads(response.choices[0].message.content)


async def explain_correction(
    original: str,
    corrected: str,
    hsk_level: int
) -> str:
    """
    Generate detailed explanation for a correction.

    Args:
        original: Original (incorrect) text
        corrected: Corrected text
        hsk_level: User's HSK level

    Returns:
        Detailed explanation in Russian
    """
    prompt = f"""Объясни ошибку подробно для студента уровня HSK {hsk_level}:

Неправильно: {original}
Правильно: {corrected}

Дай понятное объяснение на русском:
1. Какая ошибка была допущена
2. Почему правильный вариант лучше
3. Как запомнить правило"""

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=300
    )

    return response.choices[0].message.content
