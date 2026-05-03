import json
import re

import httpx

from app.config import settings


async def extract_entities(message: str, current_entities: dict) -> dict:
    prompt = f"""Ты извлекаешь параметры клиента из сообщения в агентстве недвижимости.

Уже известные данные о клиенте:
{json.dumps(current_entities, ensure_ascii=False)}

Новое сообщение клиента: "{message}"

Извлеки только то что явно упомянуто в новом сообщении.
Если параметр не упомянут — верни null для него.
Не затирай уже известные данные — они будут смёржены отдельно.

Параметры:
- contact_name: имя клиента (строка или null)
- contact_phone: номер телефона (строка или null)
- budget_min: минимальный бюджет в тенге (число или null)
- budget_max: максимальный бюджет в тенге (число или null)
- rooms: количество комнат (число или null)
- purpose: цель — "investment" если инвестиция, "living" если для жилья, иначе null
- district: район (строка или null)
- complex_name: название ЖК (строка или null)

Ответь строго JSON без markdown:
{{"contact_name": null, "contact_phone": null, "budget_min": null, "budget_max": null, "rooms": null, "purpose": null, "district": null, "complex_name": null}}"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={
                    "model": "gpt-4o-mini",
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=10.0,
            )

        raw = response.json()["choices"][0]["message"]["content"]
        cleaned = re.sub(r"```json|```", "", raw).strip()
        new_entities = json.loads(cleaned)

        merged = {**current_entities}
        for key, value in new_entities.items():
            if value is not None:
                merged[key] = value

        print(f"[Entities] {merged}")
        return merged
    except Exception as e:
        print(f"[Entities] Error: {e}")
        return current_entities
