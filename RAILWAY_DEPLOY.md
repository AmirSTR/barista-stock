# Деплой на Railway

Репозиторий подготовлен как isolated monorepo: один Railway-проект содержит managed PostgreSQL и два сервиса из одного GitHub-репозитория.

## 1. Создайте проект и сервисы

1. В Railway создайте **Empty Project**.
2. Добавьте **PostgreSQL**.
3. Дважды добавьте один и тот же GitHub-репозиторий и назовите сервисы `backend` и `frontend`.
4. Для `backend` задайте:
   - **Root Directory**: `/backend`
   - **Config File Path**: `/backend/railway.toml`
5. Для `frontend` задайте:
   - **Root Directory**: `/frontend`
   - **Config File Path**: `/frontend/railway.toml`
6. В **Networking** сгенерируйте публичный домен для обоих сервисов.

Dockerfile, watch paths, restart policy и healthchecks уже описаны в per-service `railway.toml`.

## 2. Переменные backend

Добавьте в `backend`:

| Переменная | Значение |
|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
| `DEBUG` | `false` |
| `CORS_ORIGINS` | `https://${{frontend.RAILWAY_PUBLIC_DOMAIN}}` |
| `MINI_APP_URL` | `https://${{frontend.RAILWAY_PUBLIC_DOMAIN}}` |
| `BOT_TOKEN` | токен от BotFather |
| `BOT_ENABLED` | `true` |
| `WAREHOUSE_CHAT_ID` | ID складского чата; переменную можно не создавать |
| `ADMIN_TELEGRAM_IDS` | ID через запятую, например `12345,67890` |
| `TELEGRAM_AUTH_REQUIRED` | `true` |
| `TELEGRAM_INIT_DATA_TTL_SECONDS` | `86400` |
| `API_ADMIN_TOKEN` | случайный секрет минимум 32 байта |
| `AUTO_SEED` | `true` для первого запуска; затем можно сменить на `false` |
| `INITIAL_STOCK_QTY` | `50` или нужный стартовый остаток |

Сгенерировать `API_ADMIN_TOKEN` локально можно командой `openssl rand -hex 32`. Не добавляйте его во frontend: это серверный административный секрет.

OCR через Gemini:

| Переменная | Значение |
|---|---|
| `OCR_PROVIDER` | `gemini` |
| `OCR_MODEL` | `gemini-2.5-flash` |
| `GEMINI_API_KEY` | ключ Gemini |
| `OCR_DEMO_MODE` | `false` |

Для OpenAI используйте `OCR_PROVIDER=openai`, `OCR_MODEL=gpt-4o-mini` и именно `OPENAI_API_KEY`.

Не создавайте `PORT`: Railway внедряет его автоматически. Пока API и Telegram polling работают в одном контейнере, оставьте у backend **ровно одну replica**, иначе Telegram получит несколько polling-процессов.

## 3. Переменные frontend

Добавьте в `frontend`:

| Переменная | Значение |
|---|---|
| `VITE_API_URL` | `https://${{backend.RAILWAY_PUBLIC_DOMAIN}}` |
| `VITE_ENABLE_MOCKS` | `false` |

`VITE_API_URL` используется во время Docker build. Dockerfile намеренно останавливает сборку, если переменная отсутствует, чтобы не задеплоить UI, отправляющий `/api` в собственный Nginx.

## 4. Telegram и проверка

1. В BotFather укажите HTTPS-домен frontend как URL Mini App.
2. Перезапустите оба сервиса после добавления переменных.
3. Проверьте:
   - `https://<backend>/health` → `{"status":"healthy"}`;
   - `https://<frontend>/health` → `ok`;
   - Mini App открывается из кнопки бота;
   - заказ создаётся и появляется в складском чате;
   - в логах backend успешно прошли Alembic и безопасный seed.

Административный REST-вызов должен передавать ключ:

```bash
curl -H "X-API-Key: $API_ADMIN_TOKEN" \
  "https://<backend>/api/orders"
```

## Что делает startup backend

1. ждёт PostgreSQL;
2. выполняет `alembic upgrade head` с fail-fast;
3. при `AUTO_SEED=true` заполняет только пустой каталог (255 позиций), не очищая существующие данные;
4. запускает Uvicorn и, если настроен токен, Telegram polling;
5. завершает контейнер, если API или бот аварийно остановился, чтобы Railway применил restart policy.

Официальные справки Railway: [isolated monorepo](https://docs.railway.com/deployments/monorepo), [config as code](https://docs.railway.com/config-as-code/reference), [variables](https://docs.railway.com/variables/reference), [healthchecks](https://docs.railway.com/deployments/healthchecks), [PostgreSQL](https://docs.railway.com/databases/postgresql).
