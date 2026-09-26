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
    """Загружает список демо-материалов."""
    if os.path.exists(DEMO_FILE):
        with open(DEMO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"photos": [], "videos": []}

def save_demo(data):
    """Сохраняет список демо-материалов."""
    with open(DEMO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

demo_data = load_demo()

# Режим добавления (только для админа)
adding_mode = {"active": False}


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


# ============ /demo — показывает все материалы ============
@dp.message_handler(commands=["demo"])
async def cmd_demo(message: types.Message):
    if not demo_data["photos"] and not demo_data["videos"]:
        await message.answer("📸 Демо-материалы пока не добавлены. Менеджер скоро их загрузит!")
        return

    await message.answer("📸 Смотрите наши работы:")

    for photo in demo_data["photos"]:
        try:
            await bot.send_photo(
                message.from_user.id,
                photo=photo["file_id"],
                caption=photo.get("caption", "")
            )
        except Exception as e:
            logging.error(f"Ошибка фото: {e}")

    for video in demo_data["videos"]:
        try:
            await bot.send_video(
                message.from_user.id,
                video=video["file_id"],
                caption=video.get("caption", "")
            )
        except Exception as e:
            logging.error(f"Ошибка видео: {e}")

    final_msg = await message.answer(
        "📋 Хотите такой же пол?\n\n"
        "Отправьте /checklist — пришлю список подготовки.\n"
        "Или оставьте номер телефона — замерщик свяжется 👍"
    )

    # Закрепляем призыв в чате клиента
    try:
        await bot.pin_chat_message(
            chat_id=message.from_user.id,
            message_id=final_msg.message_id,
            disable_notification=True
        )
    except Exception as e:
        logging.error(f"Не удалось закрепить: {e}")


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
        "Теперь отправляй мне фото и видео — они будут сохраняться.\n"
        "Каждое фото/видео можно подписать — подпись станет описанием.\n\n"
        "Когда закончишь — отправь /stop_demo"
    )


@dp.message_handler(commands=["stop_demo"])
async def cmd_stop_demo(message: types.Message):
    if not is_admin(message):
        return
    adding_mode["active"] = False
    await message.answer(
        f"⏹ Режим добавления выключен.\n\n"
        f"📊 Сохранено:\n"
        f"📸 Фото: {len(demo_data['photos'])}\n"
        f"🎥 Видео: {len(demo_data['videos'])}"
    )


@dp.message_handler(commands=["show_list"])
async def cmd_show_list(message: types.Message):
    if not is_admin(message):
        return
    await message.answer(
        f"📊 <b>Демо-материалы:</b>\n\n"
        f"📸 Фото: {len(demo_data['photos'])}\n"
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


# ============ ПРИЁМ ФОТО И ВИДЕО В РЕЖИМЕ ДОБАВЛЕНИЯ ============
@dp.message_handler(content_types=["photo"])
async def handle_photo(message: types.Message):
    if not adding_mode["active"] or not is_admin(message):
        return
    # Берём самое большое разрешение
    file_id = message.photo[-1].file_id
    demo_data["photos"].append({
        "file_id": file_id,
        "caption": message.caption or ""
    })
    save_demo(demo_data)
    await message.answer(f"✅ Фото сохранено ({len(demo_data['photos'])} всего)")


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
    await message.answer(f"✅ Видео сохранено ({len(demo_data['videos'])} всего)")


# ============ АДМИН: очистка памяти, статистика, help ============
@dp.message_handler(commands=["clear"])
async def cmd_clear(message: types.Message):
    if not is_admin(message):
        return
    user_memory.clear()
    await message.answer("🧹 Память всех клиентов очищена!")


@dp.message_handler(commands=["stats"])
async def cmd_stats(message: types.Message):
    if not is_admin(message):
        return
    await message.answer(f"📊 Активных диалогов: {len(user_memory)}")


@dp.message_handler(commands=["help"])
async def cmd_help(message: types.Message):
    text = (
        "🤖 <b>Команды:</b>\n\n"
        "/start — начать\n"
        "/checklist — чек-лист\n"
        "/demo — примеры работ\n\n"
        "<b>Для админа:</b>\n"
        "/add_demo — добавить материалы\n"
        "/stop_demo — закончить добавление\n"
        "/show_list — список материалов\n"
        "/clear_demo — удалить все материалы\n"
        "/clear — очистить память\n"
        "/stats — статистика"
    )
    await message.answer(text)


# ============ ОБРАБОТКА ТЕКСТА (AI) ============
@dp.message_handler(content_types=["text"])
async def handle_message(message: types.Message):
    # Игнорируем команды (они уже обработаны выше)
    if message.text.startswith("/"):
        return

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
