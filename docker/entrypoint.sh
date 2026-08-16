#!/bin/bash
set -e

echo "========================================="
echo "☕ Starting Coffee Chain Management App"
echo "========================================="

# 1. Wait for database readiness
if [ -n "$POSTGRES_SERVER" ]; then
    echo "⏳ Waiting for PostgreSQL at $POSTGRES_SERVER:${POSTGRES_PORT:-5432}..."
    while ! nc -z "$POSTGRES_SERVER" "${POSTGRES_PORT:-5432}"; do
        sleep 0.5
    done
    echo "✅ PostgreSQL is ready and accepting connections."
fi

# 2. Run Alembic Database Migrations
echo "🔄 Running Alembic migrations (upgrade head)..."
alembic upgrade head
echo "✅ Migrations completed successfully."

# 3. Seed database with initial catalog if empty
echo "🌱 Checking and seeding initial catalog data (225 items)..."
python -m app.cli.seed || echo "⚠️ Seed script completed or skipped (data may already exist)."

# 4. Determine execution mode
# If RAILWAY or WEB_ONLY is set, we run Uvicorn and start bot in background task if configured
echo "🚀 Launching Application Services..."

if [ "$1" = "bot" ]; then
    echo "🤖 Starting Telegram Bot worker..."
    exec python -m app.bot.runner
elif [ "$1" = "api" ]; then
    echo "🌐 Starting FastAPI HTTP server on port ${PORT:-8000}..."
    exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
else
    # Default combined mode: Run Bot in background, Uvicorn in foreground
    if [ -n "$BOT_TOKEN" ] || [ -n "$TELEGRAM_BOT_TOKEN" ]; then
        echo "🤖 Starting Telegram Bot in background..."
        python -m app.bot.runner &
        BOT_PID=$!
        echo "✅ Bot started with PID $BOT_PID"
    else
        echo "ℹ️ No BOT_TOKEN provided, running API only."
    fi

    echo "🌐 Starting FastAPI HTTP server on port ${PORT:-8000}..."
    exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
fi
