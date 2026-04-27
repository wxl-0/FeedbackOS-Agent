import hashlib
import math
from app.core.config import get_settings


DIM = 64


def mock_embedding(text: str, dim: int = DIM) -> list[float]:
    vec = [0.0] * dim
    tokens = list(text or "") + (text or "").lower().split()
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:2], "big") % dim
        sign = 1 if digest[2] % 2 == 0 else -1
        vec[idx] += sign * (1 + digest[3] / 255)
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


async def embed_text(text: str) -> list[float]:
    settings = get_settings()
    if settings.use_mock_llm or not settings.llm_api_key:
        return mock_embedding(text)
    try:
        import httpx

        async with httpx.AsyncClient(timeout=20) as client:
            res = await client.post(
                f"{settings.resolved_base_url.rstrip('/')}/embeddings",
                headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                json={"model": settings.resolved_embedding_model, "input": text[:8000]},
            )
            res.raise_for_status()
            return res.json()["data"][0]["embedding"]
    except Exception:
        return mock_embedding(text)
