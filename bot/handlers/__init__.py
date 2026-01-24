"""Bot handlers."""

from aiogram import Router


def setup_routers() -> Router:
    """Setup and return main router with all handlers."""
    from . import start, dialog, topic, settings, premium, referral, admin, callbacks, profile
    
    router = Router()
    
    # Register all routers
    router.include_router(start.router)
    router.include_router(topic.router)
    router.include_router(settings.router)
    router.include_router(premium.router)
    router.include_router(referral.router)
    router.include_router(profile.router)
    router.include_router(admin.router)
    router.include_router(callbacks.router)
    router.include_router(dialog.router)  # Dialog last - catches all messages
    
    return router
