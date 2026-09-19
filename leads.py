import logging
import re

from aiogram import Bot
from config import MANAGER_CHAT_ID, DB_PATH
import aiosqlite

logger = logging.getLogger(__name__)

PHONE_RE = re.compile(r"(\+?\d[\d\s\-\(\)]{8,}\d)")


def extract_phone(text: str):
    match = PHONE_RE.search(text)
    return match.group(1) if match else None


async def save_lead(user_id: int, username, phone: str, details: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO leads (user_id, username, phone, details) VALUES (?, ?, ?, ?)",
            (user_id, username, phone, details),
        )
        await db.commit()


async def notify_manager(bot: Bot, user, phone: str, details: str) -> None:
    if not MANAGER_CHAT_ID:
        logger.warning("MANAGER_CHAT_ID не задан")
        return

    text = (
        f"🔥 <b>НОВАЯ ЗАЯВКА</b>\n\n"
        f"👤 {user.full_name}\n"
        f"🔗 @{user.username or '—'}\n"
        f"🆔 {user.id}\n"
        f"📞 {phone}\n\n"
        f"💬 {details}"
    )
    try:
        await bot.send_message(MANAGER_CHAT_ID, text, parse_mode="HTML")
    except Exception:
        logger.exception("Не удалось отправить заявку")
