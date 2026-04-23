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
GOOGLE_SHEET_NAME=your_google_sheet_name
```

Переменные:

- `BOT_TOKEN` - токен Telegram-бота из BotFather.
- `GOOGLE_SERVICE_ACCOUNT_FILE` - путь к JSON-файлу service account.
- `GOOGLE_SHEET_NAME` - название Google Sheets таблицы.

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
