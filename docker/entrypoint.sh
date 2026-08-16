#!/bin/bash
set -e

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
    for i in range(1, 31):
        try:
            async with engine.connect() as conn:
                print(f'✅ Database is ready and reachable! (attempt {i})')
                return True
        except Exception as e:
            print(f'⏳ Database not ready yet (attempt {i}/30): {e}')
            await asyncio.sleep(2)
    print('❌ Database connection timed out after 60 seconds.')
    sys.exit(1)

asyncio.run(check())
"

# 2. Run Alembic Migrations & Ensure Schema
echo "🔄 Applying Alembic database migrations..."
alembic upgrade head || true
python -c "
import asyncio
from app.core.database import engine
from app.models.base import Base

async def init_schema():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

asyncio.run(init_schema())
"
echo "✅ Schema verified and up to date."

# 3. Check and Auto-Seed Database if empty
echo "🌱 Checking database seed state..."
python -c "
import asyncio
from sqlalchemy import select, func
from app.core.database import async_session_maker
from app.models.product import Product
from app.cli.seed import seed_database

async def auto_seed():
    async with async_session_maker() as session:
        res = await session.execute(select(func.count(Product.id)))
        count = res.scalar() or 0
        if count == 0:
            print('📦 Database is empty. Seeding catalog items, sample bars, and stock records...')
            await seed_database(initial_qty=50.0, create_sample_bars=True, session=session)
            print('✅ Initial database seed completed.')
        else:
            print(f'✅ Database already populated ({count} products found). Skipping seed.')

asyncio.run(auto_seed())
"

# 4. Graceful termination handler
cleanup() {
    echo "🛑 Received termination signal. Gracefully shutting down worker processes..."
    if [ -n "$BOT_PID" ]; then
        kill -TERM "$BOT_PID" 2>/dev/null || true
    fi
    if [ -n "$UVICORN_PID" ]; then
        kill -TERM "$UVICORN_PID" 2>/dev/null || true
    fi
    wait
    echo "👋 Shutdown complete."
    exit 0
}

trap cleanup SIGTERM SIGINT

# 5. Start FastAPI server
PORT="${PORT:-8000}"
echo "🌐 Starting FastAPI HTTP server on port $PORT..."
uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --workers 2 &
UVICORN_PID=$!

# 6. Start Telegram Bot Runner (if token is configured)
BOT_TOKEN_VALUE="${TELEGRAM_BOT_TOKEN:-$BOT_TOKEN}"
if [ -n "$BOT_TOKEN_VALUE" ]; then
    echo "🤖 Starting Telegram Bot polling runner (supervised)..."
    (
        while true; do
            python -m app.bot.runner || true
            echo "⚠️ Telegram bot worker exited. Restarting in 5s..."
            sleep 5
        done
    ) &
    BOT_PID=$!
else
    echo "⚠️ TELEGRAM_BOT_TOKEN / BOT_TOKEN is not configured. Telegram bot worker is disabled."
fi

# 7. Wait on Uvicorn web server
wait "$UVICORN_PID"
