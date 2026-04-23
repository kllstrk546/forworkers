from aiogram.types import User


def get_worker_name(user: User | None) -> str:
    if user and user.username:
        return user.username

    telegram_id = user.id if user else "unknown"
    return f"user_{telegram_id}"
