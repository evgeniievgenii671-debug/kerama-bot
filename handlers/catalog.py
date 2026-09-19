import json

from aiogram import Router, F
from aiogram.types import Message, InputMediaPhoto
from aiogram.filters import Command

from config import CATALOG_PATH

router = Router()

try:
    with open(CATALOG_PATH, encoding="utf-8") as f:
        CATALOG = json.load(f)
except FileNotFoundError:
    CATALOG = []


@router.message(Command("catalog"))
async def show_catalog(message: Message):
    items = [i for i in CATALOG if i.get("file_id")][:5]
    if not items:
        await message.answer(
            "Каталог скоро появится. Пока могу рассказать про ассортимент — что интересует?"
        )
        return

    media = [
        InputMediaPhoto(
            media=item["file_id"],
            caption=f"{item['name']} — {item.get('description', '')}",
        )
        for item in items
    ]
    await message.answer_media_group(media)
