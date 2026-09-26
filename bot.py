# ============ /demo — фото + видео + закреп ============
@dp.message_handler(commands=["demo"])
async def cmd_demo(message: types.Message):
    await message.answer("📸 Смотрите наши работы:")

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

    try:
        await bot.send_video(
            message.from_user.id,
            video=open("demo/demo.mp4", "rb"),
            caption="Видео процесса заливки 🎥"
        )
    except Exception as e:
        logging.error(f"Ошибка видео: {e}")

    final_text = (
        "📋 Хотите такой же пол?\n\n"
        "Отправьте /checklist — пришлю список подготовки.\n"
        "Или оставьте номер телефона — замерщик свяжется 👍"
    )
    final_msg = await message.answer(final_text)

    # Закрепляем финальное сообщение с призывом
    try:
        await bot.pin_chat_message(
            chat_id=message.from_user.id,
            message_id=final_msg.message_id,
            disable_notification=True
        )
        logging.info("Сообщение успешно закреплено")
    except Exception as e:
        logging.error(f"Не удалось закрепить: {e}")
