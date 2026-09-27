import os
import logging
import requests

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

SYSTEM_PROMPT = """Ты — Алекс, менеджер GidroBase (Алматы).

УСЛУГИ:
1. Гидроизоляция кровель — наплавляемая, обмазочная, ремонт, устранение протечек. Для ЖК, складов, ТРЦ, террас, паркингов.
2. Полы — эпоксидные, полиуретановые, 3D, бетонные. Для гаражей, паркингов, складов, автосервисов, производств.

ФАКТЫ:
- 10+ лет опыта, 120+ объектов
- Свои бригады, морозостойкие материалы
- Срок 3–5 дней
- Гарантия по договору до 10 лет
- Выезд инженера на замер — БЕСПЛАТНО

ПРАВИЛА:
- 1-2 предложения. С эмодзи.
- ОДИН вопрос за раз.
- Запоминай имя и используй его.
- Точные цены не называй — только инженер после замера.
- Веди к номеру телефона.

ПОРЯДОК:
1. Имя
2. Кровля или полы?
3. Объект и город
4. Площадь
5. Телефон

Примеры:
- «Приятно познакомиться, Евгений! Вас интересует кровля или полы? 🏠»
- «Понял! Какой у вас объект?»
- «Отлично! Оставьте номер — инженер приедет бесплатно 👍»
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
