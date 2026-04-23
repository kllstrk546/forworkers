import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from gspread import Worksheet
from gspread.exceptions import GSpreadException

from keyboards import (
    GET_LEAD_BUTTON,
    MARK_NOT_IN_TELEGRAM_PREFIX,
    MARK_MANUAL_WRITTEN_PREFIX,
    MARK_WRITTEN_PREFIX,
    NEXT_LEAD_PREFIX,
    NEXT_MANUAL_LEAD_PREFIX,
    main_menu_keyboard,
    manual_lead_keyboard,
    next_available_lead_keyboard,
    ready_lead_keyboard,
)
from sheets import (
    Lead,
    get_next_lead_for_worker,
    get_next_manual_lead,
    mark_lead_as_not_in_telegram,
    mark_lead_as_written,
)
from workers import get_worker_name


router = Router()
logger = logging.getLogger(__name__)


def get_telegram_url(telegram_nick: str) -> str | None:
    if telegram_nick.startswith("@") and len(telegram_nick) > 1:
        return f"https://t.me/{telegram_nick[1:]}"

    return None


def get_telegram_display(telegram_nick: str, is_manual: bool = False) -> str:
    if is_manual:
        return "не найден"

    if telegram_nick.startswith("tg://user?id="):
        return f"Telegram ID: {telegram_nick.removeprefix('tg://user?id=')}"

    return telegram_nick


def lead_card(lead: Lead, is_manual: bool = False) -> str:
    telegram_nick = get_telegram_display(lead.telegram_nick, is_manual)

    return (
        "Лид для написания:\n\n"
        f"Instagram: {lead.instagram}\n"
        f"Телефон: {lead.phone}\n"
        f"Ник в ТГ: {telegram_nick}\n"
        f"Тип бизнеса: {lead.business_type}\n"
        f"Статус: {lead.status}"
    )


def get_row_number(callback_data: str | None) -> int:
    if not callback_data:
        return 0

    try:
        return int(callback_data.split(":", maxsplit=1)[1])
    except (IndexError, ValueError):
        return 0


async def send_lead_for_worker(
    message: Message,
    worksheet: Worksheet,
    worker: str,
    after_row: int = 0,
) -> None:
    try:
        lead, is_manual = get_next_lead_for_worker(
            worksheet=worksheet,
            worker=worker,
            after_row=after_row,
        )
    except GSpreadException:
        logger.exception("Google Sheets error while getting lead")
        await message.answer(
            "Не удалось получить лид из Google Sheets. Попробуйте позже.",
            reply_markup=main_menu_keyboard(),
        )
        return

    if not lead:
        await message.answer(
            "Пока нет доступных лидов для написания.",
            reply_markup=main_menu_keyboard(),
        )
        return

    if is_manual:
        await message.answer(
            "Сейчас нет готовых лидов с Telegram username. "
            "Можно взять лид по номеру телефона вручную.",
            reply_markup=main_menu_keyboard(),
        )
        await message.answer(
            lead_card(lead, is_manual=True),
            reply_markup=manual_lead_keyboard(lead.row_number),
        )
        return

    await message.answer(
        lead_card(lead),
        reply_markup=ready_lead_keyboard(
            row_number=lead.row_number,
            telegram_url=get_telegram_url(lead.telegram_nick),
        ),
    )


async def send_manual_lead_for_worker(
    message: Message,
    worksheet: Worksheet,
    worker: str,
    after_row: int = 0,
) -> None:
    try:
        lead = get_next_manual_lead(
            worksheet=worksheet,
            worker=worker,
            after_row=after_row,
        )
    except GSpreadException:
        logger.exception("Google Sheets error while getting manual lead")
        await message.answer(
            "Не удалось получить лид из Google Sheets. Попробуйте позже.",
            reply_markup=main_menu_keyboard(),
        )
        return

    if not lead:
        await message.answer(
            "Пока нет доступных лидов для написания.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await message.answer(
        lead_card(lead, is_manual=True),
        reply_markup=manual_lead_keyboard(lead.row_number),
    )


@router.message(F.text == GET_LEAD_BUTTON)
async def get_lead_button(message: Message, worksheet: Worksheet) -> None:
    worker = get_worker_name(message.from_user)
    await send_lead_for_worker(message, worksheet, worker)


