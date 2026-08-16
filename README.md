# ☕ Coffee Chain Inventory & Order Management System

Комплексная система управления складскими запасами, приёмки поставок и оформления заказов для сети кофеен:
- **FastAPI Backend** (SQLAlchemy 2.0 asyncpg, Alembic, Pydantic v2, RapidFuzz)
- **Telegram Bot (Aiogram 3)** — интерфейс для бариста и кладовщиков / администраторов
- **Telegram Mini App (TWA)** — реактивный интерфейс на React 18 + Vite + TailwindCSS
- **Vision LLM OCR Module** — распознавание накладных/чеков (Google Gemini 2.5 Flash / OpenAI GPT-4o-mini)
- **Nginx Reverse Proxy & PostgreSQL 16** — полная контейнеризация для продакшн-деплоя.

---

## ⚡ Быстрый запуск проекта в 3 команды (Docker Compose)

```bash
# 1. Скопируйте шаблон переменных окружения
cp .env.example .env

# 2. Укажите ваши токены в файле .env (BOT_TOKEN, WAREHOUSE_CHAT_ID, AI_API_KEY)
nano .env

# 3. Запустите весь продакшн-стек в Docker
docker compose up -d --build
```

После запуска контейнеров:
- **Telegram Mini App & Веб-интерфейс**: `http://localhost` (или ваш настроенный HTTPS-домен)
- **Интерактивная документация API (Swagger UI)**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **База данных PostgreSQL**: `localhost:5432` (миграции и сид 225 товаров применяются автоматически).

---

## 🚂 Деплой на Railway (Cloud Deployment)

