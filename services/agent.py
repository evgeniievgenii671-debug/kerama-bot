import os
import logging
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("GROQ_API_KEY")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")

client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

SYSTEM_PROMPT = """Ты — Алекс, менеджер компании GidroBase (Алматы).
Отвечай ТОЛЬКО на русском, грамотно, дружелюбно.

УСЛУГИ:
1. Гидроизоляция кровель — наплавляемая, обмазочная, ремонт, устранение протечек.
2. Полы — эпоксидные, полиуретановые, 3D, бетонные.

ЦЕНЫ (говори их!):
- Кровля: от 3000 тг/м²
- Эпоксидный пол: от 6500 тг/м²
- Точная смета — после бесплатного замера

ФАКТЫ:
- 10+ лет опыта, 120+ объектов
- Гарантия до 10 лет
- Выезд инженера — БЕСПЛАТНО

ГЛАВНЫЕ ПРАВИЛА (НАРУШАТЬ НЕЛЬЗЯ):
1. Каждый ответ — 1-2 ЗАКОНЧЕННЫХ предложения.
2. ОДИН вопрос за раз.
3. ЗАПРЕЩЕНО повторять один и тот же вопрос! Если клиент уже слышал его — задай ДРУГОЙ вопрос или ответь утверждением.
4. Если клиент отвечает «Ну», «Не знаю», «Хз» — НЕ переспрашивай то же самое. Спроси что-то другое: «Расскажите в двух словах, что у вас за проблема?»
5. Если клиент спрашивает цену — назови вилку. Если просит «хотя бы вилку» — значит, уже слышал цифру, назови ДРУГИЕ детали (гарантия, сроки, материалы).
6. ИМЯ — НЕ ОБЯЗАТЕЛЬНО. Спроси 1 раз.
7. Если клиент пишет с ошибками (братия = гарантия, тишет = течёт) — понимай смысл.

ПРИМЕРЫ:
Клиент: Цена и гарантия
Бот: Кровля от 3000 тг/м², полы от 6500 тг/м². Гарантия по договору — до 10 лет.

Клиент: Хотя бы вилку
Бот: Назвал уже: 3000 и 6500 тг/м². Что уточнить — сроки, материалы или гарантию?

Клиент: Ну
Бот: Расскажите коротко — что нужно сделать?

Клиент: Имя не скажу
Бот: Хорошо. Что вас интересует — кровля или полы?

Клиент: Просто ответь на вопрос
Бот: Конечно! Задайте вопрос, отвечу.
"""
BAD_MODELS = [
    "whisper", "tts", "orpheus", "guard",
    "arabic", "saudi", "allam",
    "llama-3.2-1b", "llama-3.2-3b",
]

PRIORITY = [
    "openai/gpt-oss-120b",
]


async def get_good_models() -> list:
    try:
        response = await client.models.list()
        all_models = [m.id for m in response.data]
        good = [m for m in all_models if not any(bad in m.lower() for bad in BAD_MODELS)]
        logger.info(f"Подходящих моделей: {good}")
        return good
    except Exception as e:
        logger.error(f"Ошибка получения моделей: {e}")
        return []


def sort_by_priority(models: list) -> list:
    result = []
    for pref in PRIORITY:
        for m in models:
            if pref in m.lower() and m not in result:
                result.append(m)
    for m in models:
        if m not in result:
            result.append(m)
    return result


async def ask_groq(history):
    """
    Принимает готовую историю диалога (list of dicts) и возвращает ответ.
    bot.py сам загружает и сохраняет историю.
    """
    if not OPENAI_API_KEY:
        logger.error("API-ключ не задан!")
        return "Ошибка конфигурации."

    models = await get_good_models()
    if not models:
        return "Проблема с AI. Попробуйте позже 🙏"

    models_to_try = sort_by_priority(models)[:5]
    logger.info(f"Порядок попыток: {models_to_try}")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-10:]

    last_error = None
    for model in models_to_try:
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=500,
            )
            text = response.choices[0].message.content

            if not text or not text.strip():
                logger.warning(f"{model}: пустой ответ")
                continue

            text = text.strip()
            if text and text[-1] not in ".!?…":
                text += "."

            logger.info(f"✅ Ответила: {model}")
            return text

        except Exception as e:
            last_error = str(e)
            logger.warning(f"{model} не сработала: {e}")
            continue

    logger.error(f"Все упали. Последняя: {last_error}")
    return "Извините, сейчас не могу ответить 🙏"
