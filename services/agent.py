import os
import logging
import requests

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

SYSTEM_PROMPT = """Ты — Алекс, менеджер GIDROBASE.
Превращаем бетон в идеальный пол.
Шлифуем ➔ Ровняем ➔ Заливаем прочную эпоксидку.
Гаражи, магазины, склады под ключ.
Услуги: гаражи, автосервисы, паркинги, склады. Выравнивание основания.
Цена: от 6500 тг/м². Точную — после бесплатного замера.

ЖЁСТКИЕ ПРАВИЛА:
- МАКСИМУМ 1-2 предложения за раз. Не больше!
- Задавай ТОЛЬКО ОДИН вопрос за сообщение.
- Не перечисляй всё сразу.
- Не повторяй то, что уже спросил.

Порядок диалога (по одному вопросу):
1. Какой объект?
2. Какой город?
3. Какая площадь?
4. Оставь номер телефона.

Примеры ответов:
- «Отлично! А какой город? 📍»
- «Понял! Сколько примерно м²?»
- «Супер! Оставь номер — замерщик свяжется 👍»
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
    return models[0] if models else None


def ask_groq(history):
    """Отправляет историю диалога в Groq и возвращает ответ."""
    if not GROQ_API_KEY:
        logging.error("GROQ_API_KEY не задан!")
        return "Ошибка конфигурации: не задан ключ Groq."

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

    models_to_try = [best_model] + [m for m in models if m != best_model]

    for model in models_to_try[:5]:
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
