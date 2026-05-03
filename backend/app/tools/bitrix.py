import json

import httpx

from app.config import settings
from app.prompts import HANDOVER_PROMPT

BITRIX_URL = settings.BITRIX_WEBHOOK_URL


def _format_collected_entities(entities: dict) -> str:
    purpose_map = {
        "investment": "Инвестиция",
        "living": "Для проживания",
    }
    summary_lines = [
        f"Имя: {entities.get('contact_name') or 'не указано'}",
        f"Телефон: {entities.get('contact_phone') or 'не указано'}",
        f"Бюджет от: {entities.get('budget_min') if entities.get('budget_min') is not None else 'не указано'}",
        f"Бюджет до: {entities.get('budget_max') if entities.get('budget_max') is not None else 'не указано'}",
        f"Комнат: {entities.get('rooms') if entities.get('rooms') is not None else 'не указано'}",
        f"Цель: {purpose_map.get(entities.get('purpose'), 'не указано')}",
        f"Район: {entities.get('district') or 'не указано'}",
        f"ЖК: {entities.get('complex_name') or 'не указано'}",
    ]
    return "\n".join(summary_lines)


async def check_handover_needed(message: str, conversation_history: list) -> tuple[bool, str]:
    history_text = "\n".join(
        [
            f"{'Клиент' if m['role']=='user' else 'Бот'}: {m['content']}"
            for m in conversation_history[-10:]
        ]
    )

    prompt = HANDOVER_PROMPT.format(history_text=history_text, message=message)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json={
                "model": "gpt-4o",
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [{"role": "user", "content": prompt}],
            },
        )

    data = response.json()
    result_text = data["choices"][0]["message"]["content"].strip()

    try:
        result = json.loads(result_text)
        return result["handover"], result["reason"]
    except Exception:
        return False, ""


async def create_bitrix_lead(entities: dict, conversation_history: list, reason: str = "") -> dict:
    entities_summary = _format_collected_entities(entities)
    history_text = "\n".join(
        [
            f"{'Клиент' if m['role']=='user' else 'Бот'}: {m['content']}"
            for m in conversation_history
        ]
    )

    source_desc = (
        "Клиент готов к покупке — WhatsApp Bot"
        if reason == "purchase_ready"
        else "Клиент запросил менеджера — WhatsApp Bot"
    )

    lead_data = {
        "fields": {
            "TITLE": f"Лид от бота — {entities.get('contact_name', 'Без имени')}",
            "NAME": entities.get("contact_name", ""),
            "PHONE": [{"VALUE": entities.get("contact_phone", ""), "VALUE_TYPE": "WORK"}],
            "OPPORTUNITY": entities.get("budget_max", 0),
            "COMMENTS": (
                f"Причина: {source_desc}\n\n"
                f"Собранные данные:\n{entities_summary}\n\n"
                f"Полная история диалога:\n{history_text}"
            ),
            "SOURCE_DESCRIPTION": "WhatsApp Bot",
        },
        "params": {"REGISTER_SONET_EVENT": "Y"},
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BITRIX_URL}/crm.lead.add", json=lead_data)

    return response.json()
