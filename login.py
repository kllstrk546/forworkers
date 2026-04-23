import asyncio

from telethon import TelegramClient
from telethon.sessions import StringSession

from config import get_settings


async def main() -> None:
    settings = get_settings()
    client = TelegramClient(StringSession(), settings.api_id, settings.api_hash)

    print("Начинаем авторизацию парсера...")
    await client.start()
    print("Готово! Скопируйте значение ниже в TELETHON_SESSION_STRING на Scalingo:")
    print(client.session.save())
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
