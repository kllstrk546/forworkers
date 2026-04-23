import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import get_settings
from handlers.add import router as add_router
from handlers.leads import router as leads_router
from handlers.start import router as start_router
from sheets import init_sheet
from parser import background_parser  # <-- Импортируем наш парсер


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    settings = get_settings()
    worksheet = init_sheet(settings)

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(add_router)
    dp.include_router(leads_router)

    # <-- Создаем фоновую задачу для парсера перед запуском бота
    asyncio.create_task(background_parser(settings, worksheet))

    await dp.start_polling(bot, worksheet=worksheet)


if __name__ == "__main__":
    asyncio.run(main())
