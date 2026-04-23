from dataclasses import dataclass
from datetime import datetime
import re

from gspread import Worksheet, service_account

from config import Settings


HEADERS = [
    "Дата",
    "Воркер",
    "Instagram",
    "Телефон",
    "Ник в ТГ",
    "Тип бизнеса",
    "Статус",
]

WORKER_INDEX = 1
INSTAGRAM_INDEX = 2
PHONE_INDEX = 3
TELEGRAM_NICK_INDEX = 4
BUSINESS_TYPE_INDEX = 5
STATUS_INDEX = 6
NEW_STATUS = "Новый"
WRITTEN_STATUS = "Написал"


@dataclass(frozen=True)
class Lead:
    row_number: int
    instagram: str
    phone: str
    telegram_nick: str
    business_type: str
    status: str


def get_worksheet(settings: Settings) -> Worksheet:
    client = service_account(filename=settings.google_service_account_file)
    spreadsheet = client.open(settings.google_sheet_name)
    return spreadsheet.sheet1


def init_sheet(settings: Settings) -> Worksheet:
    worksheet = get_worksheet(settings)

    if not worksheet.get_all_values():
        worksheet.append_row(HEADERS, value_input_option="USER_ENTERED")

    return worksheet


def normalize_instagram(instagram: str) -> str:
    return instagram.strip().lower()


def normalize_phone(phone: str) -> str:
    return re.sub(r"\D", "", phone)


def is_duplicate_lead(worksheet: Worksheet, instagram: str, phone: str) -> bool:
    normalized_instagram = normalize_instagram(instagram)
    normalized_phone = normalize_phone(phone)

    rows = worksheet.get_all_values()[1:]

    for row in rows:
        row_instagram = row[2] if len(row) > 2 else ""
        row_phone = row[3] if len(row) > 3 else ""

        instagram_matches = (
            normalized_instagram
            and normalize_instagram(row_instagram) == normalized_instagram
        )
        phone_matches = normalized_phone and normalize_phone(row_phone) == normalized_phone

        if instagram_matches or phone_matches:
            return True

    return False


def append_lead(
    worksheet: Worksheet,
    worker: str,
    instagram: str,
    phone: str,
    business_type: str,
) -> None:
    worksheet.append_row(
        [
            datetime.now().strftime("%d.%m.%Y %H:%M"),
            worker,
            instagram,
            phone,
            "",
            business_type,
            NEW_STATUS,
        ],
        value_input_option="USER_ENTERED",
    )


def add_lead_if_not_duplicate(
    worksheet: Worksheet,
    worker: str,
    instagram: str,
    phone: str,
    business_type: str,
) -> bool:
    if is_duplicate_lead(worksheet, instagram, phone):
        return False

    append_lead(
        worksheet=worksheet,
        worker=worker,
        instagram=instagram,
        phone=phone,
        business_type=business_type,
    )
    return True


def get_row_value(row: list[str], index: int) -> str:
    return row[index].strip() if len(row) > index else ""


def normalize_status(status: str) -> str:
    return status.strip() or NEW_STATUS


def is_available_status(status: str) -> bool:
    return normalize_status(status).lower() == NEW_STATUS.lower()


def row_to_lead(row_number: int, row: list[str]) -> Lead:
    return Lead(
        row_number=row_number,
        instagram=get_row_value(row, INSTAGRAM_INDEX),
        phone=get_row_value(row, PHONE_INDEX),
        telegram_nick=get_row_value(row, TELEGRAM_NICK_INDEX),
        business_type=get_row_value(row, BUSINESS_TYPE_INDEX),
        status=normalize_status(get_row_value(row, STATUS_INDEX)),
    )


def get_available_worker_leads(worksheet: Worksheet, worker: str) -> list[Lead]:
    rows = worksheet.get_all_values()[1:]
    leads: list[Lead] = []

    for index, row in enumerate(rows, start=2):
        row_worker = get_row_value(row, WORKER_INDEX)
        row_status = get_row_value(row, STATUS_INDEX)

        if row_worker == worker and is_available_status(row_status):
            leads.append(row_to_lead(index, row))

    return leads


def find_next_lead(leads: list[Lead], after_row: int = 0) -> Lead | None:
    if not leads:
        return None

    if not after_row:
        return leads[0]

    for lead in leads:
        if lead.row_number > after_row:
            return lead

    for lead in leads:
        if lead.row_number != after_row:
            return lead

    return None


def get_ready_leads(worksheet: Worksheet, worker: str) -> list[Lead]:
    return [
        lead
        for lead in get_available_worker_leads(worksheet, worker)
        if lead.telegram_nick
    ]


def get_manual_leads(worksheet: Worksheet, worker: str) -> list[Lead]:
    return [
        lead
        for lead in get_available_worker_leads(worksheet, worker)
        if not lead.telegram_nick and lead.phone
    ]


def get_next_ready_lead(
    worksheet: Worksheet,
    worker: str,
    after_row: int = 0,
) -> Lead | None:
    return find_next_lead(get_ready_leads(worksheet, worker), after_row)


def get_next_manual_lead(
    worksheet: Worksheet,
    worker: str,
    after_row: int = 0,
) -> Lead | None:
    return find_next_lead(get_manual_leads(worksheet, worker), after_row)


def get_next_lead_for_worker(
    worksheet: Worksheet,
    worker: str,
    after_row: int = 0,
) -> tuple[Lead | None, bool]:
    ready_lead = get_next_ready_lead(worksheet, worker, after_row)

    if ready_lead:
        return ready_lead, False

    manual_lead = get_next_manual_lead(worksheet, worker, after_row)

    if manual_lead:
        return manual_lead, True

    return None, False


def mark_lead_as_written(worksheet: Worksheet, row_number: int, worker: str) -> bool:
    row = worksheet.row_values(row_number)

    if get_row_value(row, WORKER_INDEX) != worker:
        return False

    if not is_available_status(get_row_value(row, STATUS_INDEX)):
        return False

    worksheet.update_cell(row_number, STATUS_INDEX + 1, WRITTEN_STATUS)
    return True

def get_lead_without_nick(worksheet: Worksheet) -> Lead | None:
    rows = worksheet.get_all_values()[1:]
    for index, row in enumerate(rows, start=2):
        phone = get_row_value(row, PHONE_INDEX)
        telegram_nick = get_row_value(row, TELEGRAM_NICK_INDEX)
        # Если телефон есть, а ника в ТГ нет — берем в обработку
        if phone and not telegram_nick:
            return row_to_lead(index, row)
    return None

def update_telegram_nick(worksheet: Worksheet, row_number: int, nick: str) -> None:
    # TELEGRAM_NICK_INDEX равен 4, значит это 5-я колонка в таблице
    worksheet.update_cell(row_number, TELEGRAM_NICK_INDEX + 1, nick)
