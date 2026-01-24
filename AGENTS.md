# AGENTS.md

## Project Overview

### Payment Integration (Tribute)
- **Payment Provider**: Tribute ([@tribute](https://t.me/tribute))
- **Product Type**: Digital Product (разовая покупка на 30 дней)
- **Payment Link**: https://t.me/tribute/app?startapp=pq5z
- **Webhook Server**: `webhook_server.py` runs on port 8080
- **Webhook Event**: `new_digital_product` — grants 30 days premium
- **Setup Guide**: See `WEBHOOK_SETUP.md` for detailed instructions

#### Subscription Flow
1. User clicks "💎 Купить подписку Premium" in profile or /premium
2. Opens Tribute payment page via `TRIBUTE_PAYMENT_LINK`
3. User completes payment in Tribute
4. Tribute sends POST to webhook (`/webhook/tribute`)
5. Webhook grants 30 days premium + notifies user
6. If referral exists, referrer gets +30 days bonus

#### Key Files
- `bot/handlers/profile.py` — Shows subscription button in profile
- `bot/handlers/premium.py` — /premium command with payment button
- `bot/keyboards/inline.py` — `get_profile_subscription_keyboard()`, `get_premium_keyboard()`
- `webhook_server.py` — Handles Tribute webhooks

## Project Overview

**HanYu 汉语** — Telegram-бот для практики разговорного китайского языка с AI.

### Tech Stack
- **Runtime**: Python 3.11+
- **Bot Framework**: aiogram 3.x
- **Database**: SQLite 3.x + aiosqlite 0.19+
- **AI**: OpenAI API (Whisper, GPT-4o-mini, TTS)
- **Validation**: Pydantic 2.x, pydantic-settings 2.x

### Architecture
- Event-driven with aiogram handlers
- Middleware chain: Throttling → Auth → Subscription
- Repository pattern for database operations
- Service layer for AI integrations

## Dev Environment Tips

### Setup
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# Fill in BOT_TOKEN, OPENAI_API_KEY, ADMIN_IDS in .env
```

### Project Structure
```
hanyu-bot/
├── bot/
│   ├── main.py           # Entry point
│   ├── config.py         # Pydantic settings
│   ├── handlers/         # Command handlers (dialog, settings, premium, etc.)
│   ├── keyboards/        # Reply & Inline keyboards
│   ├── middlewares/      # Auth, subscription, throttling
│   ├── services/         # AI services (Whisper, GPT, TTS)
│   ├── database/         # Models, repos, schema
│   └── utils/            # HSK dictionaries
├── data/                 # HSK JSON files
└── requirements.txt
```

### Key Files
- `bot/config.py` — All settings from .env
- `bot/services/ai.py` — Whisper, GPT, TTS integration
- `bot/handlers/dialog.py` — Main voice/text processing
- `bot/database/repositories.py` — All CRUD operations

## Build & Run Commands

```bash
# Option 1: Run bot only (polling mode)
python -m bot.main

# Option 2: Run bot + webhook server together
python start_all.py

# Option 3: Run separately in different terminals
# Terminal 1: Webhook server
python webhook_server.py

# Terminal 2: Bot
python -m bot.main

# Terminal 3 (if testing locally): ngrok for webhook
ngrok http 8080

# Run with specific log level
LOG_LEVEL=DEBUG python -m bot.main

# Format code
black bot/
isort bot/

# Type checking (if installed)
mypy bot/
```

## Testing Instructions

### Manual Testing
1. Start bot: `python -m bot.main`
2. Send /start to bot in Telegram
3. Test voice message → should get voice reply
4. Test text message → should get voice reply
5. Test /settings, /topic, /premium commands
6. Test /admin (only works for ADMIN_IDS)

### Key Flows to Test
- [ ] New user registration (/start)
- [ ] Referral link (/start?start=ref_CODE)
- [ ] Voice message processing
- [ ] Text message processing
- [ ] Error correction display
- [ ] Inline buttons (Text, Help, Translate, Explain)
- [ ] Settings change (level, speed, topic)
- [ ] Profile subscription button (👤 Профиль → "Купить/Управление подпиской")
- [ ] Premium purchase via Tribute (/premium → payment link)
- [ ] Webhook payment processing (POST /webhook/tribute)
- [ ] Admin panel (stats, users, broadcast)

## Code Style Guidelines

### Naming
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/Variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

### Imports Order
1. Standard library
2. Third-party (aiogram, openai, pydantic)
3. Local imports (bot.*)

### Handler Pattern
```python
@router.message(Command("cmd"))
async def cmd_handler(message: Message, user: User):
    """Handle /cmd command."""
    # Handler logic
```

### Repository Pattern
- All DB operations through repository classes
- Use `async with get_db()` for connections
- Return dataclass models from repositories

## Git & PR Instructions

### Branch Naming
- `feature/description`
- `fix/description`
- `refactor/description`

### Commit Message Format
```
type: short description

- detail 1
- detail 2
```

Types: feat, fix, refactor, docs, test, chore

## Security & Best Practices

### Secrets
- Never commit `.env` file
- Use `.env.example` for documentation
- Admin IDs in env, not in code

### Input Validation
- Max text length: 500 chars (configurable)
- Max voice duration: 60 sec (configurable)
- Rate limiting: 1 msg/sec per user

### Error Handling
- Log errors with context
- Show user-friendly messages
- Don't expose internal errors

### Database
- SQLite for simplicity
- Foreign keys enabled
- Indexes on frequently queried columns
