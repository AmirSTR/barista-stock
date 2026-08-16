# Coffee Chain Inventory

Система складского учёта и заказов для сети кофеен:

- FastAPI + PostgreSQL + Alembic;
- Telegram-бот на Aiogram;
- Telegram Mini App на React/Vite;
- OCR накладных через Gemini или OpenAI.

## Структура

```text
.
├── backend/                 # самостоятельный Python-сервис
│   ├── app/
│   ├── alembic/
│   ├── tests/
│   ├── Dockerfile
│   ├── entrypoint.sh
│   └── railway.toml
├── frontend/                # самостоятельный React/Nginx-сервис
│   ├── src/
│   ├── Dockerfile
│   ├── nginx.conf.template
│   └── railway.toml
├── docker-compose.yml       # локальный стек
└── RAILWAY_DEPLOY.md
```

`backend` и `frontend` имеют отдельные build context, Dockerfile, healthcheck и Railway config. Это позволяет Railway пересобирать только изменившийся сервис.

## Локальный запуск

```bash
cp .env.example .env
docker compose up --build
```

После запуска:

- frontend: http://localhost:8080
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- healthcheck: http://localhost:8000/health

Без `BOT_TOKEN` API запускается без Telegram polling. Для локального браузерного режима в шаблоне отключена проверка Telegram `initData`; на Railway её необходимо включить.

## Разработка без Docker

Backend:

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp ../.env.example .env
alembic upgrade head
python -m app.db.seed_data
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm ci
VITE_API_URL=http://localhost:8000 npm run dev
```

## Проверки

```bash
(cd backend && .venv/bin/pytest -q)
(cd frontend && npm run build)
bash -n backend/entrypoint.sh
docker compose config
```

## Защита production API

- создание заказа требует валидный заголовок `X-Telegram-Init-Data`, полученный из `Telegram.WebApp.initData`;
- административные изменения требуют `X-API-Key`, совпадающий с серверной переменной `API_ADMIN_TOKEN`;
- mock-каталог, fake-заказы и demo OCR выключены по умолчанию;
- CORS ограничивается переменной `CORS_ORIGINS`.

Подробная инструкция: [RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md).
