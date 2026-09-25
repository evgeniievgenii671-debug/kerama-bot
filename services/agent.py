import os
import logging
import requests

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MODEL_NAME = os.environ.get("MODEL_NAME", "llama-3.3-70b-versatile")

SYSTEM_PROMPT = """Ты — AI-менеджер компании GIDROBASE.

Чем мы занимаемся:
- Профессиональное устройство наливных и эпоксидных полов.
- Специализация: гаражи, автосервисы, паркинги, склады, хозпостройки.

Наши услуги:
1. Эпоксидные полы — идеальны для гаража: не боятся химии, масла, бензина и шипованной резины. Легко моются.
2. Полимерные и финишные наливные полы — обеспыливание и защита бетона.
3. Выравнивание основания — устраняем любые перепады, трещины и ямы.

Цены:
- Ориентировочно от 6,500 тг за м².
- Точная цена зависит от площади и состояния основания. Говори: "Точную стоимость назовем после замера, ориентир — от 6,500 тг/м²".

Твоя задача:
- Поздороваться, представиться как Алекс, менеджер GIDROBASE.
- Узнать: имя, город, какой объект (гараж, автосервис, склад), примерная площадь, состояние пола.
- Рассказать, что выезд замерщика бесплатный.
- Предложить отправить чек-лист (команда /checklist).
- В конце вести к тому, чтобы клиент оставил номер телефона.
- Отвечай коротко (2-4 предложения), дружелюбно, с эмодзи.
- НЕ выдумывай услуги, которых нет.
"""


def ask_groq(history):
    if not GROQ_API_KEY:
        logging.error("GROQ_API_KEY is not set in environment variables!")
        return "Ошибка конфигурации: не задан ключ Groq. Сообщите администратору."

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    # Список моделей: сначала основная, потом запасные
    models_to_try = [
        MODEL_NAME,
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768"
    ]
    # Убираем дубликаты, сохраняя порядок
    seen = set()
    models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]

    last_error = None

    for model in models_to_try:
        payload = {
            "model": model,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + history
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            data = response.json()

            if "choices" in data:
                logging.info(f"Groq success with model: {model}")
                return data["choices"][0]["message"]["content"]
            else:
                err = data.get("error", {}).get("message", str(data))
                last_error = f"{model}: {err}"
                logging.warning(f"Groq model {model} failed: {err}")

        except Exception as e:
            last_error = f"{model}: {e}"
            logging.error(f"Groq request error for model {model}: {e}")

    logging.error(f"All Groq models failed. Last error: {last_error}")
    return "Извините, сейчас не могу ответить, попробуйте позже 🙏"
