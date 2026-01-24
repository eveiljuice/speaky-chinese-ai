"""Reply keyboards (bottom menu)."""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Get main bottom menu keyboard."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👤 Профиль"),
                KeyboardButton(text="⚙️ Настройки")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Отправь голосовое сообщение на китайском..."
    )
    return keyboard
