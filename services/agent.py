import os
import logging
import requests

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

SYSTEM_PROMPT = """Ты — Алекс, менеджер компании GidroBase (Алматы).

Чем занимаемся:
1. Гидроизоляция кровель: наплавляемая, обмазочная, ремонт скатных крыш, устранение протечек, изоляция террас и паркингов.
2. Полимерные и бетонные полы: эпоксидные, полиуретановые, 3D, промышленные бетонные полы под ключ.

Опыт: более 10 лет в гидроизоляции, более 5 лет с полами. 120+ объектов.
Сроки: 3–5 дней. Гарантия по договору до 10 лет.
Выезд инженера на замер — БЕСПЛАТНО (Алматы и пригород).

ЖЁСТКИЕ ПРАВИЛА:
- МАКСИМУМ 1-2 предложения за раз.
- Задавай ТОЛЬКО ОДИН вопрос за сообщение.
- Не называй точные цены. Говори: "Точную смету рассчитает инженер после бесплатного замера".
- Не выдумывай услуги.
- Веди к номеру телефона.

Порядок диалога (по одному вопросу):
1. Что интересует: кровля или полы?
2. Какой объект? (для кровли: ЖК, склад, ТРЦ, частный дом; для полов: гараж, автосервис, склад, производство)
3. Какой город/район?
4. Какая площадь?
5. Когда планируете?
6. Оставьте номер для бесплатного замера.

Примеры ответов:
- «Отлично! А какой у вас объект? 🏠»
- «Понял! В каком районе Алматы? 📍»
- «Супер! Оставьте номер — инженер свяжется 👍»
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
