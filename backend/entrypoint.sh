#!/bin/bash
set -Eeuo pipefail

echo "=========================================================="
echo "🚀 Coffee Chain Inventory & Order System: Starting Backend"
echo "=========================================================="

# 1. Wait for PostgreSQL
echo "⏳ Waiting for PostgreSQL database to accept connections..."
python -c "
import asyncio, os, sys
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def check():
    engine = create_async_engine(settings.ASYNC_DATABASE_URL)
    try:
        for i in range(1, 31):
            try:
                async with engine.connect():
                    print(f'✅ Database is ready and reachable! (attempt {i})')
                    return
            except Exception as exc:
                print(f'⏳ Database not ready yet (attempt {i}/30): {exc}')
                await asyncio.sleep(2)
        print('❌ Database connection timed out after 60 seconds.')
        sys.exit(1)
    finally:
        await engine.dispose()

asyncio.run(check())
"

# 2. Run Alembic migrations. A broken migration must fail the deployment.
echo "🔄 Applying Alembic database migrations..."
alembic upgrade head
echo "✅ Schema verified and up to date."

# 3. Seed only a brand-new catalog, using the non-destructive seed helper.
if [ "${AUTO_SEED:-true}" = "true" ]; then
  echo "🌱 Checking database seed state..."
  python -c "
import asyncio
import os
from app.core.database import engine
from app.db.seed_data import seed_database

async def main():
    try:
        await seed_database(initial_qty=float(os.getenv('INITIAL_STOCK_QTY', '50')))
    finally:
        await engine.dispose()

asyncio.run(main())
"
else
  echo "ℹ️ AUTO_SEED is disabled; skipping initial catalog seed."
fi

# 4. Graceful termination handler
cleanup() {
    echo "🛑 Received termination signal. Gracefully shutting down worker processes..."
    if [ -n "${BOT_PID:-}" ]; then
        kill -TERM "$BOT_PID" 2>/dev/null || true
    fi
    if [ -n "${UVICORN_PID:-}" ]; then
        kill -TERM "$UVICORN_PID" 2>/dev/null || true
    fi
    wait 2>/dev/null || true
    echo "👋 Shutdown complete."
}

trap 'cleanup; exit 0' SIGTERM SIGINT

# 5. Start FastAPI server
PORT="${PORT:-8000}"
WEB_CONCURRENCY="${WEB_CONCURRENCY:-1}"
echo "🌐 Starting FastAPI HTTP server on port $PORT..."
uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --workers "$WEB_CONCURRENCY" &
UVICORN_PID=$!

# 6. Start Telegram Bot Runner (if token is configured)
BOT_TOKEN_VALUE="${TELEGRAM_BOT_TOKEN:-$BOT_TOKEN}"
if [ -n "$BOT_TOKEN_VALUE" ] && [ "${BOT_ENABLED:-true}" = "true" ]; then
    echo "🤖 Starting Telegram Bot polling runner..."
    python -m app.bot.runner &
    BOT_PID=$!
else
    echo "ℹ️ Telegram bot worker is disabled or no token is configured."
fi

# 7. If either critical process exits, stop the container so Railway can
# restart it instead of reporting a healthy API while the bot is dead.
if [ -n "${BOT_PID:-}" ]; then
    set +e
    wait -n "$UVICORN_PID" "$BOT_PID"
    EXIT_CODE=$?
    set -e
    echo "❌ A backend process exited with code $EXIT_CODE; stopping its sibling."
    cleanup
    if [ "$EXIT_CODE" -eq 0 ]; then
        exit 1
    fi
    exit "$EXIT_CODE"
fi

wait "$UVICORN_PID"
