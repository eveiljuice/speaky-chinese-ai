"""Database models as dataclasses."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import json


@dataclass
class User:
    """User model."""
    id: int  # Telegram user ID
    username: Optional[str] = None
    first_name: str = ""
    language_code: str = "ru"
    
    # Learning settings
    hsk_level: int = 1
    speech_speed: str = "normal"  # slow, normal, fast
    current_topic: str = "daily"
    
    # Subscription
    premium_until: Optional[datetime] = None
    
    # Referral
    referrer_id: Optional[int] = None
    referral_code: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active_at: datetime = field(default_factory=datetime.utcnow)
    is_blocked: bool = False
    
    @classmethod
    def from_row(cls, row: dict) -> "User":
        """Create User from database row."""
        return cls(
            id=row["id"],
            username=row.get("username"),
            first_name=row.get("first_name", ""),
            language_code=row.get("language_code", "ru"),
            hsk_level=row.get("hsk_level", 1),
            speech_speed=row.get("speech_speed", "normal"),
            current_topic=row.get("current_topic", "daily"),
            premium_until=_parse_datetime(row.get("premium_until")),
            referrer_id=row.get("referrer_id"),
            referral_code=row.get("referral_code"),
            created_at=_parse_datetime(row.get("created_at")) or datetime.utcnow(),
            last_active_at=_parse_datetime(row.get("last_active_at")) or datetime.utcnow(),
            is_blocked=bool(row.get("is_blocked", 0)),
        )


@dataclass
class Message:
    """Message model."""
    id: Optional[int] = None
    user_id: int = 0
    role: str = "user"  # user or assistant
    content: str = ""
    
    # For user messages
    original_text: Optional[str] = None
    correction: Optional[dict] = None  # JSON: {original, corrected, explanation}
    
    # For assistant messages
    pinyin: Optional[str] = None
    translation: Optional[str] = None
    
    topic: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def from_row(cls, row: dict) -> "Message":
        """Create Message from database row."""
        correction = row.get("correction")
        if correction and isinstance(correction, str):
            try:
                correction = json.loads(correction)
            except json.JSONDecodeError:
                correction = None
        
        return cls(
            id=row.get("id"),
            user_id=row.get("user_id", 0),
            role=row.get("role", "user"),
            content=row.get("content", ""),
            original_text=row.get("original_text"),
            correction=correction,
            pinyin=row.get("pinyin"),
            translation=row.get("translation"),
            topic=row.get("topic"),
            created_at=_parse_datetime(row.get("created_at")) or datetime.utcnow(),
        )


@dataclass
class DailyUsage:
    """Daily usage tracking model."""
    id: Optional[int] = None
    user_id: int = 0
    date: str = ""  # YYYY-MM-DD
    text_count: int = 0
    voice_count: int = 0
    
    @classmethod
    def from_row(cls, row: dict) -> "DailyUsage":
        """Create DailyUsage from database row."""
        return cls(
            id=row.get("id"),
            user_id=row.get("user_id", 0),
            date=row.get("date", ""),
            text_count=row.get("text_count", 0),
            voice_count=row.get("voice_count", 0),
        )


@dataclass
class Referral:
    """Referral model."""
    id: Optional[int] = None
    referrer_id: int = 0
    referred_id: int = 0
    status: str = "registered"  # registered or subscribed
    bonus_days_given: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def from_row(cls, row: dict) -> "Referral":
        """Create Referral from database row."""
        return cls(
            id=row.get("id"),
            referrer_id=row.get("referrer_id", 0),
            referred_id=row.get("referred_id", 0),
            status=row.get("status", "registered"),
            bonus_days_given=row.get("bonus_days_given", 0),
            created_at=_parse_datetime(row.get("created_at")) or datetime.utcnow(),
        )


@dataclass
class Payment:
    """Payment model."""
    id: Optional[int] = None
    user_id: int = 0
    amount: int = 0  # In kopecks
    currency: str = "RUB"
    
    telegram_payment_id: Optional[str] = None
    provider_payment_id: Optional[str] = None
    
    status: str = "completed"  # pending, completed, failed, refunded
    days_granted: int = 0
    source: str = "payment"  # payment, referral, admin, promo
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def from_row(cls, row: dict) -> "Payment":
        """Create Payment from database row."""
        return cls(
            id=row.get("id"),
            user_id=row.get("user_id", 0),
            amount=row.get("amount", 0),
            currency=row.get("currency", "RUB"),
            telegram_payment_id=row.get("telegram_payment_id"),
            provider_payment_id=row.get("provider_payment_id"),
            status=row.get("status", "completed"),
            days_granted=row.get("days_granted", 0),
            source=row.get("source", "payment"),
            created_at=_parse_datetime(row.get("created_at")) or datetime.utcnow(),
        )


def _parse_datetime(value) -> Optional[datetime]:
    """Parse datetime from various formats."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            # Try ISO format
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            try:
                # Try SQLite format
                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None
    return None
