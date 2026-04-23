import asyncio
import logging
import random

from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.contacts import ImportContactsRequest
from telethon.tl.types import InputPhoneContact
from gspread import Worksheet

from config import Settings
from sheets import get_lead_without_nick, update_telegram_nick

logger = logging.getLogger(__name__)


def mask_phone(phone: str) -> str:
    if len(phone) <= 5:
        return "***"

    return f"{phone[:4]}***{phone[-2:]}"


async def background_parser(settings: Settings, worksheet: Worksheet) -> None:
    client = TelegramClient(settings.session_name, settings.api_id, settings.api_hash)

    await client.connect()
    if not await client.is_user_authorized():
        logger.error("❌ Telethon не авторизован! Запустите login.py для создания файла сессии.")
        return

    logger.info("✅ Фоновый парсер Telethon успешно запущен.")

    while True:
        try:
            lead = get_lead_without_nick(worksheet)

            if not lead:
                # База обработана, спим 5 минут и проверяем таблицу снова
                await asyncio.sleep(300)
                continue

            phone = lead.phone
            if not phone.startswith("+"):
                phone = "+" + phone

            logger.info(
                "Парсер проверяет лид в строке %s, телефон %s",
                lead.row_number,
                mask_phone(phone),
            )

            # Добавляем в контакты
            contact = InputPhoneContact(
                client_id=0,
                phone=phone,
                first_name="Lead",
                last_name=str(lead.row_number)
            )
            result = await client(ImportContactsRequest([contact]))

            user = result.users[0] if result.users else None
            username = getattr(user, "username", None) if user else None

            if username:
                nick = f"@{username}"
                update_telegram_nick(worksheet, lead.row_number, nick)
                logger.info("Лид в строке %s обновлен: %s", lead.row_number, nick)
            else:
                logger.info(
                    "Для лида в строке %s username не найден. Ник в ТГ оставлен пустым.",
                    lead.row_number,
                )

            # Рандомная пауза от 15 до 30 минут, чтобы не улететь в бан
            delay = random.randint(900, 1800)
            logger.info(f"Парсер спит {delay // 60} минут...")
            await asyncio.sleep(delay)

        except FloodWaitError as e:
            logger.warning(f"⚠️ Лимит Telethon! Ждем {e.seconds} секунд.")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.exception(f"Ошибка в парсере: {e}")
            await asyncio.sleep(60)
