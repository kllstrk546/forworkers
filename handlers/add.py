import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from gspread import Worksheet
from gspread.exceptions import GSpreadException

from keyboards import (
    ADD_LEAD_BUTTON,
    CANCEL_ADD_LEAD,
    CONFIRM_ADD_LEAD,
    add_lead_confirmation_keyboard,
    main_menu_keyboard,
)
from sheets import add_lead_if_not_duplicate
from workers import get_worker_name


router = Router()
logger = logging.getLogger(__name__)


class AddLead(StatesGroup):
    instagram = State()
    phone = State()
    business_type = State()
    confirmation = State()


def get_clean_text(message: Message) -> str | None:
    if not message.text:
        return None

    text = message.text.strip()
    return text or None


async def start_add_lead(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AddLead.instagram)
    await message.answer("Введите Instagram аккаунт лида:")


@router.message(Command("add"))
async def add_lead_command(message: Message, state: FSMContext) -> None:
    await start_add_lead(message, state)


@router.message(F.text == ADD_LEAD_BUTTON)
async def add_lead_button(message: Message, state: FSMContext) -> None:
    await start_add_lead(message, state)


@router.message(AddLead.instagram)
async def process_instagram(message: Message, state: FSMContext) -> None:
    instagram = get_clean_text(message)

    if not instagram:
        await message.answer("Instagram аккаунт не может быть пустым. Введите значение:")
        return

    await state.update_data(instagram=instagram)
    await state.set_state(AddLead.phone)
    await message.answer("Введите номер телефона:")


@router.message(AddLead.phone)
async def process_phone(message: Message, state: FSMContext) -> None:
    phone = get_clean_text(message)

    if not phone:
        await message.answer("Номер телефона не может быть пустым. Введите значение:")
        return

    await state.update_data(phone=phone)
    await state.set_state(AddLead.business_type)
    await message.answer("Введите тип бизнеса:")


@router.message(AddLead.business_type)
async def process_business_type(message: Message, state: FSMContext) -> None:
    business_type = get_clean_text(message)

    if not business_type:
        await message.answer("Тип бизнеса не может быть пустым. Введите значение:")
        return

    await state.update_data(business_type=business_type)
    data = await state.get_data()

    await state.set_state(AddLead.confirmation)
    await message.answer(
        "Проверьте данные лида:\n\n"
        f"Instagram: {data['instagram']}\n"
        f"Телефон: {data['phone']}\n"
        f"Тип бизнеса: {data['business_type']}",
        reply_markup=add_lead_confirmation_keyboard(),
    )


@router.callback_query(AddLead.confirmation, F.data == CANCEL_ADD_LEAD)
async def cancel_add_lead(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Добавление лида отменено.",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(AddLead.confirmation, F.data == CONFIRM_ADD_LEAD)
async def confirm_add_lead(
    callback: CallbackQuery,
    state: FSMContext,
    worksheet: Worksheet,
) -> None:
    data = await state.get_data()

    instagram = data.get("instagram")
    phone = data.get("phone")
    business_type = data.get("business_type")

    if not instagram or not phone or not business_type:
        await state.clear()
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            "Не хватает данных лида. Запустите добавление заново.",
            reply_markup=main_menu_keyboard(),
        )
        await callback.answer()
        return

    try:
        is_added = add_lead_if_not_duplicate(
            worksheet=worksheet,
            worker=get_worker_name(callback.from_user),
            instagram=instagram,
            phone=phone,
            business_type=business_type,
        )
    except GSpreadException:
        logger.exception("Google Sheets error while adding lead")
        await state.clear()
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            "Не удалось сохранить лид в Google Sheets. Попробуйте позже.",
            reply_markup=main_menu_keyboard(),
        )
        await callback.answer()
        return

    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)

    if not is_added:
        await callback.message.answer(
            "❌ Стоп! Этот лид уже есть в базе. Попробуй найти другого.",
            reply_markup=main_menu_keyboard(),
        )
        await callback.answer()
        return

    await callback.message.answer(
        "Лид добавлен в Google Sheets.",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()
