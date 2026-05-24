"""Admin panel handler."""

import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.config import settings
from bot.database.models import User
from bot.database.repositories import AdminRepository, UserRepository, GiftLinkRepository
from bot.keyboards.inline import (
    get_admin_main_keyboard,
    get_admin_user_keyboard,
    get_admin_premium_days_keyboard,
    get_admin_broadcast_keyboard,
    get_admin_users_keyboard,
    get_admin_gift_days_keyboard,
    get_admin_gift_result_keyboard,
)
from bot.middlewares.subscription import get_subscription_status, SubscriptionType

router = Router()
logger = logging.getLogger(__name__)

USERS_PER_PAGE = 10


class AdminStates(StatesGroup):
    """Admin FSM states."""
    waiting_search = State()
    waiting_broadcast_text = State()
    waiting_user_message = State()


def admin_only(func):
    """Decorator to check admin access."""
    async def wrapper(event, *args, **kwargs):
        user_id = event.from_user.id if hasattr(event, 'from_user') else None
        if not user_id or not settings.is_admin(user_id):
            if isinstance(event, Message):
                await event.answer("⛔ Доступ запрещён")
            elif isinstance(event, CallbackQuery):
                await event.answer("⛔ Доступ запрещён", show_alert=True)
            return
        return await func(event, *args, **kwargs)
    return wrapper


@router.message(Command("admin"))
async def cmd_admin(message: Message, user: User):
    """Handle /admin command."""
    if not settings.is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён")
        return

    admin_repo = AdminRepository()
    stats = await admin_repo.get_stats()

    await message.answer(
        f"🔐 <b>Админ-панель</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"• Premium активных: <b>{stats['premium_users']}</b>\n"
        f"• За сегодня новых: <b>{stats['new_today']}</b>\n"
        f"• За сегодня сообщений: <b>{stats['messages_today']}</b>",
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML"
    )