@router.callback_query(F.data.startswith(f"{NEXT_LEAD_PREFIX}:"))
async def next_lead(callback: CallbackQuery, worksheet: Worksheet) -> None:
    await callback.message.edit_reply_markup(reply_markup=None)
    worker = get_worker_name(callback.from_user)
    await send_lead_for_worker(
        message=callback.message,
        worksheet=worksheet,
        worker=worker,
        after_row=get_row_number(callback.data),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{NEXT_MANUAL_LEAD_PREFIX}:"))
async def next_manual_lead(callback: CallbackQuery, worksheet: Worksheet) -> None:
    await callback.message.edit_reply_markup(reply_markup=None)
    worker = get_worker_name(callback.from_user)
    await send_manual_lead_for_worker(
        message=callback.message,
        worksheet=worksheet,
        worker=worker,
        after_row=get_row_number(callback.data),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{MARK_WRITTEN_PREFIX}:"))
async def mark_written(callback: CallbackQuery, worksheet: Worksheet) -> None:
    worker = get_worker_name(callback.from_user)
    row_number = get_row_number(callback.data)

    try:
        is_updated = mark_lead_as_written(worksheet, row_number, worker)
        next_lead_item, _ = get_next_lead_for_worker(worksheet, worker)
    except GSpreadException:
        logger.exception("Google Sheets error while marking lead as written")
        await callback.message.answer(
            "Не удалось обновить статус лида. Попробуйте позже.",
            reply_markup=main_menu_keyboard(),
        )
        await callback.answer()
        return

    await callback.message.edit_reply_markup(reply_markup=None)

    if not is_updated:
        await callback.message.answer(
            "Не удалось отметить лид. Возможно, он уже обработан.",
            reply_markup=main_menu_keyboard(),
        )
        await callback.answer()
        return

    if not next_lead_item:
        await callback.message.answer(
            "Готово. Статус обновлен на Написал.\n\n"
            "Больше доступных лидов пока нет.",
            reply_markup=main_menu_keyboard(),
        )
        await callback.answer()
        return

    await callback.message.answer(
        "Готово. Статус обновлен на Написал.",
        reply_markup=main_menu_keyboard(),
    )
    await callback.message.answer(
        "Есть еще доступные лиды.",
        reply_markup=next_available_lead_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{MARK_MANUAL_WRITTEN_PREFIX}:"))
async def mark_manual_written(callback: CallbackQuery, worksheet: Worksheet) -> None:
    await mark_written(callback, worksheet)


@router.callback_query(F.data.startswith(f"{MARK_NOT_IN_TELEGRAM_PREFIX}:"))
async def mark_not_in_telegram(callback: CallbackQuery, worksheet: Worksheet) -> None:
    worker = get_worker_name(callback.from_user)
    row_number = get_row_number(callback.data)

    try:
        is_updated = mark_lead_as_not_in_telegram(worksheet, row_number, worker)
        next_lead_item, _ = get_next_lead_for_worker(worksheet, worker)
    except GSpreadException:
        logger.exception("Google Sheets error while marking lead as not in Telegram")
        await callback.message.answer(
            "Не удалось обновить статус лида. Попробуйте позже.",
            reply_markup=main_menu_keyboard(),
        )
        await callback.answer()
        return

    await callback.message.edit_reply_markup(reply_markup=None)

    if not is_updated:
        await callback.message.answer(
            "Не удалось отметить лид. Возможно, он уже обработан.",
            reply_markup=main_menu_keyboard(),
        )
        await callback.answer()
        return

    if not next_lead_item:
        await callback.message.answer(
            "Готово. Статус обновлен на Нет в ТГ.\n\n"
            "Больше доступных лидов пока нет.",
            reply_markup=main_menu_keyboard(),
        )
        await callback.answer()
        return

    await callback.message.answer(
        "Готово. Статус обновлен на Нет в ТГ.",
        reply_markup=main_menu_keyboard(),
    )
    await callback.message.answer(
        "Есть еще доступные лиды.",
        reply_markup=next_available_lead_keyboard(),
    )
    await callback.answer()
