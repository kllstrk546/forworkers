import asyncio
from telethon import TelegramClient
from config import get_settings

async def main():
    settings = get_settings()
    client = TelegramClient(settings.session_name, settings.api_id, settings.api_hash)
    
    print("Начинаем авторизацию парсера...")
    await client.start()
    print(f"Готово! Файл {settings.session_name}.session успешно создан.")
    print("Теперь можно запускать main.py")

if __name__ == '__main__':
    asyncio.run(main())
