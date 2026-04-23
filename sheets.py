from dataclasses import dataclass
from datetime import datetime
import json
import re

from gspread import Worksheet, service_account, service_account_from_dict

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

HEADER_FORMAT = {
    "backgroundColor": {"red": 0.86, "green": 0.91, "blue": 0.98},
    "horizontalAlignment": "CENTER",
    "verticalAlignment": "MIDDLE",
    "textFormat": {
        "bold": True,
        "foregroundColor": {"red": 0.12, "green": 0.18, "blue": 0.28},
    },
    "wrapStrategy": "WRAP",
}
BODY_FORMAT = {
    "verticalAlignment": "MIDDLE",
    "wrapStrategy": "WRAP",
}
PHONE_COLUMN_FORMAT = {
    "numberFormat": {"type": "TEXT"},
}
NEW_STATUS_FORMAT = {
    "backgroundColor": {"red": 1.0, "green": 0.95, "blue": 0.78},
    "horizontalAlignment": "CENTER",
    "textFormat": {
        "bold": True,
        "foregroundColor": {"red": 0.45, "green": 0.32, "blue": 0.05},
    },
}
WRITTEN_STATUS_FORMAT = {
    "backgroundColor": {"red": 0.82, "green": 0.93, "blue": 0.84},
    "horizontalAlignment": "CENTER",
    "textFormat": {
        "bold": True,
        "foregroundColor": {"red": 0.08, "green": 0.35, "blue": 0.16},
    },
}
COLUMN_WIDTHS = {
    0: 135,
    1: 155,
    2: 155,
    3: 155,
    4: 155,
    5: 230,
    6: 135,
}


@dataclass(frozen=True)
class Lead:
    row_number: int
    instagram: str
    phone: str
    telegram_nick: str
    business_type: str
    status: str


def get_worksheet(settings: Settings) -> Worksheet:
    if settings.google_service_account_json:
        credentials = json.loads(settings.google_service_account_json)
        client = service_account_from_dict(credentials)
    elif settings.google_service_account_file:
        client = service_account(filename=settings.google_service_account_file)
    else:
        raise RuntimeError("Google service account credentials are not configured")

    spreadsheet = client.open(settings.google_sheet_name)
    return spreadsheet.sheet1


def init_sheet(settings: Settings) -> Worksheet:
    worksheet = get_worksheet(settings)
    rows = worksheet.get_all_values()

    if not rows:
        worksheet.append_row(HEADERS, value_input_option="USER_ENTERED")
    elif rows[0] != HEADERS:
        worksheet.insert_row(HEADERS, index=1, value_input_option="USER_ENTERED")

    initialize_sheet_format(worksheet)
    return worksheet


def initialize_sheet_format(worksheet: Worksheet) -> None:
    worksheet.freeze(rows=1)
    worksheet.format("A1:G1", HEADER_FORMAT)
    worksheet.format("A:G", BODY_FORMAT)
    worksheet.format("D:D", PHONE_COLUMN_FORMAT)

    requests = [
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": worksheet.id,
                    "dimension": "COLUMNS",
                    "startIndex": column_index,
                    "endIndex": column_index + 1,
                },
                "properties": {"pixelSize": width},
                "fields": "pixelSize",
            }
        }
        for column_index, width in COLUMN_WIDTHS.items()
    ]

    worksheet.spreadsheet.batch_update({"requests": requests})
    apply_status_validation(worksheet)

    rows = worksheet.get_all_values()[1:]
    for row_number, row in enumerate(rows, start=2):
        current_phone = get_row_value(row, PHONE_INDEX)
        normalized_phone = normalize_ukrainian_phone(current_phone)

        if normalized_phone and current_phone != normalized_phone:
            worksheet.update_cell(row_number, PHONE_INDEX + 1, normalized_phone)

        current_status = get_row_value(row, STATUS_INDEX)
        normalized_status = normalize_status(current_status)

        if current_status != normalized_status:
            worksheet.update_cell(row_number, STATUS_INDEX + 1, normalized_status)

        format_status_cell(worksheet, row_number, normalized_status)


