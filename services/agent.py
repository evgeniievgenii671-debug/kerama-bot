import os
import logging
import requests

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

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


def get_available_models():
    """Запрашивает у Groq список доступных моделей."""
    try:
        r = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            timeout=10
        )
        data = r.json()
        models = [m["id"] for m in data.get("data", [])]
        logging.info(f"Доступные модели Groq: {models}")
        return models
    except Exception as e:
        logging.error(f"Не удалось получить список моделей: {e}")
        return []


def pick_best_model(models):
    """Выбирает лучшую модель из доступных."""
    # Приоритет: сначала большие llama, потом маленькие, потом всё остальное
    priorities = [
        "llama-3.3-70b",
        "llama-3.1-70b",
        "llama3-70b",
        "llama-3.1-8b",
        "llama3-8b",
        "llama",
        "gemma",
        "mixtral",
    ]
    for pref in priorities:
        for m in models:
            if pref in m.lower():
                return m
    # Если ничего не подошло — берём первую попавшуюся
    return models[0] if models else None


def ask_groq(history):
    if not GROQ_API_KEY:
        logging.error("GROQ_API_KEY не задан!")
        return "Ошибка конфигурации: не задан ключ Groq."

    # Получаем список моделей
    models = get_available_models()
    if not models:
        return "Извините, проблема с доступом к AI. Попробуйте позже 🙏"

    best_model = pick_best_model(models)
    logging.info(f"Выбрана модель: {best_model}")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    # Пробуем лучшую, потом остальные
    models_to_try = [best_model] + [m for m in models if m != best_model]

    for model in models_to_try[:5]:  # максимум 5 попыток
        payload = {
            "model": model,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + history
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            data = response.json()
            if "choices" in data:
                logging.info(f"✅ Успех с моделью: {model}")
                return data["choices"][0]["message"]["content"]
            else:
                err = data.get("error", {}).get("message", str(data))
                logging.warning(f"Модель {model} не сработала: {err}")
        except Exception as e:
            logging.error(f"Ошибка запроса к {model}: {e}")

    logging.error("Все модели Groq не сработали.")
    return "Извините, сейчас не могу ответить, попробуйте позже 🙏"
