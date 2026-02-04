# Railway "Conflict" Error Fix

## Проблема

```
ERROR - Failed to fetch updates - TelegramConflictError: 
Telegram server says - Conflict: terminated by other getUpdates request
```

## Причина

На Railway запущено **несколько реплик (копий)** вашего бота, и все они пытаются получать обновления через polling. Telegram не позволяет нескольким процессам одновременно получать обновления.

## Решение

### 1. Проверьте количество реплик на Railway

1. Откройте [Railway Dashboard](https://railway.app)
2. Выберите проект `speaky-chinese`
3. Перейдите в **Settings → Deploy**
4. Проверьте: **Replicas = 1** (должна быть только одна реплика!)

### 2. Переключитесь на Webhook Mode

Railway предоставляет публичный URL, поэтому лучше использовать webhook вместо polling:

#### Файлы уже созданы:
- ✅ `railway_start.py` - запуск в webhook режиме
- ✅ `Procfile` - указывает Railway использовать `railway_start.py`
- ✅ `railway.json` - конфигурация с `numReplicas: 1`

#### Шаги для переключения:

```bash
# 1. Добавьте новые файлы в git
git add railway_start.py Procfile railway.json
git commit -m "fix: switch to webhook mode for Railway"
git push origin main

# Railway автоматически задеплоит изменения
```

#### Настройте переменные окружения в Railway:

В Railway Dashboard добавьте (если еще нет):
```
BOT_TOKEN=your_bot_token
OPENAI_API_KEY=your_openai_key
ADMIN_IDS=your_telegram_id
TRIBUTE_API_KEY=your_tribute_key
TRIBUTE_PRODUCT_ID=your_product_id
TRIBUTE_PAYMENT_LINK=https://t.me/tribute/app?startapp=pq5z
LOG_LEVEL=INFO
```

Railway автоматически предоставляет:
- `PORT` - порт для приложения
- `RAILWAY_STATIC_URL` - публичный URL вашего приложения

### 3. Проверьте деплоймент

После деплоя проверьте:

```bash
# Через Railway CLI
railway logs

# Или через curl
curl https://your-app.railway.app/health

# Должен вернуть:
# {"status": "ok", "service": "speaky-chinese-bot", "mode": "webhook"}
```

### 4. Проверьте webhook

```bash
# Локально проверьте статус webhook
python check_webhook.py

# Должен показать:
# Webhook URL: https://your-app.railway.app/webhook
```

### 5. Тестирование

Отправьте боту сообщение в Telegram - должно работать без ошибок.

## Альтернатива: Оставить Polling Mode

Если хотите оставить polling mode:

1. Убедитесь что **Replicas = 1** в Railway Settings
2. Измените `Procfile`:
   ```
   web: python -m bot.main
   ```
3. Добавьте в `.env` на Railway:
   ```
   WEBHOOK_MODE=false
   ```

⚠️ **НО:** Webhook mode **более надежен** для Railway, так как:
- Не тратит ресурсы на постоянные запросы к Telegram API
- Мгновенная доставка сообщений
- Нет конфликтов при рестартах

## Проверка текущей конфигурации

```bash
# 1. Сколько активных деплойментов?
railway status

# 2. Какой процесс запущен?
railway logs | head -20
# Должно быть: "Starting SpeakyChinese Bot (Railway Webhook Mode)"

# 3. Есть ли несколько процессов?
# Посмотрите в Railway Dashboard → Deployments
# Должен быть только 1 активный deployment
```

## Полная перезагрузка (если ничего не помогает)

```bash
# 1. На Railway: остановите все деплойменты
# Dashboard → Deployments → Stop все активные

# 2. Локально удалите webhook (если установлен)
python delete_webhook.py

# 3. Задеплойте заново
git push origin main

# 4. Проверьте логи
railway logs -f
```

## Итого

✅ **Правильная конфигурация для Railway:**
- `Procfile` → `web: python railway_start.py` (webhook mode)
- `railway.json` → `numReplicas: 1`
- Railway Settings → Replicas = 1
- Env var `RAILWAY_STATIC_URL` предоставляется автоматически

❌ **Неправильная конфигурация:**
- Несколько реплик (replicas > 1)
- Polling mode (`bot.main`) на Railway
- Несколько активных деплойментов одновременно
