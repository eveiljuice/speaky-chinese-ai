"""Database connection and initialization."""

import logging
import aiosqlite
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from bot.config import settings

logger = logging.getLogger(__name__)

DB_PATH = Path(settings.DB_PATH)

# Ensure parent directory exists (critical for Railway Volumes where DB_PATH=/data/bot.db)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Database schema
SCHEMA = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,                           -- Telegram user ID
    username TEXT,                                    -- @username (может быть NULL)
    first_name TEXT NOT NULL,                         -- Имя из Telegram
    language_code TEXT DEFAULT 'ru',                  -- Язык интерфейса
    
    -- Настройки обучения
    hsk_level INTEGER DEFAULT 1 CHECK (hsk_level BETWEEN 1 AND 3),
    speech_speed TEXT DEFAULT 'normal' CHECK (speech_speed IN ('slow', 'normal', 'fast')),
    current_topic TEXT DEFAULT 'daily',               -- Текущая тема диалога
    
    -- Подписка
    premium_until TIMESTAMP,                          -- NULL = нет Premium
    
    -- Реферальная программа
    referrer_id INTEGER REFERENCES users(id),         -- Кто пригласил
    referral_code TEXT UNIQUE,                        -- Уникальный код для ссылки
    
    -- Метаданные
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_blocked INTEGER DEFAULT 0                      -- Заблокирован ли
);

CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code);
CREATE INDEX IF NOT EXISTS idx_users_referrer_id ON users(referrer_id);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,                            -- Текст сообщения
    
    -- Для сообщений пользователя
    original_text TEXT,                               -- Исходный текст (до исправления)
    correction TEXT,                                  -- JSON: {"original": "...", "corrected": "...", "explanation": "..."}
    
    -- Для ответов бота
    pinyin TEXT,                                      -- Пиньинь ответа
    translation TEXT,                                 -- Перевод на русский
    
    topic TEXT,                                       -- Тема диалога
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- Saved words table
CREATE TABLE IF NOT EXISTS saved_words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    hanzi TEXT NOT NULL,                              -- 你好
    pinyin TEXT NOT NULL,                             -- nǐ hǎo
    translation TEXT NOT NULL,                        -- привет
    context TEXT,                                     -- Предложение, где встретилось
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, hanzi)                            -- Одно слово один раз
);

CREATE INDEX IF NOT EXISTS idx_saved_words_user_id ON saved_words(user_id);

-- Daily usage table
CREATE TABLE IF NOT EXISTS daily_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date TEXT NOT NULL,                               -- YYYY-MM-DD
    
    text_count INTEGER DEFAULT 0,                     -- Текстовых сообщений
    voice_count INTEGER DEFAULT 0,                    -- Голосовых сообщений
    
    UNIQUE(user_id, date)
);

CREATE INDEX IF NOT EXISTS idx_daily_usage_user_date ON daily_usage(user_id, date);

-- Referrals table
CREATE TABLE IF NOT EXISTS referrals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER NOT NULL REFERENCES users(id),  -- Кто пригласил
    referred_id INTEGER NOT NULL REFERENCES users(id),  -- Кого пригласил
    
    status TEXT DEFAULT 'registered' CHECK (status IN ('registered', 'subscribed')),
    bonus_days_given INTEGER DEFAULT 0,                 -- Сколько дней уже начислено
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(referred_id)                                 -- Каждый может быть приглашён только раз
);

CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id ON referrals(referrer_id);

-- Payments table
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    amount INTEGER NOT NULL,                            -- Сумма в копейках (77000 = ₽770)
    currency TEXT DEFAULT 'RUB',
    
    telegram_payment_id TEXT,                           -- ID платежа от Telegram
    provider_payment_id TEXT,                           -- ID от платёжной системы
    
    status TEXT DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    
    days_granted INTEGER NOT NULL,                      -- Сколько дней Premium выдано
    source TEXT DEFAULT 'payment' CHECK (source IN ('payment', 'referral', 'admin', 'promo')),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_created_at ON payments(created_at);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
"""


# Migrations: add new columns safely (idempotent ALTER TABLE)
MIGRATIONS = [
    # Migration 1: Add notification tracking columns for trial/premium expiry
    "ALTER TABLE users ADD COLUMN trial_notified INTEGER DEFAULT 0",
    "ALTER TABLE users ADD COLUMN premium_expired_notified INTEGER DEFAULT 0",
]


async def init_db() -> None:
    """Initialize database with schema and run migrations."""
    logger.info(f"Database path: {DB_PATH} (exists: {DB_PATH.exists()})")

    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()

        # Run migrations (safe: ignores "duplicate column" errors)
        for i, migration in enumerate(MIGRATIONS, 1):
            try:
                await db.execute(migration)
                await db.commit()
                logger.info(f"Migration {i} applied: {migration[:60]}...")
            except Exception as e:
                if "duplicate column" in str(e).lower():
                    pass  # Column already exists — expected on subsequent runs
                else:
                    logger.warning(f"Migration {i} skipped: {e}")

    logger.info("Database initialized successfully.")


@asynccontextmanager
async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Get database connection as async context manager."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()
