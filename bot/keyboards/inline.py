"""Inline keyboards."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_message_keyboard(message_id: int, has_correction: bool = False) -> InlineKeyboardMarkup:
    """Get inline keyboard for bot response message."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="📝 Текст", callback_data=f"text:{message_id}"),
        InlineKeyboardButton(
            text="❓ Помощь", callback_data=f"help:{message_id}"),
        InlineKeyboardButton(
            text="🔄 Перевод", callback_data=f"translate:{message_id}")
    )

    if has_correction:
        builder.row(
            InlineKeyboardButton(text="💡 Объяснить",
                                 callback_data=f"explain:{message_id}")
        )

    return builder.as_markup()


def get_topic_keyboard(current_topic: str) -> InlineKeyboardMarkup:
    """Get topic selection keyboard."""
    topics = [
        ("travel", "✈️ Путешествия"),
        ("food", "🍜 Еда"),
        ("work", "💼 Работа"),
        ("daily", "🏠 Быт"),
        ("study", "📚 Учёба"),
        ("health", "🏥 Здоровье")
    ]

    builder = InlineKeyboardBuilder()

    for topic_id, topic_name in topics:
        mark = "✅ " if topic_id == current_topic else ""
        builder.button(
            text=f"{mark}{topic_name}",
            callback_data=f"topic:{topic_id}"
        )

    builder.adjust(2)  # 2 buttons per row
    return builder.as_markup()


def get_level_keyboard(current_level: int) -> InlineKeyboardMarkup:
    """Get HSK level selection keyboard."""
    builder = InlineKeyboardBuilder()

    for level in [1, 2, 3]:
        mark = "✅ " if level == current_level else ""
        builder.button(
            text=f"{mark}HSK {level}",
            callback_data=f"level:{level}"
        )

    builder.adjust(3)
    return builder.as_markup()


def get_speed_keyboard(current_speed: str) -> InlineKeyboardMarkup:
    """Get speech speed selection keyboard."""
    speeds = [
        ("slow", "🐢 Медленно"),
        ("normal", "🚶 Нормально"),
        ("fast", "🏃 Быстро")
    ]

    builder = InlineKeyboardBuilder()

    for speed_id, speed_name in speeds:
        mark = "✅ " if speed_id == current_speed else ""
        builder.button(
            text=f"{mark}{speed_name}",
            callback_data=f"speed:{speed_id}"
        )

    builder.adjust(3)
    return builder.as_markup()


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Get settings menu keyboard."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📊 Изменить уровень HSK",
                             callback_data="settings:level")
    )
    builder.row(
        InlineKeyboardButton(text="🔊 Изменить скорость речи",
                             callback_data="settings:speed")
    )
    builder.row(
        InlineKeyboardButton(text="🎯 Изменить тему",
                             callback_data="settings:topic")
    )

    return builder.as_markup()


def get_premium_keyboard() -> InlineKeyboardMarkup:
    """Get premium purchase keyboard."""
    from bot.config import settings

    builder = InlineKeyboardBuilder()

    # If Tribute is configured, show payment link
    if settings.TRIBUTE_PAYMENT_LINK:
        builder.row(
            InlineKeyboardButton(
                text="💎 Купить Premium — ₽770/мес",
                url=settings.TRIBUTE_PAYMENT_LINK
            )
        )
    else:
        # Fallback message if Tribute not configured
        builder.row(
            InlineKeyboardButton(
                text="💎 Покупка временно недоступна",
                callback_data="noop"
            )
        )

    return builder.as_markup()


def get_profile_subscription_keyboard(has_premium: bool) -> InlineKeyboardMarkup:
    """Get subscription button for profile based on premium status.
    
    Args:
        has_premium: True if user has active Premium subscription
        
    Returns:
        Keyboard with "Управление подпиской" or "Купить подписку Premium" button
    """
    from bot.config import settings

    builder = InlineKeyboardBuilder()

    if settings.TRIBUTE_PAYMENT_LINK:
        button_text = "💎 Управление подпиской" if has_premium else "💎 Купить подписку Premium"
        builder.row(
            InlineKeyboardButton(
                text=button_text,
                url=settings.TRIBUTE_PAYMENT_LINK
            )
        )
    else:
        # Fallback if Tribute not configured
        builder.row(
            InlineKeyboardButton(
                text="💎 Подписка временно недоступна",
                callback_data="noop"
            )
        )

    return builder.as_markup()


