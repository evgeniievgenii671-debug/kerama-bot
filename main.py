import os
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from bot_handlers import start_command, handle_text_message

# Включаем логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Точка входа для запуска бота"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("Не найден TELEGRAM_BOT_TOKEN в переменных окружения!")
        return

    # Создаем приложение бота
    application = ApplicationBuilder().token(token).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_message))

    logger.info("Бот успешно запущен и ожидает сообщения...")
    
    # Запуск бота в режиме опросника (polling)
    application.run_polling()

if __name__ == "__main__":
    main()
