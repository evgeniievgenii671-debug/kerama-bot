import os
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
from dotenv import load_dotenv

from services.agent import ask_groq
from services.memory import get_memory, add_to_memory

load_dotenv()

# ============ НАСТРОЙКИ ============
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


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
        "Чтобы мы могли точно рассчитать стоимость, проверьте:\n\n"
        "1️⃣ <b>Площадь</b> — сколько м²?\n"
        "2️⃣ <b>Основание</b> — бетон, стяжка или старое покрытие?\n"
        "3️⃣ <b>Состояние</b> — есть ли трещины, ямы, масляные пятна?\n"
        "4️⃣ <b>Влажность</b> — не более 4% (замеряем сами)\n"
        "5️⃣ <b>Температура</b> — в помещении +15…+25°C\n"
        "6️⃣ <b>Сроки</b> — когда планируете заливку?\n\n"
        "💡 Не уверены? <b>Выезд замерщика бесплатный</b> — мы всё проверим сами.\n"
        "Оставьте номер телефона, и мы свяжемся с вами 👇"
    )
    await message.answer(text)


# ============ /demo ============
@dp.message_handler(commands=["demo"])
async def cmd_demo(message: types.Message):
    await message.answer("📸 Смотрите наши работы:")

    # 5 фото
    photos = [
        ("demo/demo1.jpg", "Эпоксидный пол в гараже 🚗"),
        ("demo/demo2.jpg", "Пол в автосервисе 🔧"),
        ("demo/demo3.jpg", "До и после ✨"),
        ("demo/demo4.jpg", "Крупный план — как зеркало 🪞"),
        ("demo/demo5.jpg", "Процесс заливки 🎬"),
    ]
    for path, caption in photos:
        try:
            await bot.send_photo(message.from_user.id, photo=open(path, "rb"), caption=caption)
        except Exception as e:
            logging.error(f"Ошибка фото {path}: {e}")

    # Видео
    try:
        await bot.send_video(
            message.from_user.id,
            video=open("demo/demo.mp4", "rb"),
            caption="Видео процесса заливки 🎥"
        )
    except Exception as e:
        logging.error(f"Ошибка видео: {e}")

    # Финальное сообщение
    await message.answer(
        "📋 Хотите такой же пол? Отправьте /checklist — "
        "я пришлю список того, что нужно подготовить.\n\n"
        "Или сразу оставьте номер телефона — замерщик свяжется 👍"
    )


# ============ АДМИН-КОМАНДЫ ============
def is_admin(message):
    return message.from_user.id == ADMIN_ID

@dp.message_handler(commands=["clear"])
async def cmd_clear(message: types.Message):
    if not is_admin(message):
        return
    from services.memory import user_memory
    user_memory.clear()
    await message.answer("🧹 Память всех клиентов очищена!")

@dp.message_handler(commands=["stats"])
async def cmd_stats(message: types.Message):
    if not is_admin(message):
        return
    from services.memory import user_memory
    await message.answer(f"📊 Активных диалогов: {len(user_memory)}")

@dp.message_handler(commands=["help"])
async def cmd_help(message: types.Message):
    text = (
        "🤖 <b>Команды:</b>\n\n"
        "/start — начать\n"
        "/checklist — чек-лист\n"
        "/demo — примеры работ\n\n"
        "<b>Админ:</b>\n"
        "/clear — очистить память\n"
        "/stats — статистика"
    )
    await message.answer(text)


# ============ ОБРАБОТКА ТЕКСТА ============
@dp.message_handler(content_types=["text"])
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    user_text = message.text

    add_to_memory(user_id, "user", user_text)
    history = get_memory(user_id)[-10:]

    ai_text = ask_groq(history)
    add_to_memory(user_id, "assistant", ai_text)

    await message.answer(ai_text)

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
            logging.error(f"Admin notify error: {e}")


# ============ HEALTH-CHECK ДЛЯ RENDER ============
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
    logging.info(f"Health server running on port {port}")
    server.serve_forever()


# ============ ЗАПУСК ============
if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()

    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