def get_pagination_keyboard(
    page: int,
    total_pages: int,
    callback_prefix: str
) -> InlineKeyboardMarkup:
    """Get pagination keyboard."""
    builder = InlineKeyboardBuilder()

    buttons = []

    if page > 1:
        buttons.append(
            InlineKeyboardButton(
                text="◀️", callback_data=f"{callback_prefix}:{page - 1}")
        )

    buttons.append(
        InlineKeyboardButton(
            text=f"{page}/{total_pages}", callback_data="noop")
    )

    if page < total_pages:
        buttons.append(
            InlineKeyboardButton(
                text="▶️", callback_data=f"{callback_prefix}:{page + 1}")
        )

    builder.row(*buttons)

    return builder.as_markup()


# Admin keyboards
def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    """Get admin panel main keyboard."""
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(
        text="👥 Все пользователи", callback_data="admin:users:all"))
    builder.row(InlineKeyboardButton(text="💎 Premium пользователи",
                callback_data="admin:users:premium"))
    builder.row(InlineKeyboardButton(
        text="📈 Статистика", callback_data="admin:stats"))
    builder.row(InlineKeyboardButton(
        text="📢 Рассылка", callback_data="admin:broadcast"))

    return builder.as_markup()


def get_admin_user_keyboard(user_id: int, is_blocked: bool) -> InlineKeyboardMarkup:
    """Get admin user card keyboard."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="💎 Выдать Premium",
                             callback_data=f"admin:give_premium:{user_id}")
    )

    if is_blocked:
        builder.row(
            InlineKeyboardButton(text="✅ Разблокировать",
                                 callback_data=f"admin:unblock:{user_id}")
        )
    else:
        builder.row(
            InlineKeyboardButton(text="🚫 Заблокировать",
                                 callback_data=f"admin:block:{user_id}")
        )

    builder.row(
        InlineKeyboardButton(
            text="📨 Написать", callback_data=f"admin:message:{user_id}"),
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")
    )

    return builder.as_markup()


def get_admin_premium_days_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Get premium days selection keyboard."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="7 дней", callback_data=f"admin:premium_days:{user_id}:7"),
        InlineKeyboardButton(
            text="30 дней", callback_data=f"admin:premium_days:{user_id}:30"),
        InlineKeyboardButton(
            text="90 дней", callback_data=f"admin:premium_days:{user_id}:90")
    )
    builder.row(
        InlineKeyboardButton(
            text="◀️ Отмена", callback_data=f"admin:user:{user_id}")
    )

    return builder.as_markup()


def get_admin_broadcast_keyboard() -> InlineKeyboardMarkup:
    """Get broadcast audience selection keyboard."""
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text="👥 Всем пользователям",
                callback_data="admin:broadcast:all"))
    builder.row(InlineKeyboardButton(text="💎 Только Premium",
                callback_data="admin:broadcast:premium"))
    builder.row(InlineKeyboardButton(text="🆓 Только Free",
                callback_data="admin:broadcast:free"))
    builder.row(InlineKeyboardButton(
        text="◀️ Отмена", callback_data="admin:back"))

    return builder.as_markup()


def get_admin_users_keyboard(page: int, total_pages: int, premium_only: bool) -> InlineKeyboardMarkup:
    """Get admin users list keyboard with pagination."""
    builder = InlineKeyboardBuilder()

    prefix = "admin:users:premium" if premium_only else "admin:users:all"

    # Search button
    builder.row(InlineKeyboardButton(
        text="🔍 Поиск", callback_data="admin:search"))

    # Toggle premium/all
    if premium_only:
        builder.row(InlineKeyboardButton(text="👥 Все пользователи",
                    callback_data="admin:users:all:1"))
    else:
        builder.row(InlineKeyboardButton(text="💎 Только Premium",
                    callback_data="admin:users:premium:1"))

    # Pagination
    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton(
            text="◀️", callback_data=f"{prefix}:{page - 1}"))
    buttons.append(InlineKeyboardButton(
        text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        buttons.append(InlineKeyboardButton(
            text="▶️", callback_data=f"{prefix}:{page + 1}"))

    if buttons:
        builder.row(*buttons)

    # Back button
    builder.row(InlineKeyboardButton(
        text="◀️ В меню", callback_data="admin:back"))

    return builder.as_markup()
