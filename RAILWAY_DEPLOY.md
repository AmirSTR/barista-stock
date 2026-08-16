# 🚂 Деплой проекта на Railway (Пошаговое руководство)

Данное руководство описывает развертывание полного стека системы управления запасами кофейни на облачной платформе **[Railway](https://railway.app)**.

---

## 🏗 Архитектура деплоя на Railway

В Railway проект может быть запущен в двух вариантах:
1. **Единый сервис (Monolith Backend + Bot + Static Frontend)**: FastAPI отдает API, бота в фоне и скомпилированный фронтенд.
2. **Раздельные сервисы (Рекомендуется для высокой нагрузки)**:
   - **PostgreSQL Database** (Railway Plugin)
   - **Backend Web Service** (FastAPI API + Bot Polling Worker)
   - **Frontend Static / Docker Service** (Telegram Mini App)

---

## 📋 Шаг 1: Подготовка репозитория

Убедитесь, что все файлы проекта закоммичены в ваш GitHub репозиторий:
```bash
git add .
git commit -m "Deploy to Railway"
git push origin main
```

---

## 🗄 Шаг 2: Создание проекта и базы данных PostgreSQL

1. Зайдите в панель [Railway Dashboard](https://railway.app/dashboard).
2. Нажмите **New Project** $\rightarrow$ **Provision PostgreSQL**.
3. Railway создаст управляемый инстанс PostgreSQL 16.
4. Перейдите во вкладку **Variables** базы данных и скопируйте `DATABASE_URL`.

---

## ⚙️ Шаг 3: Развертывание Backend сервиса

1. В вашем проекте Railway нажмите **New** $\rightarrow$ **GitHub Repo** $\rightarrow$ выберите ваш репозиторий.
2. Railway автоматически обнаружит `Dockerfile` в [`docker/Dockerfile.backend`](file:///Users/novikov/Documents/AI application bot/docker/Dockerfile.backend) или `railway.toml`.
3. В настройках сервиса (**Settings**):
   - **Build**: `Dockerfile Path` $\rightarrow$ `docker/Dockerfile.backend`
   - **Networking**: Нажмите **Generate Domain** (получите публичный URL, например `https://barista-backend.up.railway.app`).
4. Во вкладке **Variables** добавьте следующие переменные:

| Переменная | Значение / Описание |
|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (Railway подставит автоматически) |
| `POSTGRES_USER` | `${{Postgres.POSTGRES_USER}}` |
| `POSTGRES_PASSWORD` | `${{Postgres.POSTGRES_PASSWORD}}` |
| `POSTGRES_DB` | `${{Postgres.POSTGRES_DB}}` |
| `POSTGRES_SERVER` | `${{Postgres.POSTGRES_HOST}}` |
| `POSTGRES_PORT` | `${{Postgres.POSTGRES_PORT}}` |
| `BOT_TOKEN` | Ваш токен бота от @BotFather (например: `123456:ABC-DEF...`) |
| `TELEGRAM_BOT_TOKEN` | Тот же токен бота |
| `WAREHOUSE_CHAT_ID` | Telegram ID склада (например: `-1001234567890`) |
| `TELEGRAM_WAREHOUSE_CHAT_ID` | Тот же ID склада |
| `ADMIN_TELEGRAM_IDS` | Telegram ID админов/кладовщиков через запятую (`123456789,987654321`) |
| `OCR_PROVIDER` | `gemini` (или `openai`) |
| `OCR_MODEL` | `gemini-2.5-flash` (или `gpt-4o-mini`) |
| `AI_API_KEY` | Ваш API-ключ Gemini / OpenAI |
| `GEMINI_API_KEY` | Ваш API-ключ Gemini |
| `MINI_APP_URL` | Публичный HTTPS URL фронтенда (см. Шаг 4) |
| `WEBAPP_URL` | Публичный HTTPS URL фронтенда |

> [!NOTE]
> При старте контейнера скрипт [`docker/entrypoint.sh`](file:///Users/novikov/Documents/AI application bot/docker/entrypoint.sh) автоматически применит миграции `alembic upgrade head`, проверит наличие товаров в БД и автоматически выполнит сидинг каталога из 225 позиций!

---

## 🎨 Шаг 4: Развертывание Frontend (Telegram Mini App)

1. В том же проекте Railway нажмите **New** $\rightarrow$ **GitHub Repo** $\rightarrow$ выберите тот же репозиторий.
2. В настройках сервиса (**Settings**):
   - Измените имя сервиса на `frontend`.
   - **Build**: `Dockerfile Path` $\rightarrow$ `docker/Dockerfile.frontend`
   - **Root Directory**: `/`
3. В **Networking**:
   - Нажмите **Generate Domain** (получите URL, например `https://barista-app.up.railway.app`).
4. Во вкладке **Variables** задайте:
   - `VITE_API_URL`: `https://barista-backend.up.railway.app` (URL бэкенда из Шага 3).
5. Обновите в бэкенде переменную `MINI_APP_URL` на полученный домен фронтенда (`https://barista-app.up.railway.app`).

---

## 🤖 Шаг 5: Настройка Telegram Bot (@BotFather)

1. Откройте диалог с **@BotFather** в Telegram.
2. Отправьте `/mybots` $\rightarrow$ выберите вашего бота.
3. **Bot Settings** $\rightarrow$ **Menu Button** $\rightarrow$ **Configure menu button**:
   - Отправьте URL вашего Frontend сервиса: `https://barista-app.up.railway.app`.
   - Укажите текст кнопки: `☕ Сделать заказ`.
4. (Опционально) Настройте описание бота и команды:
   ```text
   start - Главное меню и запуск приложения
   stoplist - Просмотр дефицитных позиций (для бариста)
   admin_stoplist - Управление стоп-листом (для склада)
   supply - Приёмка поставки по накладной (для склада)
   orders - Управление заказами кофеен (для склада)
   help - Справка по работе с ботом
   ```

---

## ✅ Проверка работоспособности

1. Откройте `https://barista-backend.up.railway.app/docs` — откроется интерактивный Swagger UI.
2. Откройте бота в Telegram и отправьте команду `/start` — появится приветствие и кнопка WebApp.
3. Нажмите кнопку WebApp или перейдите по ссылке `https://barista-app.up.railway.app` — загрузится интерактивный каталог кофе, сиропов, молока и хозтоваров.
