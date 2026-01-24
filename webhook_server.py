"""Webhook server for Tribute payment notifications."""
import asyncio
import hmac
import hashlib
import logging
import sys
from aiohttp import web
from aiogram import Bot

# Add bot directory to path
sys.path.insert(0, '.')

from bot.config import settings
from bot.database import init_db
from bot.database.repositories import UserRepository, PaymentRepository, ReferralRepository

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def verify_signature(payload: str, signature: str) -> bool:
    """Verify Tribute webhook signature using HMAC-SHA256."""
    if not settings.TRIBUTE_API_KEY or not signature:
        return False
    
    secret = settings.TRIBUTE_API_KEY.encode()
    expected = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


async def tribute_webhook_handler(request):
    """Handle Tribute payment webhook."""
    try:
        # Read raw payload for signature verification
        payload_text = await request.text()
        signature = request.headers.get('trbt-signature', '')
        
        logger.info(f"Received webhook request, signature: {signature[:20]}...")
        
        # Verify signature
        if not verify_signature(payload_text, signature):
            logger.warning("Invalid webhook signature!")
            return web.json_response({'error': 'Invalid signature'}, status=403)
        
        # Parse JSON
        data = await request.json()
        event_name = data.get('name', '')
        
        logger.info(f"Webhook event: {event_name}")
        
        # Handle digital product purchase
        if event_name == 'new_digital_product':
            payload = data.get('payload', {})
            user_id = payload.get('telegram_user_id')
            amount = payload.get('amount')
            product_id = payload.get('product_id')
            
            logger.info(f"Digital product purchase: user_id={user_id}, product_id={product_id}, amount={amount}")
            
            # Validate product ID if configured (convert both to string for comparison)
            if settings.TRIBUTE_PRODUCT_ID and str(product_id) != str(settings.TRIBUTE_PRODUCT_ID):
                logger.warning(f"Unknown product ID: {product_id} (expected: {settings.TRIBUTE_PRODUCT_ID})")
                return web.json_response({'error': 'Unknown product'}, status=400)
            
            if not user_id:
                logger.error("Missing telegram_user_id in payload")
                return web.json_response({'error': 'Missing user_id'}, status=400)
            
            # Grant premium access
            user_repo = UserRepository()
            payment_repo = PaymentRepository()
            referral_repo = ReferralRepository()
            
            # Add 30 days premium
            new_premium_until = await user_repo.add_premium_days(user_id, days=30)
            logger.info(f"Premium granted to user {user_id} until {new_premium_until}")
            
            # Record payment
            await payment_repo.create(
                user_id=user_id,
                amount=amount,
                days_granted=30,
                source="payment",
                status="completed",
                provider_payment_id=str(product_id)
            )
            
            # Check referral bonus
            referral = await referral_repo.get_by_referred(user_id)
            if referral and referral.status == "registered":
                await user_repo.add_premium_days(referral.referrer_id, days=30)
                await referral_repo.update_status(user_id, "subscribed")
                logger.info(f"Referral bonus granted to user {referral.referrer_id}")
                
                # Notify referrer
                bot = Bot(token=settings.BOT_TOKEN)
                try:
                    await bot.send_message(
                        referral.referrer_id,
                        "🎉 <b>Ваш друг купил Premium!</b>\n\n"
                        "Вам начислено <b>+30 дней</b> Premium в подарок!",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.warning(f"Failed to notify referrer: {e}")
                finally:
                    await bot.session.close()
            
            # Notify user about successful activation
            bot = Bot(token=settings.BOT_TOKEN)
            try:
                await bot.send_message(
                    user_id,
                    f"🎉 <b>Premium успешно активирован!</b>\n\n"
                    f"Активен до: <b>{new_premium_until.strftime('%d.%m.%Y')}</b>\n\n"
                    f"✅ Безлимитные голосовые сообщения\n"
                    f"✅ Безлимитные текстовые сообщения\n"
                    f"✅ Приоритетная поддержка\n\n"
                    f"Спасибо за покупку! 🙏",
                    parse_mode="HTML"
                )
                logger.info(f"User {user_id} notified about premium activation")
            except Exception as e:
                logger.warning(f"Failed to notify user {user_id}: {e}")
            finally:
                await bot.session.close()
            
            return web.json_response({'ok': True, 'status': 'premium_granted'})
        
        # Other events - just acknowledge
        logger.info(f"Unhandled event type: {event_name}")
        return web.json_response({'ok': True})
        
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return web.json_response({'error': str(e)}, status=500)


async def health_check_handler(request):
    """Health check endpoint."""
    return web.json_response({
        'status': 'ok',
        'service': 'speaky-chinese-webhook',
        'tribute_configured': bool(settings.TRIBUTE_API_KEY and settings.TRIBUTE_PRODUCT_ID)
    })


async def init_app():
    """Initialize webhook application."""
    # Initialize database
    logger.info("Initializing database...")
    await init_db()
    
    # Create web app
    app = web.Application()
    app.router.add_post('/webhook/tribute', tribute_webhook_handler)
    app.router.add_get('/health', health_check_handler)
    app.router.add_get('/', health_check_handler)
    
    return app


def main():
    """Run webhook server."""
    logger.info("Starting Tribute webhook server...")
    logger.info(f"Port: {settings.WEBHOOK_PORT}")
    logger.info(f"Tribute API Key configured: {bool(settings.TRIBUTE_API_KEY)}")
    logger.info(f"Tribute Product ID: {settings.TRIBUTE_PRODUCT_ID}")
    
    if not settings.TRIBUTE_API_KEY:
        logger.warning("⚠️  TRIBUTE_API_KEY not set! Webhook signature verification will fail.")
    if not settings.TRIBUTE_PRODUCT_ID:
        logger.warning("⚠️  TRIBUTE_PRODUCT_ID not set! Payment processing may fail.")
    
    # Run app
    app = asyncio.run(init_app())
    web.run_app(app, host='0.0.0.0', port=settings.WEBHOOK_PORT)


if __name__ == '__main__':
    main()
