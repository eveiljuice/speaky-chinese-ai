"""Tests for one-time gift link premium grants."""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("BOT_TOKEN", "test:token")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("ADMIN_IDS", "1")


@pytest.fixture(autouse=True)
def _patch_db(tmp_path, monkeypatch):
    """Use a temporary SQLite database for every test."""
    db_file = tmp_path / "test_bot.db"
    monkeypatch.setattr("bot.config.settings.DB_PATH", str(db_file))
    import bot.database.database as db_mod
    monkeypatch.setattr(db_mod, "DB_PATH", db_file)


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


async def _init():
    from bot.database.database import init_db
    await init_db()


@pytest.mark.asyncio
async def test_gift_link_create_and_redeem():
    from bot.database.repositories import GiftLinkRepository, UserRepository, PaymentRepository

    await _init()
    user_repo = UserRepository()
    admin = await user_repo.create(1, "admin", "Admin")
    user = await user_repo.create(2, "user", "User")

    gift_repo = GiftLinkRepository()
    gift = await gift_repo.create(created_by=admin.id, days=30)

    status, redeemed = await gift_repo.redeem(gift.token, user.id)
    assert status == "ok"
    assert redeemed is not None
    assert redeemed.used_by == user.id

    new_until = await user_repo.add_premium_days(user.id, gift.days_granted)
    assert new_until > datetime.utcnow()

    payment_repo = PaymentRepository()
    payment_id = await payment_repo.create(
        user_id=user.id,
        amount=0,
        days_granted=30,
        source="promo",
    )
    assert payment_id > 0


@pytest.mark.asyncio
async def test_gift_link_one_time_only():
    from bot.database.repositories import GiftLinkRepository, UserRepository

    await _init()
    user_repo = UserRepository()
    admin = await user_repo.create(1, "admin", "Admin")
    user1 = await user_repo.create(2, "user1", "User1")
    user2 = await user_repo.create(3, "user2", "User2")

    gift_repo = GiftLinkRepository()
    gift = await gift_repo.create(created_by=admin.id, days=7)

    status1, _ = await gift_repo.redeem(gift.token, user1.id)
    status2, _ = await gift_repo.redeem(gift.token, user2.id)

    assert status1 == "ok"
    assert status2 == "used"


@pytest.mark.asyncio
async def test_gift_link_expired():
    from bot.database.repositories import GiftLinkRepository, UserRepository

    await _init()
    user_repo = UserRepository()
    admin = await user_repo.create(1, "admin", "Admin")
    user = await user_repo.create(2, "user", "User")

    gift_repo = GiftLinkRepository()
    gift = await gift_repo.create(
        created_by=admin.id,
        days=7,
        expires_at=datetime.utcnow() - timedelta(hours=1),
    )

    status, _ = await gift_repo.redeem(gift.token, user.id)
    assert status == "expired"


@pytest.mark.asyncio
async def test_gift_link_not_found():
    from bot.database.repositories import GiftLinkRepository, UserRepository

    await _init()
    user_repo = UserRepository()
    await user_repo.create(2, "user", "User")

    gift_repo = GiftLinkRepository()
    status, gift = await gift_repo.redeem("nonexistent", 2)

    assert status == "not_found"
    assert gift is None
