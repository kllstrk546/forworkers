from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


ADD_LEAD_BUTTON = "➕ Добавить лида"
GET_LEAD_BUTTON = "🎯 Дать лид для написания"

CONFIRM_ADD_LEAD = "add_lead_confirm"
CANCEL_ADD_LEAD = "add_lead_cancel"
MARK_WRITTEN_PREFIX = "lead_written"
NEXT_LEAD_PREFIX = "lead_next"
MARK_MANUAL_WRITTEN_PREFIX = "lead_manual_written"
NEXT_MANUAL_LEAD_PREFIX = "lead_manual_next"
MARK_NOT_IN_TELEGRAM_PREFIX = "lead_not_in_tg"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=ADD_LEAD_BUTTON),
                KeyboardButton(text=GET_LEAD_BUTTON),
            ]
        ],
        resize_keyboard=True,
    )


def add_lead_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить",
                    callback_data=CONFIRM_ADD_LEAD,
                ),
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=CANCEL_ADD_LEAD,
                ),
            ]
        ]
    )


def ready_lead_keyboard(
    row_number: int,
    telegram_url: str | None = None,
) -> InlineKeyboardMarkup:
    inline_keyboard = []

    if telegram_url:
        inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text="Открыть Telegram",
                    url=telegram_url,
                )
            ]
        )

    inline_keyboard.extend(
        [
            [
                InlineKeyboardButton(
                    text="✅ Отметить как Написал",
                    callback_data=f"{MARK_WRITTEN_PREFIX}:{row_number}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚫 Нет в Telegram",
                    callback_data=f"{MARK_NOT_IN_TELEGRAM_PREFIX}:{row_number}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⏭ Следующий лид",
                    callback_data=f"{NEXT_LEAD_PREFIX}:{row_number}",
                )
            ],
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=inline_keyboard,
    )


def manual_lead_keyboard(row_number: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Отметить как Написал вручную",
                    callback_data=f"{MARK_MANUAL_WRITTEN_PREFIX}:{row_number}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚫 Нет в Telegram",
                    callback_data=f"{MARK_NOT_IN_TELEGRAM_PREFIX}:{row_number}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⏭ Показать другой",
                    callback_data=f"{NEXT_MANUAL_LEAD_PREFIX}:{row_number}",
                )
            ],
        ]
    )


def next_available_lead_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⏭ Следующий лид",
                    callback_data=f"{NEXT_LEAD_PREFIX}:0",
                )
            ]
        ]
    )
