import logging
from config import ADMIN_ID

logger = logging.getLogger(__name__)


async def notify_admin(bot, user, text: str, is_voice: bool = False):
    if not ADMIN_ID:
        return
    prefix = "🎤 Голосовое" if is_voice else "📩 Текст"
    message = (
        f"<b>{prefix}</b>\n\n"
        f"👤 {user.full_name}\n"
        f"🔗 @{user.username or '—'}\n"
        f"🆔 <code>{user.id}</code>\n\n"
        f"💬 {text}"
    )
    try:
        await bot.send_message(ADMIN_ID, message, parse_mode="HTML")
    except Exception:
        logger.exception("Ошибка отправки админу")
