"""Referral program handler."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.database.models import User
from bot.database.repositories import ReferralRepository, PaymentRepository

router = Router()


@router.message(Command("invite"))
async def cmd_invite(message: Message, user: User):
    """Handle /invite command - show referral info."""
    # Get referral stats
    referral_repo = ReferralRepository()
    total_refs, subscribed_refs = await referral_repo.count_by_referrer(user.id)
    
    # Calculate bonus days earned
    # +7 days for each registration, +30 days for each subscription
    registration_bonus = total_refs * 7
    subscription_bonus = subscribed_refs * 30
    total_bonus = registration_bonus + subscription_bonus
    
    referral_link = f"https://t.me/{(await message.bot.me()).username}?start=ref_{user.referral_code}"
    
    await message.answer(
        f"👥 <b>Реферальная программа</b>\n\n"
        f"Ваша ссылка:\n"
        f"<code>{referral_link}</code>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• Приглашено друзей: <b>{total_refs}</b>\n"
        f"• Из них оплатили: <b>{subscribed_refs}</b>\n"
        f"• Заработано дней: <b>{total_bonus}</b>\n\n"
        f"💡 <b>Бонусы:</b>\n"
        f"• Друг регистрируется → вы оба получаете <b>+7 дней Premium</b>\n"
        f"• Друг покупает Premium → вы получаете <b>+30 дней</b>",
        parse_mode="HTML"
    )
