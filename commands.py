from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services.memory import reset_history

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Добро пожаловать в KERAMA WORLD!\n\n"
        "У нас керамогранит, кафель, сантехника, травертин, обои, ламинат, "
        "декор-панели, гранит и входные двери.\n\n"
        "Чем именно можем помочь?"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Напишите текстом или отправьте голосовое — я отвечу.\n"
        "/reset — очистить историю диалога"
    )


@router.message(Command("reset"))
async def cmd_reset(message: Message):
    await reset_history(message.from_user.id)
    await message.answer("История диалога очищена.")
