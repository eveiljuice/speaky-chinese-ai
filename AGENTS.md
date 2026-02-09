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
- `bot/handlers/callbacks.py` — Inline button handlers (Text, Help, Translate, Explain)
- `bot/database/repositories.py` — All CRUD operations

### Help Button Feature
- When user clicks "❓ Помощь" button, bot generates 2-3 response suggestions
- Each suggestion includes Chinese text + pinyin (format: "我今天看书。- Wǒ jīntiān kàn shū.")
- Suggestions are context-aware based on conversation history and HSK level

### Error Correction Feature
- When AI detects errors in user's Chinese text, it displays a correction message
- Correction format: ~~错误文本~~ → ✅ **正确文本** + *pinyin*
- Pinyin is automatically generated for the corrected text
- User can click "💡 Объяснить" button for detailed explanation of the error

### Dialogue Topics
Available topics for conversation:
- ✈️ Путешествия (旅游) - travel
- 🍜 Еда (美食) - food
- 💼 Работа (工作) - work
- 🏠 Быт (日常生活) - daily life
- 📚 Учёба (学习) - study
- 🏥 Здоровье (健康) - health
- 💬 Свободный диалог (自由对话) - free conversation on any topic

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

## Deployment (Production)

### Railway Deployment (Current Setup)

#### Initial Setup

1. **Connect GitHub repository to Railway**
   - Go to [Railway Dashboard](https://railway.app)
   - Create new project → Deploy from GitHub
   - Select `speaky-chinese` repository

2. **Configure Environment Variables**
   Add these in Railway dashboard:
   ```
   BOT_TOKEN=your_telegram_bot_token
   OPENAI_API_KEY=your_openai_api_key
   ADMIN_IDS=comma,separated,telegram,ids
   TRIBUTE_API_KEY=your_tribute_api_key
   TRIBUTE_PRODUCT_ID=your_product_id
   TRIBUTE_PAYMENT_LINK=https://t.me/tribute/app?startapp=pq5z
   LOG_LEVEL=INFO
   ```

3. **Railway will automatically deploy**
   - Uses `Procfile` → runs `railway_start.py` (webhook mode)
   - Port is provided by Railway via `PORT` env var
   - Public URL is provided via `RAILWAY_STATIC_URL`

#### Important Railway Settings

**⚠️ CRITICAL: Set Replica Count to 1**
- Go to Settings → Deploy
- Set "Replicas" = 1
- Multiple replicas cause "Conflict: terminated by other getUpdates" error

**Railway Configuration (`railway.json`):**
```json
{
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE"
  }
}
```

#### Deployment Commands

```bash
# Deploy via git push
git add .
git commit -m "update: feature description"
git push origin main  # Railway auto-deploys

# View logs
railway logs

# Local Railway CLI
railway up  # Deploy from CLI
railway run python railway_start.py  # Test locally with Railway env vars
```

#### Health Check

```bash
# Check bot is running
curl https://your-railway-app.railway.app/health

# Response should be:
# {"status": "ok", "service": "speaky-chinese-bot", "mode": "webhook"}
```

#### Webhook vs Polling Mode

- **Railway (Production)**: Uses `railway_start.py` → Webhook mode
- **Local Development**: Use `python -m bot.main` → Polling mode
- **Never run polling mode on Railway** → causes multiple instances conflict
- `bot.main` blocks polling if Railway env vars are present

#### Troubleshooting Railway

**"Conflict: terminated by other getUpdates"**
- ✅ Check: Only 1 replica running (Railway Settings → Deploy)
- ✅ Check: No other deployments active
- ✅ Check: Using `railway_start.py` (webhook), not `bot.main` (polling)
- ✅ Fix: Delete webhook if needed: `python delete_webhook.py`

**Check active deployments:**
```bash
railway status
# Should show only 1 active deployment
```

**Force restart:**
```bash
railway restart
# or via dashboard: Deployments → Active → Restart
```

### Alternative: Systemd Service (VPS/Timeweb)

If deploying to VPS instead of Railway:

```bash
# 1. Setup on server
cd /root/speaky-chinese/speaky-chinese-ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure .env with production values
nano .env

# 3. Install systemd service
cp speaky-chinese.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable speaky-chinese.service
systemctl start speaky-chinese.service

# 4. Check status
systemctl status speaky-chinese
journalctl -u speaky-chinese.service -f
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
- [ ] Error correction display (with pinyin for corrected text)
- [ ] Inline buttons (Text, Help, Translate, Explain)
- [ ] Settings change (level, speed, topic)
- [ ] Settings navigation (submenu → back → close)
- [ ] Profile subscription button (👤 Профиль → "Купить/Управление подпиской")
- [ ] Premium purchase via Tribute (/premium → payment link)
- [ ] Webhook payment processing (POST /webhook/tribute)
- [ ] Admin panel (stats, users, broadcast)
- [ ] Admin premium management (grant days, grant permanent premium)
- [ ] Grant permanent premium to all admins (one-click button)

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

## Admin Features

### Premium Management
Admins can grant premium subscriptions to users through the admin panel:

1. **Grant Premium to User**
   - `/admin` → Search user or browse user list
   - Click user card → "💎 Выдать Premium"
   - Select duration: 7, 30, 90 days, or ♾️ Навсегда (permanent)
   - Permanent premium = 100 years (36500 days)

2. **Grant Premium to All Admins**
   - `/admin` → "♾️ Premium для админов"
   - One-click grants permanent premium to all admin IDs from config
   - All admins get notification about permanent premium

3. **Premium Features**
   - Permanent premium displayed as "♾️ Навсегда" in UI
   - Users get notified when premium is granted
   - Premium status affects subscription middleware (unlimited usage)

### Admin Panel Features
- **📊 Statistics**: Users, premium count, DAU/WAU/MAU, revenue
- **👥 User Management**: Browse all users, premium users only
- **🔍 Search**: Find users by Telegram ID or @username
- **💎 Grant Premium**: 7/30/90 days or permanent subscription
- **🚫 Block/Unblock**: Manage access to bot
- **📨 Direct Messages**: Send message to specific user
- **📢 Broadcast**: Send message to all/premium/free users

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
- **Railway Persistence**: Set `DB_PATH=/data/bot.db` + create Railway Volume mounted at `/data`
- Migrations run automatically on startup (safe `ALTER TABLE ADD COLUMN`)

### Subscription Expiry Notifications
- Background task runs every 1 hour (`subscription_checker.py`)
- Detects expired trials → sends message with Tribute payment button
- Detects expired premium → sends renewal notification
- Notification flags (`trial_notified`, `premium_expired_notified`) prevent duplicate messages
- `premium_expired_notified` resets when premium is re-activated

### Testing
```bash
# Run all subscription lifecycle tests
python -m pytest tests/test_subscription_lifecycle.py -v

# Test covers:
# - Trial/Free/Premium status transitions
# - Tribute payment → 30 days premium
# - Premium expiry → features blocked
# - Renewal restores premium
# - Free tier limits enforcement
# - Expiry notification system
# - Webhook signature verification
# - DB persistence across connections
```