# Admin callback handlers
@router.callback_query(F.data == "admin:back")
async def callback_admin_back(callback: CallbackQuery, state: FSMContext):
    """Return to admin main menu."""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    await state.clear()

    admin_repo = AdminRepository()
    stats = await admin_repo.get_stats()

    await callback.answer()
    await callback.message.edit_text(
        f"🔐 <b>Админ-панель</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"• Premium активных: <b>{stats['premium_users']}</b>\n"
        f"• За сегодня новых: <b>{stats['new_today']}</b>\n"
        f"• За сегодня сообщений: <b>{stats['messages_today']}</b>",
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin:stats")
async def callback_admin_stats(callback: CallbackQuery):
    """Show detailed statistics."""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    admin_repo = AdminRepository()
    stats = await admin_repo.get_stats()

    # Calculate MRR (Monthly Recurring Revenue)
    mrr = stats['premium_users'] * (settings.PREMIUM_PRICE // 100)

    await callback.answer()
    await callback.message.edit_text(
        f"📈 <b>Статистика бота</b>\n\n"
        f"👥 <b>Пользователи:</b>\n"
        f"• Всего: <b>{stats['total_users']}</b>\n"
        f"• За сегодня: <b>+{stats['new_today']}</b>\n"
        f"• За неделю: <b>+{stats['new_week']}</b>\n"
        f"• За месяц: <b>+{stats['new_month']}</b>\n\n"
        f"💎 <b>Premium:</b>\n"
        f"• Активных: <b>{stats['premium_users']}</b>\n"
        f"• Конверсия: <b>{stats['conversion']}%</b>\n"
        f"• MRR: <b>₽{mrr:,}</b>\n\n"
        f"💬 <b>Сообщения (сегодня):</b>\n"
        f"• Текстовых: <b>{stats['text_today']}</b>\n"
        f"• Голосовых: <b>{stats['voice_today']}</b>\n"
        f"• Всего: <b>{stats['messages_today']}</b>\n\n"
        f"📊 <b>Активность:</b>\n"
        f"• DAU: <b>{stats['dau']}</b>\n"
        f"• WAU: <b>{stats['wau']}</b>\n"
        f"• MAU: <b>{stats['mau']}</b>",
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin:users:"))
async def callback_admin_users(callback: CallbackQuery):
    """Show users list."""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    parts = callback.data.split(":")
    # admin:users:all or admin:users:premium or admin:users:all:page
    user_type = parts[2]
    page = int(parts[3]) if len(parts) > 3 else 1

    premium_only = user_type == "premium"

    admin_repo = AdminRepository()
    offset = (page - 1) * USERS_PER_PAGE
    users, total = await admin_repo.get_users_list(
        limit=USERS_PER_PAGE,
        offset=offset,
        premium_only=premium_only
    )

    total_pages = max(1, (total + USERS_PER_PAGE - 1) // USERS_PER_PAGE)

    # Format user list
    lines = []
    for i, u in enumerate(users, start=offset + 1):
        status = get_subscription_status(u)
        status_emoji = {
            SubscriptionType.PREMIUM: "💎",
            SubscriptionType.TRIAL: "🎁",
            SubscriptionType.FREE: "🆓"
        }.get(status, "🆓")

        name = f"@{u.username}" if u.username else f"user_{u.id}"
        date_str = u.created_at.strftime("%d.%m.%Y")
        lines.append(f"{i}. {name} — {status_emoji} — {date_str}")

    title = "💎 Premium пользователи" if premium_only else "👥 Пользователи"

    await callback.answer()
    await callback.message.edit_text(
        f"{title} ({total})\n\n" +
        "\n".join(lines) if lines else "Нет пользователей",
        reply_markup=get_admin_users_keyboard(page, total_pages, premium_only),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin:search")
async def callback_admin_search(callback: CallbackQuery, state: FSMContext):
    """Start user search."""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_search)
    await callback.answer()
    await callback.message.edit_text(
        "🔍 <b>Поиск пользователя</b>\n\n"
        "Введите Telegram ID или @username:",
        parse_mode="HTML"
    )


@router.message(AdminStates.waiting_search)
async def process_search(message: Message, state: FSMContext):
    """Process user search query."""
    if not settings.is_admin(message.from_user.id):
        return

    admin_repo = AdminRepository()
    user = await admin_repo.search_user(message.text.strip())

    if not user:
        await message.answer(
            "❌ Пользователь не найден.\n"
            "Попробуйте другой ID или username.",
            reply_markup=get_admin_main_keyboard()
        )
        await state.clear()
        return

    await state.clear()
    await show_user_card(message, user.id)


@router.callback_query(F.data.startswith("admin:user:"))
async def callback_admin_user(callback: CallbackQuery):
    """Show user card."""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    user_id = int(callback.data.split(":")[2])
    await callback.answer()
    await show_user_card(callback.message, user_id, edit=True)


async def show_user_card(message: Message, user_id: int, edit: bool = False):
    """Show detailed user card."""
    admin_repo = AdminRepository()
    details = await admin_repo.get_user_details(user_id)

    if not details:
        text = "❌ Пользователь не найден"
        if edit:
            await message.edit_text(text, reply_markup=get_admin_main_keyboard())
        else:
            await message.answer(text, reply_markup=get_admin_main_keyboard())
        return

    user = details["user"]
    status = get_subscription_status(user)

    status_name = {
        SubscriptionType.PREMIUM: "💎 Premium",
        SubscriptionType.TRIAL: "🎁 Trial",
        SubscriptionType.FREE: "🆓 Free"
    }.get(status, "🆓 Free")

    premium_info = ""
    if status == SubscriptionType.PREMIUM and user.premium_until:
        premium_info = f"\n• Активна до: <b>{user.premium_until.strftime('%d.%m.%Y')}</b>"

    referrer_info = ""
    if details["referrer"]:
        referrer_info = f"\n• Приглашён: @{details['referrer']}"

    blocked_info = "\n⛔ <b>ЗАБЛОКИРОВАН</b>" if user.is_blocked else ""

    text = (
        f"👤 <b>Пользователь #{user.id}</b>{blocked_info}\n\n"
        f"📋 <b>Основное:</b>\n"
        f"• Username: {f'@{user.username}' if user.username else '—'}\n"
        f"• Имя: {user.first_name}\n"
        f"• Язык: {user.language_code}\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• Зарегистрирован: {user.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"• Последняя активность: {user.last_active_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"• Сообщений всего: <b>{details['msg_count']}</b>\n"
        f"• Слов в словаре: <b>{details['words_count']}</b>\n\n"
        f"💎 <b>Подписка:</b>\n"
        f"• Статус: {status_name}{premium_info}\n"
        f"• Оплат всего: <b>{details['payment_count']}</b>\n\n"
        f"👥 <b>Рефералы:</b>{referrer_info}\n"
        f"• Пригласил: <b>{details['referrals_count']}</b> человек"
    )

    if edit:
        await message.edit_text(
            text,
            reply_markup=get_admin_user_keyboard(user.id, user.is_blocked),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            text,
            reply_markup=get_admin_user_keyboard(user.id, user.is_blocked),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("admin:give_premium:"))
async def callback_give_premium(callback: CallbackQuery):
    """Show premium days selection."""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    user_id = int(callback.data.split(":")[2])

    user_repo = UserRepository()
    user = await user_repo.get(user_id)

    name = f"@{user.username}" if user and user.username else f"user_{user_id}"

    await callback.answer()
    await callback.message.edit_text(
        f"💎 <b>Выдать Premium</b>\n\n"
        f"Пользователь: {name}\n\n"
        f"Выберите срок:",
        reply_markup=get_admin_premium_days_keyboard(user_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin:premium_days:"))
async def callback_premium_days(callback: CallbackQuery):
    """Grant premium days to user."""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    parts = callback.data.split(":")
    user_id = int(parts[2])
    days = int(parts[3])

    user_repo = UserRepository()
    new_until = await user_repo.add_premium_days(user_id, days)

    user = await user_repo.get(user_id)
    name = f"@{user.username}" if user and user.username else f"user_{user_id}"

    # Check if this is permanent premium (100 years)
    is_permanent = days >= 36500

    if is_permanent:
        await callback.answer("✅ Перманентный Premium выдан!", show_alert=True)
        await callback.message.edit_text(
            f"✅ <b>Premium выдан!</b>\n\n"
            f"Пользователь: {name}\n"
            f"Срок: ♾️ <b>Навсегда</b>\n"
            f"Активен до: {new_until.strftime('%d.%m.%Y')}",
            reply_markup=get_admin_user_keyboard(
                user_id, user.is_blocked if user else False),
            parse_mode="HTML"
        )

        # Notify user
        try:
            await callback.bot.send_message(
                user_id,
                f"🎁 Вам выдан <b>перманентный Premium</b>!\n"
                f"♾️ Подписка активна навсегда!",
                parse_mode="HTML"
            )
        except Exception:
            pass
    else:
        await callback.answer(f"✅ Premium выдан на {days} дней!", show_alert=True)
        await callback.message.edit_text(
            f"✅ <b>Premium выдан!</b>\n\n"
            f"Пользователь: {name}\n"
            f"Срок: {days} дней\n"
            f"Активен до: {new_until.strftime('%d.%m.%Y')}",
            reply_markup=get_admin_user_keyboard(
                user_id, user.is_blocked if user else False),
            parse_mode="HTML"
        )

        # Notify user
        try:
            await callback.bot.send_message(
                user_id,
                f"🎁 Вам выдан Premium на <b>{days} дней</b>!\n"
                f"Активен до: {new_until.strftime('%d.%m.%Y')}",
                parse_mode="HTML"
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("admin:block:"))
async def callback_block_user(callback: CallbackQuery):
    """Block user."""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    user_id = int(callback.data.split(":")[2])

    user_repo = UserRepository()
    await user_repo.block(user_id)

    await callback.answer("🚫 Пользователь заблокирован", show_alert=True)
    await show_user_card(callback.message, user_id, edit=True)


@router.callback_query(F.data.startswith("admin:unblock:"))
async def callback_unblock_user(callback: CallbackQuery):
    """Unblock user."""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    user_id = int(callback.data.split(":")[2])

    user_repo = UserRepository()
    await user_repo.unblock(user_id)

    await callback.answer("✅ Пользователь разблокирован", show_alert=True)
    await show_user_card(callback.message, user_id, edit=True)


@router.callback_query(F.data.startswith("admin:message:"))
async def callback_message_user(callback: CallbackQuery, state: FSMContext):
    """Start composing message to user."""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    user_id = int(callback.data.split(":")[2])

    await state.set_state(AdminStates.waiting_user_message)
    await state.update_data(target_user_id=user_id)

    user_repo = UserRepository()
    user = await user_repo.get(user_id)
    name = f"@{user.username}" if user and user.username else f"user_{user_id}"

    await callback.answer()
    await callback.message.edit_text(
        f"📨 <b>Сообщение пользователю</b>\n\n"
        f"Получатель: {name}\n\n"
        f"Введите текст сообщения:",
        parse_mode="HTML"
    )


@router.message(AdminStates.waiting_user_message)
async def process_user_message(message: Message, state: FSMContext):
    """Send message to user."""
    if not settings.is_admin(message.from_user.id):
        return

    data = await state.get_data()
    user_id = data.get("target_user_id")

    if not user_id:
        await state.clear()
        return

    try:
        await message.bot.send_message(user_id, message.text)
        await message.answer(
            "✅ Сообщение отправлено!",
            reply_markup=get_admin_main_keyboard()
        )
    except Exception as e:
        await message.answer(
            f"❌ Не удалось отправить сообщение: {e}",
            reply_markup=get_admin_main_keyboard()
        )

    await state.clear()


# Broadcast
@router.callback_query(F.data == "admin:broadcast")
async def callback_broadcast(callback: CallbackQuery):
    """Show broadcast audience selection."""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_text(
        "📢 <b>Рассылка сообщений</b>\n\n"
        "Выберите аудиторию:",
        reply_markup=get_admin_broadcast_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin:broadcast:"))
async def callback_broadcast_audience(callback: CallbackQuery, state: FSMContext):
    """Set broadcast audience and ask for message."""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    audience = callback.data.split(":")[2]

    admin_repo = AdminRepository()
    user_ids = await admin_repo.get_broadcast_audience(audience)

    if not user_ids:
        await callback.answer("Нет пользователей для рассылки", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_broadcast_text)
    await state.update_data(broadcast_audience=audience, broadcast_count=len(user_ids))

    audience_names = {"all": "всем", "premium": "Premium", "free": "Free"}

    await callback.answer()
    await callback.message.edit_text(
        f"📝 <b>Рассылка {audience_names.get(audience, 'всем')}</b>\n\n"
        f"Получателей: <b>{len(user_ids)}</b>\n\n"
        f"Введите текст рассылки:",
        parse_mode="HTML"
    )


@router.message(AdminStates.waiting_broadcast_text)
async def process_broadcast(message: Message, state: FSMContext):
    """Send broadcast message."""
    if not settings.is_admin(message.from_user.id):
        return

    data = await state.get_data()
    audience = data.get("broadcast_audience", "all")

    admin_repo = AdminRepository()
    user_ids = await admin_repo.get_broadcast_audience(audience)

    await state.clear()

    status_msg = await message.answer(f"📤 Отправка... 0/{len(user_ids)}")

    success = 0
    failed = 0

    for i, user_id in enumerate(user_ids, 1):
        try:
            await message.bot.send_message(user_id, message.text)
            success += 1
        except Exception:
            failed += 1

        # Update status every 10 messages
        if i % 10 == 0:
            try:
                await status_msg.edit_text(f"📤 Отправка... {i}/{len(user_ids)}")
            except Exception:
                pass

    await status_msg.edit_text(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"• Успешно: <b>{success}</b>\n"
        f"• Ошибок: <b>{failed}</b>",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin:premium_all_admins")
async def callback_premium_all_admins(callback: CallbackQuery):
    """Grant permanent premium to all admins."""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    await callback.answer()

    # Get all admin IDs from config
    admin_ids = [int(aid.strip())
                 for aid in settings.ADMIN_IDS.split(',') if aid.strip()]

    user_repo = UserRepository()
    granted = []
    failed = []

    for admin_id in admin_ids:
        try:
            # Grant 100 years of premium (permanent)
            new_until = await user_repo.add_premium_days(admin_id, 36500)
            user = await user_repo.get(admin_id)
            name = f"@{user.username}" if user and user.username else f"user_{admin_id}"
            granted.append(name)

            # Notify admin
            try:
                await callback.bot.send_message(
                    admin_id,
                    f"🎁 Вам выдан <b>перманентный Premium</b>!\n"
                    f"♾️ Подписка активна навсегда!",
                    parse_mode="HTML"
                )
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Failed to grant premium to admin {admin_id}: {e}")
            failed.append(str(admin_id))

    result_text = f"✅ <b>Premium выдан всем админам!</b>\n\n"

    if granted:
        result_text += f"♾️ <b>Перманентный Premium получили:</b>\n"
        result_text += "\n".join([f"• {name}" for name in granted])

    if failed:
        result_text += f"\n\n❌ <b>Ошибки:</b>\n"
        result_text += "\n".join([f"• ID {fid}" for fid in failed])

    await callback.message.edit_text(
        result_text,
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML"
    )


def _format_gift_days(days: int) -> str:
    """Format gift link duration for display."""
    if days >= 36500:
        return "♾️ Навсегда"
    return f"{days} дней"


async def _build_gift_link(bot, token: str) -> str:
    """Build Telegram deep link for a gift token."""
    me = await bot.get_me()
    return f"https://t.me/{me.username}?start=gift_{token}"


@router.callback_query(F.data == "admin:gift")
async def callback_admin_gift(callback: CallbackQuery):
    """Show gift link creation menu."""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_text(
        "🎁 <b>Одноразовая Gift-ссылка</b>\n\n"
        "Ссылка срабатывает один раз: первый человек, "
        "кто перейдёт по ней и нажмёт Start, получит Premium.\n\n"
        "Выберите срок:",
        reply_markup=get_admin_gift_days_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("admin:gift_days:"))
async def callback_admin_gift_days(callback: CallbackQuery):
    """Create one-time gift link."""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    days = int(callback.data.split(":")[2])
    gift_repo = GiftLinkRepository()
    gift = await gift_repo.create(created_by=callback.from_user.id, days=days)
    link = await _build_gift_link(callback.bot, gift.token)

    await callback.answer("✅ Ссылка создана!", show_alert=True)
    await callback.message.edit_text(
        f"🎁 <b>Gift-ссылка создана!</b>\n\n"
        f"Срок: <b>{_format_gift_days(days)}</b>\n"
        f"Статус: 🟢 не использована\n\n"
        f"Отправь эту ссылку человеку:\n"
        f"<code>{link}</code>\n\n"
        f"<i>⚠️ Ссылка одноразовая — после первого перехода станет недействительной.</i>",
        reply_markup=get_admin_gift_result_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin:gift_list")
async def callback_admin_gift_list(callback: CallbackQuery):
    """Show recent gift links."""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    gift_repo = GiftLinkRepository()
    gifts = await gift_repo.list_recent(limit=10)

    if not gifts:
        await callback.answer()
        await callback.message.edit_text(
            "📋 <b>Gift-ссылки</b>\n\nПока нет созданных ссылок.",
            reply_markup=get_admin_gift_days_keyboard(),
            parse_mode="HTML",
        )
        return

    me = await callback.bot.get_me()
    lines = ["📋 <b>Последние gift-ссылки</b>\n"]
    for gift in gifts:
        status = "✅ использована" if gift.is_used else (
            "⏰ истекла" if gift.is_expired else "🟢 активна"
        )
        link = f"https://t.me/{me.username}?start=gift_{gift.token}"
        lines.append(
            f"• {_format_gift_days(gift.days_granted)} — {status}\n"
            f"  <code>{link}</code>"
        )

    await callback.answer()
    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=get_admin_gift_days_keyboard(),
        parse_mode="HTML",
    )