Проект полностью оптимизирован для быстрого деплоя в облаке [Railway](https://railway.app):
- Поддерживает автоматический билд через `railway.toml` и `Dockerfile`.
- Динамически адаптируется к переменной `PORT`, внедряемой Railway.
- Поддерживает раздельный или совместный деплой бэкенда и Mini App с бесплатным автоматическим HTTPS.

Подробное пошаговое руководство с настройкой переменных окружения доступно в файле **[`RAILWAY_DEPLOY.md`](file:///Users/novikov/Documents/AI%20application%20bot/RAILWAY_DEPLOY.md)**.

---

## 🏗 Архитектура Docker-окружения

```
                      ┌────────────────────────────────────────┐
                      │              Internet / DNS            │
                      └───────────────────┬────────────────────┘
                                          │ (Ports 80, 443)
                                          ▼
                      ┌────────────────────────────────────────┐
                      │              nginx-proxy               │
                      │  - Let's Encrypt SSL / Certbot         │
                      │  - HTTP -> HTTPS Redirect              │
                      └──────────────┬──────────────────┬──────┘
                                     │ /api/*           │ /*
                                     ▼                  ▼
┌──────────────────────────────────────────────┐   ┌──────────────────────────────┐
│                   backend                    │   │           frontend           │
│ - FastAPI HTTP Server (Port 8000)            │   │ - React + Vite SPA Bundle    │
│ - Aiogram 3 Bot Polling Worker               │   │ - Nginx Static Distribution  │
│ - Alembic Migrations & Auto-Seed on Startup  │   │   (Multi-stage build)        │
│ - Vision LLM OCR & RapidFuzz Reconcile       │   └──────────────────────────────┘
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│                   postgres                   │
│ - PostgreSQL 16 Alpine                       │
│ - Persistent Volume `pg_data`                │
│ - Healthcheck readiness probe                │
└──────────────────────────────────────────────┘
```

1. **`docker/Dockerfile.backend`**:
   - Образ на базе `python:3.11-slim`.
   - Автоматически запускает [`docker/entrypoint.sh`](file:///Users/novikov/Documents/AI%20application%20bot/docker/entrypoint.sh): ожидает готовность PostgreSQL, применяет миграции `alembic upgrade head`, проверяет наличие данных и автоматически сидит каталог товаров (225 позиций), после чего запускает сервер FastAPI и воркер бота Aiogram.
2. **`docker/Dockerfile.frontend`**:
   - Multi-stage build (`node:20-alpine` для компиляции TypeScript/Vite $\rightarrow$ `nginx:alpine` для отдачи оптимизированной статики и роутинга SPA).
3. **`docker-compose.yml`**:
   - Оркестрация сервисов `postgres`, `backend`, `frontend`, `nginx-proxy`.
4. **`docker/nginx/default.conf`**:
   - Проксирование API-запросов (`/api/`), документации (`/docs`), раздача Mini App и поддержка выпуска SSL-сертификатов Let's Encrypt / Certbot.

---

## 🔑 Переменные окружения (`.env`)

| Переменная | Описание | Пример |
|---|---|---|
| `POSTGRES_USER` | Пользователь БД PostgreSQL | `postgres` |
| `POSTGRES_PASSWORD` | Пароль к базе данных | `your_secure_db_password` |
| `POSTGRES_DB` | Имя базы данных | `coffee_db` |
| `DATABASE_URL` | Строка подключения к базе данных | `postgresql+asyncpg://postgres:pass@postgres:5432/coffee_db` |
| `BOT_TOKEN` / `TELEGRAM_BOT_TOKEN` | Токен Telegram-бота от @BotFather | `123456789:ABCdefGHIjkl...` |
| `WAREHOUSE_CHAT_ID` / `TELEGRAM_WAREHOUSE_CHAT_ID` | ID чата склада для уведомлений о заказах | `-1001234567890` |
| `MINI_APP_URL` / `WEBAPP_URL` | URL Telegram WebApp (HTTPS для продакшна) | `https://coffee.yourdomain.com` |
| `ADMIN_TELEGRAM_IDS` | Telegram ID админов/кладовщиков (через запятую) | `123456789,987654321` |
| `OCR_PROVIDER` | Провайдер Vision LLM (`gemini` или `openai`) | `gemini` |
| `OCR_MODEL` | Модель Vision LLM | `gemini-2.5-flash` / `gpt-4o-mini` |
| `AI_API_KEY` / `GEMINI_API_KEY` | API-ключ Google Gemini / OpenAI | `AIzaSy...` |

---

## 📸 Модуль оцифровки накладных поставок по фотографии

Модуль предназначен для автоматической приёмки товаров от поставщиков с защитой доступа **только для администраторов/кладовщиков**:

1. **Контроль доступа**:
   - Проверка по `ADMIN_TELEGRAM_IDS` через кастомный фильтр [`IsAdminFilter`](file:///Users/novikov/Documents/AI%20application%20bot/app/bot/filters/admin.py).
   - Обычные пользователи получают отказ: `⛔ У вас нет доступа к приёмке накладных и управлению складом`.
2. **Vision LLM (Gemini 2.5 Flash / GPT-4o-mini)**:
   - Анализ фото чека, накладной, ТОРГ-12 или УПД.
   - Извлечение товарных позиций, единиц измерения и количества со строгой валидацией по Pydantic-схеме.
3. **Fuzzy Matching со складом (RapidFuzz)**:
   - Интеллектуальное сопоставление со 195+ товарами номенклатуры.
   - Схожесть $\ge 85\%$: автоматическая привязка к товару склада (`✅`).
   - Схожесть $< 85\%$: пометка флагом `is_uncertain = True` с подсказкой наиболее похожего товара (`❓`).
4. **Зачисление на баланс склада**:
   - Сохранение черновика в статусе `draft`.
   - По нажатию кнопки `[ ✅ Зачислить на склад ]`: транзакционное увеличение `stocks.real_qty += item.quantity`, перевод статуса накладной в `confirmed` и выход позиций из стоп-листа.

---

## 💻 Локальная разработка без Docker

### 1. Подготовка бэкенда
```bash
# Создание виртуального окружения
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Настройка окружения
cp .env.example .env

# Применение миграций и сидинг БД
alembic upgrade head
python -m app.cli.seed

# Запуск API сервера
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Запуск Telegram-бота (в отдельном терминале)
python -m app.bot.runner
```

### 2. Подготовка фронтенда
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Запуск автоматических тестов

В проекте настроен расширенный набор из 37 асинхронных тестов, проверяющих:
- Атомарное бронирование остатков и полное исключение оверселла при конкурентных заказах.
- Жизненный цикл заказов (сборка, отгрузка, отмена, расчет стоп-листа).
- Оцифровку накладных через OCR, нечёткое сопоставление RapidFuzz и разграничение прав доступа `IsAdminFilter`.

```bash
.venv/bin/pytest -v
```

```text
============================== 37 passed in 1.53s ==============================
```
