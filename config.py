from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

@dataclass(frozen=True)
class Settings:
    bot_token: str
    google_sheet_name: str
    api_id: int
    api_hash: str
    session_name: str
    google_service_account_file: str | None = None
    google_service_account_json: str | None = None
    telethon_session_string: str | None = None

def get_settings() -> Settings:
    load_dotenv(ENV_FILE, override=True)

    bot_token = os.getenv("BOT_TOKEN")
    google_service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    google_service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    google_sheet_name = os.getenv("GOOGLE_SHEET_NAME")
    api_id_str = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    session_name = os.getenv("SESSION_NAME", "parser_session")
    telethon_session_string = os.getenv("TELETHON_SESSION_STRING")

    missing_vars = [
        name
        for name, value in {
            "BOT_TOKEN": bot_token,
            "GOOGLE_SHEET_NAME": google_sheet_name,
            "API_ID": api_id_str,
            "API_HASH": api_hash,
        }.items()
        if not value
    ]

    if not google_service_account_file and not google_service_account_json:
        missing_vars.append("GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_SERVICE_ACCOUNT_JSON")

    if missing_vars:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing_vars)
        )

    return Settings(
        bot_token=bot_token,
        google_sheet_name=google_sheet_name,
        api_id=int(api_id_str),
        api_hash=api_hash,
        session_name=session_name,
        google_service_account_file=google_service_account_file,
        google_service_account_json=google_service_account_json,
        telethon_session_string=telethon_session_string,
    )
