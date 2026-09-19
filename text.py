from aiogram import Router, F
from aiogram.types import Message

from services.agent import ask_agent
from services.leads import extract_phone, save_lead, notify_manager

router = Router()


@router.message(F.text)
async def handle_text(message: Message):
    await message.bot.send_chat_action(message.chat.id, "typing")
    answer = await ask_agent(message.from_user.id, message.text)

    phone = extract_phone(message.text)
    if phone:
        await save_lead(
            message.from_user.id,
            message.from_user.username,
            phone,
            message.text,
        )
        await notify_manager(
            message.bot,
            message.from_user,
            phone,
            message.text,
        )

    await message.answer(answer)
