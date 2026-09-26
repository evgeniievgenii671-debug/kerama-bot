import os
import logging
import requests

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

SYSTEM_PROMPT = """Ты — Алекс, менеджер GIDROBASE. Продаём эпоксидные и наливные полы.

Услуги: гаражи, автосервисы, паркинги, склады, хозпостройки.
Цена: от 6500 тг/м². Точную — после бесплатного замера.

ТВОЯ ЗАДАЧА — вести диалог и заполнить карточку клиента:
1. Имя
2. Объект (гараж/автосервис/склад)
3. Город
4. Площадь
5. Состояние пола
6. Телефон

ПРАВИЛА:
- МАКСИМУМ 1-2 предложения за раз.
- Задавай ТОЛЬКО ОДИН вопрос за сообщение.
- Используй то, что клиент уже сказал (не переспрашивай имя).
- Если клиент просит фото/примеры — скажи: "Сейчас пришлю примеры" (бот сам отправит).
- Не выдумывай услуги.
- Веди к номеру телефона.

Порядок (по одному вопросу):
имя → объект → город → площадь → телефон

Примеры:
- «Приятно познакомиться, Евгений! Какой у вас объект? 🏠»
- «Отлично! А в каком вы городе? 📍»
- «Понял! Сколько примерно м²?»
- «Супер! Оставьте номер — замерщик свяжется 👍»
"""


def get_available_models():
    try:
        r = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            timeout=10
        )
        return [m["id"] for m in r.json().get("data", [])]
    except Exception as e:
        logging.error(f"Ошибка списка моделей: {e}")
        return []


def pick_best_model(models):
    priorities = ["llama-3.3-70b", "llama-3.1-70b", "llama3-70b",
                  "llama-3.1-8b", "llama3-8b", "llama", "gemma", "mixtral"]
    for pref in priorities:
        for m in models:
            if pref in m.lower():
                return m
    return models[0] if models else None


def ask_groq(history):
    if not GROQ_API_KEY:
        return "Ошибка конфигурации."

    models = get_available_models()
    if not models:
        return "Проблема с AI. Попробуйте позже 🙏"

    best = pick_best_model(models)
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    for model in [best] + [m for m in models if m != best][:4]:
        payload = {
            "model": model,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + history
        }
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=30)
            data = r.json()
            if "choices" in data:
                logging.info(f"✅ {model}")
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logging.error(f"Ошибка {model}: {e}")

    return "Извините, сейчас не могу ответить 🙏"
