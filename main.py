import os
import logging
from threading import Thread
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from bot_handlers import start_command, handle_message

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация Flask-приложения
app = Flask(__name__)

@app.route("/")
def health_check():
    return "Bot is running!", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def main():
    # Запускаем Flask-сервер в отдельном потоке
    web_thread = Thread(target=run_web)
    web_thread.start()

    # Получаем токен из переменных окружения Render
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.error("Не найден TELEGRAM_TOKEN в переменных окружения!")
        return

    @app.route(f"/{token}", methods=["POST"])
    def webhook():
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.update_queue.put(update)
        return "ok", 200

    # Создаем приложение бота
    application = ApplicationBuilder().token(token).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Бот успешно запущен и ожидает сообщения...")

if __name__ == "__main__":
    main()
