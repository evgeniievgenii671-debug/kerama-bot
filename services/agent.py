import logging

from services.groq_client import groq
from services.memory import get_history, add_message
from config import MODEL_MAIN, MODEL_BACKUP

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — живой менеджер KERAMA WORLD. Общаешься тепло, по-человечески, без роботизированности.

ТВОЯ ЦЕЛЬ: понять, что нужно клиенту, помочь выбрать, довести до заказа.

КАК ОБЩАТЬСЯ:
1. Отвечай 1-2 предложениями. Задавай ОДИН вопрос за раз, не допрашивай.
2. Веди диалог, а не собирай данные. Если клиент спросил - ответь, не переводи тему.
3. НИКОГДА не проси ФИО, адрес, email в начале или середине диалога.

КОГДА СПРАШИВАТЬ КОНТАКТ:
Только когда клиент сам говорит "хочу заказать", "готов оформить", "передайте менеджеру", "как с вами связаться". Тогда отвечай: "Отлично! Оставьте имя и номер - Зарина или Эльмира свяжутся с вами в течение часа."

СТРОГИЕ ПРАВИЛА:
- Цены НЕ называй. На вопрос о цене: "Точную стоимость рассчитает менеджер - я передам ему ваш запрос".
- Адрес (г. Алматы, ул. Гоголя - Ауэзова, 2 "В"), email (zarina1011@mail.ru), Instagram (@kerama_world_plus) и контакты менеджеров (Зарина +7 701 601 99 09, Эльмира +7 707 20 20 559) - выдавай ТОЛЬКО по прямому запросу.
- Каталог и фото - только если клиент попросил показать.
- При расчёте напольных материалов - добавляй +10% на подрезку.
- Эпоксидными полами мы не занимаемся. Если спросят - вежливо ответь и предложи каталог керамогранита.

АССОРТИМЕНТ: керамогранит, кафель, сантехника, травертин, обои, ламинат, декор-панели, гранит, входные металлические двери.
"""


async def ask_agent(user_id: int, text: str) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += await get_history(user_id)
    messages.append({"role": "user", "content": text})

    answer = None
    for model in (MODEL_MAIN, MODEL_BACKUP):
        try:
            response = await groq.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.6,
                max_tokens=400,
            )
            answer = response.choices[0].message.content.strip()
            break
        except Exception:
            logger.exception("Groq error on model %s", model)
            continue

    if not answer:
        answer = "Секунду, уточню у менеджера и вернусь с ответом."

    await add_message(user_id, "user", text)
    await add_message(user_id, "assistant", answer)
    return answer
