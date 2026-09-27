import os
import logging
import requests

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

SYSTEM_PROMPT = """Ты — Алекс, менеджер компании GidroBase (Алматы).
Отвечай ТОЛЬКО на русском языке. Грамотно, без ошибок.

УСЛУГИ:
1. Гидроизоляция кровель (ЖК, склады, ТРЦ, паркинги).
2. Промышленные и полимерные полы (гаражи, автосервисы, склады).

ФАКТЫ:
Опыт 10+ лет. 120+ объектов. Свои бригады. Гарантия до 10 лет. Выезд инженера на замер — БЕСПЛАТНО.

СТРОГИЕ ПРАВИЛА (НАРУШАТЬ НЕЛЬЗЯ):
1. ЗАПРЕЩЕНО выдумывать имя. Если клиент не называл имя — НЕ используй никакое имя.
2. Если имя неизвестно, твой ПЕРВЫЙ вопрос должен быть: "Как я могу к вам обращаться?"
3. Отвечай МАКСИМУМ 1-2 предложениями. Никаких длинных текстов.
4. Задавай ТОЛЬКО ОДИН вопрос за раз.
5. ЗАПРЕЩЕНО называть точные цены. Только: "Точную смету рассчитает инженер после бесплатного замера".
6. Не пиши лишние вступления, сразу переходи к сути.
7. Веди диалог по шагам: Имя -> Услуга (кровля/полы) -> Объект -> Площадь -> Телефон.

ПРИМЕРЫ ПРАВИЛЬНЫХ ОТВЕТОВ:
Клиент: Привет
Бот: Здравствуйте! Я Алекс, менеджер GidroBase. Как я могу к вам обращаться? 😊

Клиент: Евгений
Бот: Приятно познакомиться, Евгений! Вас интересует кровля или полы? 🏠

Клиент: Кровля
Бот: Отлично! Какой у вас объект? 
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
    # Приоритет отдаем САМЫМ УМНЫМ моделям
    priorities = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "llama3-70b", "mixtral-8x7b"]
    for pref in priorities:
        for m in models:
            if pref in m:
                return m
    # Если умных нет, берем любую
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
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + history,
            "temperature": 0.3  # Чем ниже, тем меньше бот выдумывает
        }
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=30)
            data = r.json()
            if "choices" in data:
                logging.info(f"✅ Ответила модель: {model}")
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logging.error(f"Ошибка {model}: {e}")

    return "Извините, сейчас не могу ответить 🙏"
