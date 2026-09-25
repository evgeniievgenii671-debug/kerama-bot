import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
from dotenv import load_dotenv

from services.agent import ask_groq
from services.memory import get_memory, add_to_memory

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


# ============ /start ============
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    get_memory(message.from_user.id)  # создаём память
    text = (
        "👋 Здравствуйте! Меня зовут Алекс, я менеджер компании <b>GIDROBASE</b>.\n\n"
        "Мы профессионально делаем эпоксидные и наливные полы:\n"
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
    await message.answer("📸 Сейчас пришлю примеры наших работ...")
    # Раскомментируй, когда положишь файлы в папку с ботом:
    # await bot.send_photo(message.from_user.id, photo=open("demo_garage.jpg", "rb"), caption="Эпоксидный пол в гараже 🚗")
    # await bot.send_photo(message.from_user.id, photo=open("demo_service.jpg", "rb"), caption="Пол в автосервисе 🔧")


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
            logging.error(f"Admin notify error: {e}")


# ============ ЗАПУСК ============
if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