def apply_status_validation(worksheet: Worksheet) -> None:
    worksheet.spreadsheet.batch_update(
        {
            "requests": [
                {
                    "setDataValidation": {
                        "range": {
                            "sheetId": worksheet.id,
                            "startRowIndex": 1,
                            "startColumnIndex": STATUS_INDEX,
                            "endColumnIndex": STATUS_INDEX + 1,
                        },
                        "rule": {
                            "condition": {
                                "type": "ONE_OF_LIST",
                                "values": [
                                    {"userEnteredValue": NEW_STATUS},
                                    {"userEnteredValue": WRITTEN_STATUS},
                                ],
                            },
                            "showCustomUi": True,
                            "strict": True,
                        },
                    }
                }
            ]
        }
    )


def normalize_instagram(instagram: str) -> str:
    return instagram.strip().lower()


def normalize_phone(phone: str) -> str:
    return re.sub(r"\D", "", phone)


def normalize_ukrainian_phone(phone: str) -> str | None:
    digits = normalize_phone(phone)

    if len(digits) == 9:
        return f"380{digits}"

    if len(digits) == 10 and digits.startswith("0"):
        return f"38{digits}"

    if len(digits) == 11 and digits.startswith("80"):
        return f"3{digits}"

    if len(digits) == 12 and digits.startswith("380"):
        return digits

    return None


def is_duplicate_lead(worksheet: Worksheet, instagram: str, phone: str) -> bool:
    normalized_instagram = normalize_instagram(instagram)
    normalized_phone = normalize_ukrainian_phone(phone)

    rows = worksheet.get_all_values()[1:]

    for row in rows:
        row_instagram = row[2] if len(row) > 2 else ""
        row_phone = row[3] if len(row) > 3 else ""

        instagram_matches = (
            normalized_instagram
            and normalize_instagram(row_instagram) == normalized_instagram
        )
        row_normalized_phone = normalize_ukrainian_phone(row_phone)
        phone_matches = normalized_phone and row_normalized_phone == normalized_phone

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
    normalized_phone = normalize_ukrainian_phone(phone)

    if not normalized_phone:
        raise ValueError("Invalid Ukrainian phone number")

    worksheet.append_row(
        [
            datetime.now().strftime("%d.%m.%Y %H:%M"),
            worker,
            instagram,
            normalized_phone,
            "",
            business_type,
            NEW_STATUS,
        ],
        value_input_option="RAW",
    )
    row_number = len(worksheet.get_all_values())
    worksheet.format(f"A{row_number}:G{row_number}", BODY_FORMAT)
    format_status_cell(worksheet, row_number, NEW_STATUS)


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
    clean_status = status.strip().lower()

    if clean_status == WRITTEN_STATUS.lower():
        return WRITTEN_STATUS

    return NEW_STATUS


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
    format_status_cell(worksheet, row_number, WRITTEN_STATUS)
    return True


def format_status_cell(worksheet: Worksheet, row_number: int, status: str) -> None:
    clean_status = normalize_status(status)
    cell_range = f"G{row_number}"

    if clean_status == WRITTEN_STATUS:
        worksheet.format(cell_range, WRITTEN_STATUS_FORMAT)
        return

    worksheet.format(cell_range, NEW_STATUS_FORMAT)


def get_lead_without_nick(
    worksheet: Worksheet,
    excluded_rows: set[int] | None = None,
) -> Lead | None:
    excluded_rows = excluded_rows or set()
    rows = worksheet.get_all_values()[1:]

    for index, row in enumerate(rows, start=2):
        if index in excluded_rows:
            continue

        phone = get_row_value(row, PHONE_INDEX)
        telegram_nick = get_row_value(row, TELEGRAM_NICK_INDEX)
        # Если телефон есть, а ника в ТГ нет — берем в обработку
        if phone and not telegram_nick:
            return row_to_lead(index, row)
    return None


def update_telegram_nick(worksheet: Worksheet, row_number: int, nick: str) -> None:
    # TELEGRAM_NICK_INDEX равен 4, значит это 5-я колонка в таблице
    worksheet.update_cell(row_number, TELEGRAM_NICK_INDEX + 1, nick)
