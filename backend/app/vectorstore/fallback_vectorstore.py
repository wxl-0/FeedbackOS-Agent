import math
import time
from typing import Any
from sqlalchemy.orm import Session
from app.db.models import RetrievalLog


def cosine(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    dot = sum(a[i] * b[i] for i in range(n))
    na = math.sqrt(sum(x * x for x in a)) or 1
    nb = math.sqrt(sum(x * x for x in b)) or 1
    return dot / (na * nb)


class FallbackVectorStore:
    def __init__(self):
        self.collections: dict[str, list[dict[str, Any]]] = {
            "feedback_embeddings": [],
            "document_embeddings": [],
            "prd_embeddings": [],
        }

    def insert(self, collection: str, item: dict[str, Any]) -> None:
        self.collections.setdefault(collection, [])
        key = "feedback_id" if "feedback_id" in item else "chunk_id" if "chunk_id" in item else "prd_id"
        self.collections[collection] = [x for x in self.collections[collection] if x.get(key) != item.get(key)]
        self.collections[collection].append(item)

    def search(self, collection: str, query: str, embedding: list[float], top_k: int, filters: dict[str, Any] | None, db: Session | None = None, run_id: int | None = None) -> list[dict[str, Any]]:
        start = time.perf_counter()
        rows = self.collections.get(collection, [])
        filters = filters or {}
        scored = []
        for row in rows:
            if any(v is not None and str(row.get(k)) != str(v) for k, v in filters.items()):
                continue
            scored.append({**row, "similarity": cosine(embedding, row["embedding"])})
        scored.sort(key=lambda x: x["similarity"], reverse=True)
        result = scored[:top_k]
        if db:
            avg = sum(r["similarity"] for r in result) / len(result) if result else 0
            db.add(RetrievalLog(
                run_id=run_id, query=query, top_k=top_k, returned_count=len(result),
                avg_similarity=avg, no_result=not result,
                latency_ms=int((time.perf_counter() - start) * 1000),
            ))
            db.commit()
        return result


fallback_store = FallbackVectorStore()

