import os
import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
from dotenv import load_dotenv

from services.agent import ask_groq
from services.memory import get_memory, add_to_memory, user_memory

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# ============ ФАЙЛ С ДЕМО-МАТЕРИАЛАМИ ============
DEMO_FILE = "demo_data.json"

def load_demo():
    if os.path.exists(DEMO_FILE):
        with open(DEMO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"photos": [], "videos": []}

def save_demo(data):
    with open(DEMO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

demo_data = load_demo()
adding_mode = {"active": False}

# ============ КЛЮЧЕВЫЕ СЛОВА ДЛЯ ДЕМО ============
DEMO_KEYWORDS = [
    "фото", "фотки", "фотографии", "фотка", "снимки",
    "видео", "видик", "ролик", "запись",
    "пример", "примеры", "работы", "покажи", "показать",
    "скинь", "скинуть", "пришли", "прислать", "отправь",
    "демо", "образец", "образцы", "портфолио", "кейс"
]

def is_demo_request(text):
    """Проверяет, просит ли клиент показать примеры работ."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in DEMO_KEYWORDS)


# ============ /start ============
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    get_memory(message.from_user.id)
    text = (
        "👋 Здравствуйте! Меня зовут Алекс, я менеджер компании <b>GIDROBASE</b>.\n\n"
        "Мы делаем эпоксидные и наливные полы:\n"
        "✅ Гаражи, автосервисы, паркинги\n"
        "✅ Склады, хозпостройки\n"
        "✅ Выравнивание основания\n\n"
        "Подскажите, какой у вас объект? 🏠"
    )
    await message.answer(text)


# ============ /checklist ============
@dp.message_handler(commands=["checklist"])
async def cmd_checklist(message: types.Message):
    text = (
        "📋 <b>Чек-лист: готов ли ваш пол к заливке?</b>\n\n"
        "1️⃣ <b>Площадь</b> — сколько м²?\n"
        "2️⃣ <b>Основание</b> — бетон, стяжка или старое покрытие?\n"
        "3️⃣ <b>Состояние</b> — трещины, ямы, масляные пятна?\n"
        "4️⃣ <b>Влажность</b> — не более 4%\n"
        "5️⃣ <b>Температура</b> — +15…+25°C\n"
        "6️⃣ <b>Сроки</b> — когда планируете?\n\n"
        "💡 <b>Выезд замерщика бесплатный</b> — оставьте номер 👇"
    )
    await message.answer(text)


# ============ ФУНКЦИЯ ОТПРАВКИ ДЕМО ============
async def send_demo(chat_id):
    """Отправляет все демо-материалы клиенту."""
    if not demo_data["photos"] and not demo_data["videos"]:
        await bot.send_message(chat_id, "📸 Демо-материалы пока не добавлены.")
        return

    await bot.send_message(chat_id, "📸 Вот примеры наших работ:")

    for photo in demo_data["photos"]:
        try:
            await bot.send_photo(
                chat_id,
                photo=photo["file_id"],
                caption=photo.get("caption", "")
            )
        except Exception as e:
            logging.error(f"Ошибка фото: {e}")

    for video in demo_data["videos"]:
        try:
            await bot.send_video(
                chat_id,
                video=video["file_id"],
                caption=video.get("caption", "")
            )
        except Exception as e:
            logging.error(f"Ошибка видео: {e}")


# ============ /demo ============
@dp.message_handler(commands=["demo"])
async def cmd_demo(message: types.Message):
    await send_demo(message.from_user.id)
    await message.answer(
        "📋 Хотите такой же пол? Отправьте /checklist — "
        "я пришлю список подготовки.\n\n"
        "Или оставьте номер — замерщик свяжется 👍"
    )


# ============ АДМИН: добавление демо ============
def is_admin(message):
    return message.from_user.id == ADMIN_ID


@dp.message_handler(commands=["add_demo"])
async def cmd_add_demo(message: types.Message):
    if not is_admin(message):
        return
    adding_mode["active"] = True
    await message.answer(
        "✅ Режим добавления включён.\n\n"
        "Отправляй фото и видео (можно с подписью — она станет описанием).\n"
        "Когда закончишь — отправь /stop_demo"
    )


@dp.message_handler(commands=["stop_demo"])
async def cmd_stop_demo(message: types.Message):
    if not is_admin(message):
        return
    adding_mode["active"] = False
    await message.answer(
        f"⏹ Добавление выключено.\n\n"
        f"📸 Фото: {len(demo_data['photos'])}\n"
        f"🎥 Видео: {len(demo_data['videos'])}"
    )


@dp.message_handler(commands=["show_list"])
async def cmd_show_list(message: types.Message):
    if not is_admin(message):
        return
    await message.answer(
        f"📊 Фото: {len(demo_data['photos'])}\n"
        f"🎥 Видео: {len(demo_data['videos'])}"
    )


@dp.message_handler(commands=["clear_demo"])
async def cmd_clear_demo(message: types.Message):
    if not is_admin(message):
        return
    demo_data["photos"] = []
    demo_data["videos"] = []
    save_demo(demo_data)
    await message.answer("🗑 Все демо-материалы удалены.")


# ============ ПРИЁМ ФОТО/ВИДЕО ============
@dp.message_handler(content_types=["photo"])
async def handle_photo(message: types.Message):
    if not adding_mode["active"] or not is_admin(message):
        return
    file_id = message.photo[-1].file_id
    demo_data["photos"].append({
        "file_id": file_id,
        "caption": message.caption or ""
    })
    save_demo(demo_data)
    await message.answer(f"✅ Фото сохранено ({len(demo_data['photos'])} шт.)")


@dp.message_handler(content_types=["video"])
async def handle_video(message: types.Message):
    if not adding_mode["active"] or not is_admin(message):
        return
    file_id = message.video.file_id
    demo_data["videos"].append({
        "file_id": file_id,
        "caption": message.caption or ""
    })
    save_demo(demo_data)
    await message.answer(f"✅ Видео сохранено ({len(demo_data['videos'])} шт.)")


# ============ ОБРАБОТКА ТЕКСТА ============
@dp.message_handler(content_types=["text"])
async def handle_message(message: types.Message):
    # Игнорируем команды
    if message.text.startswith("/"):
        return

    user_id = message.from_user.id
    user_text = message.text

    add_to_memory(user_id, "user", user_text)

    # Проверяем: клиент просит демо?
    if is_demo_request(user_text):
        await send_demo(user_id)
        # Добавляем в память, что показали демо
        add_to_memory(user_id, "assistant", "[Показал примеры работ]")
        await message.answer(
            "📋 Понравилось? Давайте подберём решение под ваш объект.\n\n"
            "Подскажите, какой у вас объект? 🏠"
        )
        return

    # Обычный диалог через Groq
    history = get_memory(user_id)[-10:]
    ai_text = ask_groq(history)
    add_to_memory(user_id, "assistant", ai_text)

    await message.answer(ai_text)

    # Уведомление админу
    if ADMIN_ID:
        try:
            await bot.send_message(
                ADMIN_ID,
                f"🔔 <b>Новый диалог</b>\n"
                f"Клиент: @{message.from_user.username or '—'}\n"
                f"Имя: {message.from_user.full_name}\n"
                f"Написал: {user_text}\n\n"
                f"Бот ответил: {ai_text[:200]}..."
            )
        except Exception as e:
            logging.error(f"Admin notify: {e}")


# ============ HEALTH-CHECK ============
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"GIDROBASE bot is running!")

    def log_message(self, format, *args):
        pass


def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logging.info(f"Health server on port {port}")
    server.serve_forever()


# ============ ЗАПУСК ============
if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()

    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
