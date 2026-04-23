from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards import main_menu_keyboard


router = Router()


@router.message(CommandStart())
async def start_command(message: Message) -> None:
    await message.answer(
        "Привет! Я бот для работы с лидами.\n\n"
        "Я умею добавлять новых лидов в таблицу и выдавать готовых лидов "
        "для написания.",
        reply_markup=main_menu_keyboard(),
    )
