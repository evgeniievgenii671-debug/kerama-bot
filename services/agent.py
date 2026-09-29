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
1. Гидроизоляция кровель — наплавляемая, обмазочная, ремонт, устранение протечек. Для ЖК, складов, ТРЦ, террас, паркингов.
2. Полы — эпоксидные, полиуретановые, 3D, бетонные. Для гаражей, паркингов, складов, автосервисов, производств.

ЦЕНЫ (ориентиры, говори их!):
- Кровля: от 3000 тг/м²
- Эпоксидный пол: от 6500 тг/м²
- Точная смета — после бесплатного замера

ФАКТЫ:
- 10+ лет опыта, 120+ объектов
- Свои бригады, морозостойкие материалы
- Срок 3–5 дней
- Гарантия по договору до 10 лет
- Выезд инженера на замер — БЕСПЛАТНО

ЖЁСТКИЕ ПРАВИЛА:
1. Каждый ответ — 1-2 ЗАКОНЧЕННЫХ предложения. С точкой в конце.
2. Задавай ТОЛЬКО ОДИН вопрос за раз.
3. ЗАПРЕЩЕНО повторять один и тот же вопрос! Если клиент проигнорировал — перефразируй или ответь утверждением.
4. Если клиент спрашивает цену — назови вилку, потом уточняй.
5. ИМЯ — НЕ ОБЯЗАТЕЛЬНО. Спроси 1 раз. Не назвал — иди дальше.
6. Понимай короткие ответы: «Не важно», «Да», «Ну» = согласие/отказ.
7. Не выдумывай цены. Только вилки из блока ЦЕНЫ выше.

ПОРЯДОК ДИАЛОГА:
1. Спроси имя (1 раз)
2. Кровля или полы?
3. Какой объект, где находится?
4. Площадь?
5. Оставьте номер — инженер приедет бесплатно

ПРИМЕРЫ ПРАВИЛЬНЫХ ОТВЕТОВ:
Клиент: Цены и гарантия
Бот: Кровля от 3000 тг/м², полы от 6500 тг/м². Гарантия по договору — до 10 лет.

Клиент: Хотя бы вилку
Бот: Назвал уже: 3000 и 6500 тг/м². Что уточнить — сроки, материалы или гарантию?

Клиент: Не важно
Бот: Хорошо! Тогда уточните, что вас интересует — кровля или полы?

Клиент: Крыша течёт
Бот: Понял! Гидроизоляция кровли — от 3000 тг/м². Какой у вас объект?
"""

BAD_MODELS = [
    "whisper", "tts", "orpheus", "guard",
    "arabic", "saudi", "allam",
    "llama-3.2-1b", "llama-3.2-3b",
]

PRIORITY = [
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "moonshotai/kimi-k2",
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
                max_tokens=300,
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
