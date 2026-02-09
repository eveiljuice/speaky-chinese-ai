"""Database repository classes for CRUD operations."""

import json
import secrets
from datetime import datetime, timedelta, date
from typing import Optional

import aiosqlite

from .database import get_db
from .models import User, Message, DailyUsage, Referral, Payment


class UserRepository:
    """Repository for user operations."""

    @staticmethod
    def _generate_referral_code() -> str:
        """Generate unique referral code."""
        return secrets.token_urlsafe(6)  # ~8 chars

    async def get(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        async with get_db() as db:
            async with db.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return User.from_row(dict(row))
        return None

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        async with get_db() as db:
            async with db.execute(
                "SELECT * FROM users WHERE LOWER(username) = LOWER(?)",
                (username,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return User.from_row(dict(row))
        return None

    async def get_by_referral_code(self, code: str) -> Optional[User]:
        """Get user by referral code."""
        async with get_db() as db:
            async with db.execute(
                "SELECT * FROM users WHERE referral_code = ?", (code,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return User.from_row(dict(row))
        return None

    async def create(
        self,
        user_id: int,
        username: Optional[str],
        first_name: str,
        language_code: str = "ru",
        referrer_id: Optional[int] = None
    ) -> User:
        """Create new user."""
        referral_code = self._generate_referral_code()

        async with get_db() as db:
            await db.execute(
                """INSERT INTO users 
                   (id, username, first_name, language_code, referrer_id, referral_code)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, username, first_name,
                 language_code, referrer_id, referral_code)
            )
            await db.commit()

        return await self.get(user_id)

    async def update(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user fields."""
        if not kwargs:
            return await self.get(user_id)

        fields = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [user_id]

        async with get_db() as db:
            await db.execute(
                f"UPDATE users SET {fields} WHERE id = ?",
                values
            )
            await db.commit()

        return await self.get(user_id)

    async def update_last_active(self, user_id: int) -> None:
        """Update user's last active timestamp."""
        async with get_db() as db:
            await db.execute(
                "UPDATE users SET last_active_at = CURRENT_TIMESTAMP WHERE id = ?",
                (user_id,)
            )
            await db.commit()

    async def get_expired_trial_users(self) -> list[User]:
        """Get users whose trial has expired but haven't been notified yet."""
        from bot.config import settings as cfg
        cutoff = (datetime.utcnow() - timedelta(days=cfg.TRIAL_DAYS)).isoformat()

        async with get_db() as db:
            async with db.execute(
                """SELECT * FROM users 
                   WHERE trial_notified = 0
                   AND (premium_until IS NULL OR premium_until <= ?)
                   AND created_at <= ?
                   AND NOT is_blocked""",
                (datetime.utcnow().isoformat(), cutoff)
            ) as cursor:
                rows = await cursor.fetchall()
                return [User.from_row(dict(row)) for row in rows]

    async def get_expired_premium_users(self) -> list[User]:
        """Get users whose premium has expired but haven't been notified yet."""
        now = datetime.utcnow().isoformat()
        async with get_db() as db:
            async with db.execute(
                """SELECT * FROM users 
                   WHERE premium_expired_notified = 0
                   AND premium_until IS NOT NULL
                   AND premium_until <= ?
                   AND NOT is_blocked""",
                (now,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [User.from_row(dict(row)) for row in rows]

    async def mark_trial_notified(self, user_id: int) -> None:
        """Mark user as notified about trial expiry."""
        async with get_db() as db:
            await db.execute(
                "UPDATE users SET trial_notified = 1 WHERE id = ?",
                (user_id,)
            )
            await db.commit()

    async def mark_premium_expired_notified(self, user_id: int) -> None:
        """Mark user as notified about premium expiry."""
        async with get_db() as db:
            await db.execute(
                "UPDATE users SET premium_expired_notified = 1 WHERE id = ?",
                (user_id,)
            )
            await db.commit()

    async def reset_premium_expired_notified(self, user_id: int) -> None:
        """Reset premium expiry notification flag (when premium is re-activated)."""
        async with get_db() as db:
            await db.execute(
                "UPDATE users SET premium_expired_notified = 0 WHERE id = ?",
                (user_id,)
            )
            await db.commit()

    async def add_premium_days(self, user_id: int, days: int) -> datetime:
        """Add premium days to user. Also resets premium_expired_notified flag."""
        async with get_db() as db:
            async with db.execute(
                "SELECT premium_until FROM users WHERE id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()

            now = datetime.utcnow()
            current = None
            if row and row[0]:
                try:
                    current = datetime.fromisoformat(row[0])
                except (ValueError, TypeError):
                    pass

            base = max(current, now) if current else now
            new_until = base + timedelta(days=days)

            await db.execute(
                "UPDATE users SET premium_until = ?, premium_expired_notified = 0 WHERE id = ?",
                (new_until.isoformat(), user_id)
            )
            await db.commit()

            return new_until

    async def remove_premium(self, user_id: int) -> None:
        """Remove premium from user."""
        async with get_db() as db:
            await db.execute(
                "UPDATE users SET premium_until = NULL WHERE id = ?",
                (user_id,)
            )
            await db.commit()

    async def block(self, user_id: int) -> None:
        """Block user."""
        async with get_db() as db:
            await db.execute(
                "UPDATE users SET is_blocked = 1 WHERE id = ?",
                (user_id,)
            )
            await db.commit()

    async def unblock(self, user_id: int) -> None:
        """Unblock user."""
        async with get_db() as db:
            await db.execute(
                "UPDATE users SET is_blocked = 0 WHERE id = ?",
                (user_id,)
            )
            await db.commit()


class MessageRepository:
    """Repository for message operations."""

    async def create(
        self,
        user_id: int,
        role: str,
        content: str,
        original_text: Optional[str] = None,
        correction: Optional[dict] = None,
        pinyin: Optional[str] = None,
        translation: Optional[str] = None,
        topic: Optional[str] = None
    ) -> int:
        """Create new message and return its ID."""
        correction_json = json.dumps(correction) if correction else None

        async with get_db() as db:
            cursor = await db.execute(
                """INSERT INTO messages 
                   (user_id, role, content, original_text, correction, pinyin, translation, topic)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, role, content, original_text,
                 correction_json, pinyin, translation, topic)
            )
            await db.commit()
            return cursor.lastrowid

    async def get(self, message_id: int) -> Optional[Message]:
        """Get message by ID."""
        async with get_db() as db:
            async with db.execute(
                "SELECT * FROM messages WHERE id = ?", (message_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Message.from_row(dict(row))
        return None

    async def get_history(
        self,
        user_id: int,
        limit: int = 10,
        topic: Optional[str] = None
    ) -> list[Message]:
        """Get user's message history."""
        async with get_db() as db:
            if topic:
                query = """SELECT * FROM messages 
                          WHERE user_id = ? AND topic = ?
                          ORDER BY created_at DESC LIMIT ?"""
                params = (user_id, topic, limit)
            else:
                query = """SELECT * FROM messages 
                          WHERE user_id = ?
                          ORDER BY created_at DESC LIMIT ?"""
                params = (user_id, limit)

            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                # Return in chronological order
                return [Message.from_row(dict(row)) for row in reversed(rows)]


class DailyUsageRepository:
    """Repository for daily usage tracking."""

    async def get_or_create(self, user_id: int) -> DailyUsage:
        """Get or create today's usage record."""
        today = date.today().isoformat()

        async with get_db() as db:
            async with db.execute(
                "SELECT * FROM daily_usage WHERE user_id = ? AND date = ?",
                (user_id, today)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return DailyUsage.from_row(dict(row))

            # Create new record
            await db.execute(
                "INSERT INTO daily_usage (user_id, date) VALUES (?, ?)",
                (user_id, today)
            )
            await db.commit()

            return DailyUsage(user_id=user_id, date=today)

    async def increment_text(self, user_id: int) -> int:
        """Increment text count and return new value."""
        today = date.today().isoformat()

        async with get_db() as db:
            await db.execute(
                """INSERT INTO daily_usage (user_id, date, text_count) 
                   VALUES (?, ?, 1)
                   ON CONFLICT(user_id, date) 
                   DO UPDATE SET text_count = text_count + 1""",
                (user_id, today)
            )
            await db.commit()

            async with db.execute(
                "SELECT text_count FROM daily_usage WHERE user_id = ? AND date = ?",
                (user_id, today)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def increment_voice(self, user_id: int) -> int:
        """Increment voice count and return new value."""
        today = date.today().isoformat()

        async with get_db() as db:
            await db.execute(
                """INSERT INTO daily_usage (user_id, date, voice_count) 
                   VALUES (?, ?, 1)
                   ON CONFLICT(user_id, date) 
                   DO UPDATE SET voice_count = voice_count + 1""",
                (user_id, today)
            )
            await db.commit()

            async with db.execute(
                "SELECT voice_count FROM daily_usage WHERE user_id = ? AND date = ?",
                (user_id, today)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0


class ReferralRepository:
    """Repository for referral operations."""

    async def create(self, referrer_id: int, referred_id: int) -> bool:
        """Create referral record. Returns True if created, False if already exists."""
        async with get_db() as db:
            try:
                await db.execute(
                    "INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)",
                    (referrer_id, referred_id)
                )
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    async def get_by_referred(self, referred_id: int) -> Optional[Referral]:
        """Get referral by referred user ID."""
        async with get_db() as db:
            async with db.execute(
                "SELECT * FROM referrals WHERE referred_id = ?",
                (referred_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Referral.from_row(dict(row))
        return None

    async def update_status(self, referred_id: int, status: str) -> None:
        """Update referral status."""
        async with get_db() as db:
            await db.execute(
                "UPDATE referrals SET status = ? WHERE referred_id = ?",
                (status, referred_id)
            )
            await db.commit()

    async def count_by_referrer(self, referrer_id: int) -> tuple[int, int]:
        """Count referrals by referrer. Returns (total, subscribed)."""
        async with get_db() as db:
            async with db.execute(
                "SELECT COUNT(*) FROM referrals WHERE referrer_id = ?",
                (referrer_id,)
            ) as cursor:
                total = (await cursor.fetchone())[0]

            async with db.execute(
                "SELECT COUNT(*) FROM referrals WHERE referrer_id = ? AND status = 'subscribed'",
                (referrer_id,)
            ) as cursor:
                subscribed = (await cursor.fetchone())[0]

            return total, subscribed


class AdminRepository:
    """Repository for admin operations."""

    async def get_stats(self) -> dict:
        """Get bot statistics."""
        from datetime import date, timedelta

        today = date.today().isoformat()
        week_ago = (date.today() - timedelta(days=7)).isoformat()
        month_ago = (date.today() - timedelta(days=30)).isoformat()

        async with get_db() as db:
            # Total users
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                total_users = (await cursor.fetchone())[0]

            # New users today
            async with db.execute(
                "SELECT COUNT(*) FROM users WHERE DATE(created_at) = ?", (today,)
            ) as cursor:
                new_today = (await cursor.fetchone())[0]

            # New users this week
            async with db.execute(
                "SELECT COUNT(*) FROM users WHERE DATE(created_at) >= ?", (week_ago,)
            ) as cursor:
                new_week = (await cursor.fetchone())[0]

            # New users this month
            async with db.execute(
                "SELECT COUNT(*) FROM users WHERE DATE(created_at) >= ?", (month_ago,)
            ) as cursor:
                new_month = (await cursor.fetchone())[0]

            # Active premium users
            async with db.execute(
                "SELECT COUNT(*) FROM users WHERE premium_until > CURRENT_TIMESTAMP"
            ) as cursor:
                premium_users = (await cursor.fetchone())[0]

            # Messages today
            async with db.execute(
                "SELECT COUNT(*) FROM messages WHERE DATE(created_at) = ?", (today,)
            ) as cursor:
                messages_today = (await cursor.fetchone())[0]

            # Voice messages today
            async with db.execute(
                "SELECT COALESCE(SUM(voice_count), 0) FROM daily_usage WHERE date = ?",
                (today,)
            ) as cursor:
                voice_today = (await cursor.fetchone())[0]

            # Text messages today
            async with db.execute(
                "SELECT COALESCE(SUM(text_count), 0) FROM daily_usage WHERE date = ?",
                (today,)
            ) as cursor:
                text_today = (await cursor.fetchone())[0]

            # DAU (distinct users active today)
            async with db.execute(
                "SELECT COUNT(DISTINCT user_id) FROM daily_usage WHERE date = ?",
                (today,)
            ) as cursor:
                dau = (await cursor.fetchone())[0]

            # WAU
            async with db.execute(
                "SELECT COUNT(DISTINCT user_id) FROM daily_usage WHERE date >= ?",
                (week_ago,)
            ) as cursor:
                wau = (await cursor.fetchone())[0]

            # MAU
            async with db.execute(
                "SELECT COUNT(DISTINCT user_id) FROM daily_usage WHERE date >= ?",
                (month_ago,)
            ) as cursor:
                mau = (await cursor.fetchone())[0]

            # Total revenue (last 30 days)
            async with db.execute(
                """SELECT COALESCE(SUM(amount), 0) FROM payments 
                   WHERE created_at >= ? AND status = 'completed' AND source = 'payment'""",
                (month_ago,)
            ) as cursor:
                revenue = (await cursor.fetchone())[0]

            return {
                "total_users": total_users,
                "new_today": new_today,
                "new_week": new_week,
                "new_month": new_month,
                "premium_users": premium_users,
                "messages_today": messages_today,
                "voice_today": voice_today,
                "text_today": text_today,
                "dau": dau,
                "wau": wau,
                "mau": mau,
                "revenue": revenue,
                "conversion": round(premium_users / total_users * 100, 1) if total_users > 0 else 0
            }

    async def get_users_list(
        self,
        limit: int = 10,
        offset: int = 0,
        premium_only: bool = False
    ) -> tuple[list[User], int]:
        """Get paginated list of users."""
        async with get_db() as db:
            if premium_only:
                count_query = "SELECT COUNT(*) FROM users WHERE premium_until > CURRENT_TIMESTAMP"
                query = """SELECT * FROM users WHERE premium_until > CURRENT_TIMESTAMP
                          ORDER BY created_at DESC LIMIT ? OFFSET ?"""
            else:
                count_query = "SELECT COUNT(*) FROM users"
                query = "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?"

            async with db.execute(count_query) as cursor:
                total = (await cursor.fetchone())[0]

            async with db.execute(query, (limit, offset)) as cursor:
                rows = await cursor.fetchall()
                users = [User.from_row(dict(row)) for row in rows]

            return users, total

    async def search_user(self, query: str) -> Optional[User]:
        """Search user by ID or username."""
        async with get_db() as db:
            # Try by ID first
            try:
                user_id = int(query)
                async with db.execute(
                    "SELECT * FROM users WHERE id = ?", (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return User.from_row(dict(row))
            except ValueError:
                pass

            # Try by username
            username = query.lstrip("@")
            async with db.execute(
                "SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return User.from_row(dict(row))

        return None

    async def get_user_details(self, user_id: int) -> dict:
        """Get detailed user info for admin card."""
        async with get_db() as db:
            # User basic info
            async with db.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                user = User.from_row(dict(row))

            # Message count
            async with db.execute(
                "SELECT COUNT(*) FROM messages WHERE user_id = ?", (user_id,)
            ) as cursor:
                msg_count = (await cursor.fetchone())[0]

            # Saved words count
            async with db.execute(
                "SELECT COUNT(*) FROM saved_words WHERE user_id = ?", (user_id,)
            ) as cursor:
                words_count = (await cursor.fetchone())[0]

            # Payment count
            async with db.execute(
                "SELECT COUNT(*) FROM payments WHERE user_id = ? AND source = 'payment'",
                (user_id,)
            ) as cursor:
                payment_count = (await cursor.fetchone())[0]

            # Referrer info
            referrer = None
            if user.referrer_id:
                async with db.execute(
                    "SELECT username FROM users WHERE id = ?", (
                        user.referrer_id,)
                ) as cursor:
                    ref_row = await cursor.fetchone()
                    if ref_row:
                        referrer = ref_row[0]

            # Referrals count
            async with db.execute(
                "SELECT COUNT(*) FROM referrals WHERE referrer_id = ?", (user_id,)
            ) as cursor:
                referrals_count = (await cursor.fetchone())[0]

            return {
                "user": user,
                "msg_count": msg_count,
                "words_count": words_count,
                "payment_count": payment_count,
                "referrer": referrer,
                "referrals_count": referrals_count
            }

    async def get_broadcast_audience(self, audience: str) -> list[int]:
        """Get user IDs for broadcast."""
        async with get_db() as db:
            if audience == "premium":
                query = """SELECT id FROM users 
                          WHERE premium_until > CURRENT_TIMESTAMP AND NOT is_blocked"""
            elif audience == "free":
                query = """SELECT id FROM users 
                          WHERE (premium_until IS NULL OR premium_until <= CURRENT_TIMESTAMP) 
                          AND NOT is_blocked"""
            else:  # all
                query = "SELECT id FROM users WHERE NOT is_blocked"

            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]


class PaymentRepository:
    """Repository for payment operations."""

    async def create(
        self,
        user_id: int,
        amount: int,
        days_granted: int,
        source: str = "payment",
        telegram_payment_id: Optional[str] = None,
        provider_payment_id: Optional[str] = None,
        currency: str = "RUB",
        status: str = "completed"
    ) -> int:
        """Create payment record and return ID."""
        async with get_db() as db:
            cursor = await db.execute(
                """INSERT INTO payments 
                   (user_id, amount, currency, telegram_payment_id, provider_payment_id, 
                    status, days_granted, source)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, amount, currency, telegram_payment_id, provider_payment_id,
                 status, days_granted, source)
            )
            await db.commit()
            return cursor.lastrowid

    async def get_user_payments(self, user_id: int) -> list[Payment]:
        """Get user's payment history."""
        async with get_db() as db:
            async with db.execute(
                "SELECT * FROM payments WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [Payment.from_row(dict(row)) for row in rows]

    async def get_total_revenue(self, days: int = 30) -> int:
        """Get total revenue in last N days (in kopecks)."""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        async with get_db() as db:
            async with db.execute(
                """SELECT COALESCE(SUM(amount), 0) FROM payments 
                   WHERE created_at > ? AND status = 'completed' AND source = 'payment'""",
                (cutoff,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
