"""Authentication middleware - loads/creates user from DB."""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from bot.database.repositories import UserRepository


class AuthMiddleware(BaseMiddleware):
    """Middleware that loads or creates user and adds to handler data."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Get user from event
        user_tg = None
        if isinstance(event, Message):
            user_tg = event.from_user
        elif isinstance(event, CallbackQuery):
            user_tg = event.from_user
        
        if not user_tg:
            return await handler(event, data)
        
        # Load or create user
        repo = UserRepository()
        user = await repo.get(user_tg.id)
        
        if not user:
            # Create new user
            user = await repo.create(
                user_id=user_tg.id,
                username=user_tg.username,
                first_name=user_tg.first_name or "User",
                language_code=user_tg.language_code or "ru"
            )
        else:
            # Update last active
            await repo.update_last_active(user_tg.id)
            
            # Update username if changed
            if user.username != user_tg.username:
                await repo.update(user_tg.id, username=user_tg.username)
        
        # Check if user is blocked
        if user.is_blocked:
            if isinstance(event, Message):
                await event.answer("⛔ Ваш аккаунт заблокирован.")
            return None
        
        # Add user to handler data
        data["user"] = user
        
        return await handler(event, data)
