import json

import redis.asyncio as redis

from app.config import settings

redis_client = redis.from_url(settings.REDIS_URL)


async def get_memory(phone: str) -> dict:
    try:
        data = await redis_client.get(f"chat:{phone}")
        if data:
            return json.loads(data)
    except Exception:
        pass
    return {"messages": [], "entities": {}}


async def save_memory(phone: str, memory: dict) -> None:
    try:
        await redis_client.set(
            f"chat:{phone}",
            json.dumps(memory, ensure_ascii=False),
            ex=86400,
        )
    except Exception as e:
        print(f"[Redis] Save error: {e}")


async def clear_memory(phone: str) -> None:
    await redis_client.delete(f"chat:{phone}")


async def set_paused(phone: str) -> None:
    await redis_client.set(f"paused:{phone}", "1", ex=86400)


async def clear_paused(phone: str) -> None:
    await redis_client.delete(f"paused:{phone}")


async def is_paused(phone: str) -> bool:
    result = await redis_client.get(f"paused:{phone}")
    return result is not None


async def list_chat_phones() -> list[str]:
    phones: list[str] = []
    async for key in redis_client.scan_iter(match="chat:*"):
        decoded = key.decode() if isinstance(key, bytes) else str(key)
        phones.append(decoded.replace("chat:", "", 1))
    phones.sort()
    return phones
