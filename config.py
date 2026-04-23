from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    google_service_account_file: str
    google_sheet_name: str


def get_settings() -> Settings:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN")
    google_service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    google_sheet_name = os.getenv("GOOGLE_SHEET_NAME")

    missing_vars = [
        name
        for name, value in {
            "BOT_TOKEN": bot_token,
            "GOOGLE_SERVICE_ACCOUNT_FILE": google_service_account_file,
            "GOOGLE_SHEET_NAME": google_sheet_name,
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
    )
