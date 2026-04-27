import json
from typing import Any
from app.core.config import get_settings


class MemoryCache:
    def __init__(self):
        self.store: dict[str, str] = {}

    def get(self, key: str) -> Any:
        raw = self.store.get(key)
        return json.loads(raw) if raw else None

    def set(self, key: str, value: Any, ex: int | None = None) -> None:
        self.store[key] = json.dumps(value, ensure_ascii=False)


class RedisCache(MemoryCache):
    def __init__(self):
        try:
            import redis

            self.client = redis.from_url(get_settings().redis_url, socket_connect_timeout=0.2)
            self.client.ping()
            self.available = True
        except Exception:
            self.available = False
            super().__init__()

    def get(self, key: str) -> Any:
        if not self.available:
            return super().get(key)
        raw = self.client.get(key)
        return json.loads(raw) if raw else None

    def set(self, key: str, value: Any, ex: int | None = None) -> None:
        if not self.available:
            return super().set(key, value, ex)
        self.client.set(key, json.dumps(value, ensure_ascii=False), ex=ex)


cache = RedisCache()

