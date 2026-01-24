"""Throttling middleware - rate limiting to prevent spam."""

import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery


class ThrottlingMiddleware(BaseMiddleware):
    """Rate limiting middleware - 1 message per second per user."""
    
    def __init__(self, rate_limit: float = 1.0):
        self.rate_limit = rate_limit
        self.user_last_message: Dict[int, float] = {}
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Get user ID
        user_id = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id
        
        if not user_id:
            return await handler(event, data)
        
        now = time.time()
        
        # Check rate limit
        if user_id in self.user_last_message:
            elapsed = now - self.user_last_message[user_id]
            if elapsed < self.rate_limit:
                # Too fast - ignore message silently
                return None
        
        # Update last message time
        self.user_last_message[user_id] = now
        
        # Cleanup old entries (every 100 users)
        if len(self.user_last_message) > 1000:
            cutoff = now - 60  # Remove entries older than 1 minute
            self.user_last_message = {
                uid: ts for uid, ts in self.user_last_message.items()
                if ts > cutoff
            }
        
        return await handler(event, data)
