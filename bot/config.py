"""Bot configuration using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Telegram
    BOT_TOKEN: str

    # OpenAI
    OPENAI_API_KEY: str

    # Payments (stub for now)
    PAYMENT_PROVIDER_TOKEN: str = ""
    
    # Tribute Payment
    TRIBUTE_API_KEY: str = ""
    TRIBUTE_PRODUCT_ID: str = ""  # Product ID from Tribute (can be string like 'pq5z')
    TRIBUTE_PAYMENT_LINK: str = ""  # Payment link from Tribute
    WEBHOOK_URL: str = ""  # Your webhook URL (e.g., https://yourdomain.com/webhook/tribute)
    WEBHOOK_PORT: int = 8080  # Port for webhook server
    
    # Admin IDs (comma-separated string -> list)
    ADMIN_IDS: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"

    # Database
    DB_PATH: str = "bot.db"

    # Limits
    MAX_TEXT_LENGTH: int = 500
    MAX_VOICE_DURATION: int = 60  # seconds

    # Free tier limits
    FREE_TEXT_LIMIT: int = 20
    FREE_VOICE_LIMIT: int = 5
    FREE_VOCAB_LIMIT: int = 50

    # Trial duration
    TRIAL_DAYS: int = 3

    # Premium price in kopecks (770 RUB)
    PREMIUM_PRICE: int = 77000

    @property
    def admin_ids(self) -> list[int]:
        """Parse admin IDs from comma-separated string."""
        if not self.ADMIN_IDS:
            return []
        return [int(id_.strip()) for id_ in self.ADMIN_IDS.split(",") if id_.strip()]

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        return user_id in self.admin_ids


# Global settings instance
settings = Settings()
