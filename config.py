from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

@dataclass(frozen=True)
class Settings:
    bot_token: str
    google_service_account_file: str
    google_sheet_name: str
    api_id: int
    api_hash: str
    session_name: str

def get_settings() -> Settings:
    load_dotenv(ENV_FILE, override=True)

    bot_token = os.getenv("BOT_TOKEN")
    google_service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    google_sheet_name = os.getenv("GOOGLE_SHEET_NAME")
    api_id_str = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    session_name = os.getenv("SESSION_NAME", "parser_session")

    missing_vars = [
        name
        for name, value in {
            "BOT_TOKEN": bot_token,
            "GOOGLE_SERVICE_ACCOUNT_FILE": google_service_account_file,
            "GOOGLE_SHEET_NAME": google_sheet_name,
            "API_ID": api_id_str,
            "API_HASH": api_hash,
        }.items()
        if not value
    ]

    if missing_vars:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing_vars)
        )

    return Settings(
        bot_token=bot_token,
        google_service_account_file=google_service_account_file,
        google_sheet_name=google_sheet_name,
        api_id=int(api_id_str),
        api_hash=api_hash,
        session_name=session_name,
    )
