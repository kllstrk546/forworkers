# Telegram Lead Bot

Бот на Python 3.11+, aiogram 3 и gspread для работы с лидами в Google Sheets.

## Установка

1. Создайте виртуальное окружение:

```bash
python -m venv .venv
```

2. Активируйте окружение.

Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

3. Установите зависимости:

```bash
pip install -r requirements.txt
```

## .env

Создайте файл `.env` в корне проекта:

```env
BOT_TOKEN=your_telegram_bot_token
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json
GOOGLE_SERVICE_ACCOUNT_JSON=
GOOGLE_SHEET_NAME=your_google_sheet_name
API_ID=your_telegram_api_id
API_HASH=your_telegram_api_hash
SESSION_NAME=parser_session
TELETHON_SESSION_STRING=
```

Переменные:

- `BOT_TOKEN` - токен Telegram-бота из BotFather.
- `GOOGLE_SERVICE_ACCOUNT_FILE` - путь к JSON-файлу service account.
- `GOOGLE_SERVICE_ACCOUNT_JSON` - JSON service account одной строкой для деплоя.
- `GOOGLE_SHEET_NAME` - название Google Sheets таблицы.
- `API_ID` и `API_HASH` - данные Telegram API для Telethon.
- `SESSION_NAME` - имя локального файла сессии Telethon.
- `TELETHON_SESSION_STRING` - строковая сессия Telethon для деплоя.

Для локального запуска можно использовать `GOOGLE_SERVICE_ACCOUNT_FILE`.
Для Scalingo удобнее использовать `GOOGLE_SERVICE_ACCOUNT_JSON`.

## Google Service Account

1. Создайте service account в Google Cloud.
2. Скачайте JSON-ключ service account.
3. Положите JSON-файл в проект или укажите полный путь к нему в `.env`.
4. Откройте Google Sheets таблицу и дайте доступ email-адресу service account.
5. Убедитесь, что название таблицы совпадает с `GOOGLE_SHEET_NAME`.

При первом запуске бот проверит первый лист таблицы. Если таблица пустая, будут созданы заголовки:

- Дата
- Воркер
- Instagram
- Телефон
- Ник в ТГ
- Тип бизнеса
- Статус

## Запуск бота

```bash
python main.py
```

Бот работает через long polling.

## Основные действия

- `/start` - показать главное меню.
- `➕ Добавить лида` или `/add` - запустить сценарий добавления лида.
- `🎯 Дать лид для написания` - получить доступный лид своего воркера.

Воркер определяется по Telegram username. Если username нет, используется `user_<telegram_id>`.

## Подготовка Telethon session string

Для облачного деплоя нельзя полагаться на локальный `.session` файл. Сгенерируйте строковую сессию:

```bash
python login.py
```

После авторизации скопируйте выведенное значение в переменную окружения `TELETHON_SESSION_STRING`.

## Деплой на Scalingo

Проект подготовлен к запуску как worker-процесс.

Файлы для деплоя:

- `Procfile`
- `runtime.txt`
- `requirements.txt`

Минимальные переменные окружения на Scalingo:

```env
BOT_TOKEN=your_telegram_bot_token
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
GOOGLE_SHEET_NAME=your_google_sheet_name
API_ID=your_telegram_api_id
API_HASH=your_telegram_api_hash
TELETHON_SESSION_STRING=your_telethon_session_string
```

После деплоя включите worker:

```bash
scalingo --app your-app-name scale worker:1
```

Бот работает через long polling, поэтому отдельный web-процесс не нужен.
