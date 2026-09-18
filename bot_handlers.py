from telegram import Update
from telegram.ext import ContextTypes
from services.gemini import ask_gemini

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_name = update.effective_user.first_name or "клиент"
    welcome_text = (
        f"Здравствуйте, {user_name}! Вас приветствует официальный помощник магазина "
        "отделочных материалов **«KERAMA WORLD»**.\n\n"
        "У нас вы можете подобрать керамогранит, кафель, сантехнику и эпоксидные полы.\n"
        "Чем я могу вам помочь? Вы можете написать ваш вопрос или отправить голосовое сообщение!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик обычных текстовых сообщений от пользователя"""
    user_id = update.effective_user.id
    user_message = update.message.text

    # Отправляем сообщение в Gemini и получаем ответ
    ai_response = await ask_gemini(user_id, user_message)
    
    await update.message.reply_text(ai_response)
