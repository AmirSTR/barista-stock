# 🚂 Инструкция по деплою проекта на Railway

Пошаговое руководство по развертыванию полного стека (PostgreSQL 16, FastAPI Backend, Aiogram 3 Telegram Bot и React Vite Mini App) на облачной платформе [Railway](https://railway.app).

---

## 📋 Что будет развернуто

1. **PostgreSQL Plugin** — база данных с автоматическим `DATABASE_URL`.
2. **Backend Service** (FastAPI + Aiogram Bot Worker):
   - Автоматический прогон миграций Alembic (`alembic upgrade head`).
   - Автоматический сидинг каталога товаров (225 позиций) при первом запуске.
   - Обработка заказов и API эндпоинтов.
   - Фоновый воркер Telegram-бота.
   - Модуль оцифровки накладных поставок (Vision LLM + RapidFuzz).
3. **Frontend Service** (React 18 + Vite + TailwindCSS):
   - Telegram Mini App (TWA) для бариста.
   - Автоматический бесплатный HTTPS-домен с SSL-сертификатом для работы внутри Telegram.

---

## 🚀 Пошаговый план деплоя

### Шаг 1: Создание проекта на Railway
1. Авторизуйтесь на [railway.app](https://railway.app).
2. Нажмите **«+ New Project»** $\rightarrow$ **«Empty Project»**.

---

### Шаг 2: Добавление базы данных PostgreSQL
1. В проекте нажмите **«+ New»** $\rightarrow$ **«Database»** $\rightarrow$ **«Add PostgreSQL»**.
2. Railway создаст базу данных и автоматически добавит системную переменную `DATABASE_URL`.

---

### Шаг 3: Развертывание Backend-сервиса (API + Бот)
1. Нажмите **«+ New»** $\rightarrow$ **«GitHub Repo»** $\rightarrow$ выберите ваш репозиторий.
2. Перейдите во вкладку **Settings** созданного сервиса:
   - **Service Name**: переименуйте в `backend`.
   - **Build**: в разделе **Builder** выберите **Dockerfile** и укажите **Dockerfile Path**: `docker/Dockerfile.backend`.
3. Перейдите во вкладку **Variables** и добавьте следующие переменные:

| Переменная | Значение / Источник |
|---|---|
| `DATABASE_URL` | Нажмите **«Add Reference»** $\rightarrow$ выберите `Postgres` $\rightarrow$ `DATABASE_URL` |
| `BOT_TOKEN` | Токен бота от @BotFather (например `123456789:ABCdef...`) |
| `WAREHOUSE_CHAT_ID` | Telegram ID чата склада (например `-1001234567890`) |
| `ADMIN_TELEGRAM_IDS` | Telegram ID администраторов через запятую (например `123456789,987654321`) |
| `AI_API_KEY` | API ключ Google Gemini (`AIzaSy...`) или OpenAI |
| `OCR_PROVIDER` | `gemini` |
| `OCR_MODEL` | `gemini-2.5-flash` |
| `MINI_APP_URL` | URL фронтенда (настроим на следующем шаге) |

4. Перейдите во вкладку **Settings** $\rightarrow$ раздел **Networking** $\rightarrow$ нажмите **«Generate Domain»** (вы получите публичный URL вида `https://backend-production-xxxx.up.railway.app`).

---

### Шаг 4: Развертывание Frontend-сервиса (Telegram Mini App)
1. В том же проекте нажмите **«+ New»** $\rightarrow$ **«GitHub Repo»** $\rightarrow$ выберите тот же репозиторий.
2. Перейдите во вкладку **Settings**:
   - **Service Name**: переименуйте в `frontend`.
   - **Dockerfile Path**: укажите `docker/Dockerfile.frontend`.
3. Перейдите во вкладку **Variables** и добавьте:

| Переменная | Значение |
|---|---|
| `VITE_API_URL` | Публичный URL вашего бэкенда из Шага 3 (например `https://backend-production-xxxx.up.railway.app`) |

4. Перейдите в **Settings** $\rightarrow$ **Networking** $\rightarrow$ нажмите **«Generate Domain»** (вы получите публичный HTTPS-домен вида `https://frontend-production-yyyy.up.railway.app`).

---

### Шаг 5: Обновление URL в настройках бэкенда и Telegram-бота
1. В переменной `MINI_APP_URL` бэкенда обновите значение на полученный домен фронтенда (`https://frontend-production-yyyy.up.railway.app`).
2. В Telegram напишите боту [@BotFather](https://t.me/BotFather):
   - Отправьте команду `/setmenubutton`.
   - Выберите вашего бота.
   - Отправьте HTTPS-ссылку на фронтенд (`https://frontend-production-yyyy.up.railway.app`).
   - Укажите название кнопки меню: **«🛒 Сделать заказ»**.

---

## 🔍 Проверка работоспособности

1. **Проверка API Health**:
   - Откройте в браузере: `https://<ваш-бэкенд>/health` $\rightarrow$ ответ `{"status":"healthy"}`.
   - Swagger документация: `https://<ваш-бэкенд>/docs`.
2. **Проверка Telegram-бота**:
   - Отправьте `/start` боту в Telegram $\rightarrow$ бот предложит выбрать кофейню или сразу откроет меню Mini App.
3. **Проверка приёмки накладных (OCR)**:
   - Администратор (чей ID указан в `ADMIN_TELEGRAM_IDS`) отправляет боту фотографию накладной $\rightarrow$ бот распознает товары, создаст черновик и прикрепит кнопку `[ ✅ Зачислить на склад ]`.
