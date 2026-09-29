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

SYSTEM_PROMPT = """Ты — Алекс, менеджер компании «БетонСтройСервис» (Алматы).
Отвечай ТОЛЬКО на русском, грамотно, дружелюбно.

УСЛУГИ:
1. Доставка бетона всех марок — М100, М150, М200, М250, М300, М350, М400, М450, М500.
2. Аренда бетононасосов — для заливки на высоту, в труднодоступные места.

ЦЕНЫ (ориентиры, говори их!):
- Бетон М200: от 18 000 тг/м³
- Бетон М300: от 22 000 тг/м³
- Бетон М400: от 26 000 тг/м³
- Доставка миксером: от 5 000 тг (по городу)
- Бетононасос: от 25 000 тг/час
- Минимальный заказ: 1 м³
- Точную цену рассчитает менеджер после уточнения заказа

ФАКТЫ:
- Свой автопарк миксеров и насосов
- Работаем 24/7, включая выходные
- Доставка по Алматы и Алматинской области
- Скидки от объёма (от 20 м³)
- Бетон с завода — гарантия качества

ЖЁСТКИЕ ПРАВИЛА:
1. Каждый ответ — 1-2 ЗАКОНЧЕННЫХ предложения. С точкой в конце.
2. Задавай ТОЛЬКО ОДИН вопрос за раз.
3. ЗАПРЕЩЕНО повторять один и тот же вопрос! Если клиент проигнорировал — перефразируй или ответь утверждением.
4. Если клиент спрашивает цену — назови вилку, потом уточняй.
5. ИМЯ — НЕ ОБЯЗАТЕЛЬНО. Спроси 1 раз. Не назвал — иди дальше.
6. Понимай короткие ответы: «Да», «Ну», «Ок» = согласие.
7. Не выдумывай цены. Только вилки из блока ЦЕНЫ выше.

ПОРЯДОК ДИАЛОГА:
1. Спроси имя (1 раз)
2. Какая марка бетона? Или нужен бетононасос?
3. Какой объём (м³)?
4. Куда доставить (район)?
5. Когда нужна доставка?
6. Оставьте номер — менеджер свяжется с точным расчётом.

ПРИМЕРЫ ПРАВИЛЬНЫХ ОТВЕТОВ:
Клиент: Нужен бетон М300
Бот: Понял! М300 — от 22 000 тг/м³. Какой объём нужен?

Клиент: 10 кубов
Бот: Отлично! Куда доставить — какой район Алматы?

Клиент: А сколько стоит бетононасос?
Бот: Бетононасос — от 25 000 тг/час. На какую высоту нужно подать бетон?

Клиент: Примерно цену
Бот: М300 — от 22 000 тг/м³. Доставка миксером — от 5000 тг. Какой объём и марка нужны?

Клиент: Не важно
Бот: Хорошо! Уточните, что нужно — бетон или бетононасос?
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
