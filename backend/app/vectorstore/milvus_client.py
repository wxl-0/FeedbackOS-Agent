import time
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.embeddings import embed_text
from app.db.models import RetrievalLog
from app.vectorstore.fallback_vectorstore import fallback_store


COLLECTIONS = {
    "feedback_embeddings": "feedback_id",
    "document_embeddings": "chunk_id",
    "prd_embeddings": "prd_id",
}


def _escape(value: Any) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def _expr(filters: dict[str, Any] | None) -> str:
    parts = []
    for key, value in (filters or {}).items():
        if value is None:
            continue
        if isinstance(value, bool):
            parts.append(f"{key} == {str(value).lower()}")
        elif isinstance(value, (int, float)):
            parts.append(f"{key} == {value}")
        else:
            parts.append(f'{key} == "{_escape(value)}"')
    return " and ".join(parts)


def _parse_hit(hit: dict[str, Any]) -> dict[str, Any]:
    entity = hit.get("entity") or {}
    distance = hit.get("distance", hit.get("score", 0))
    return {**entity, "similarity": float(distance or 0)}


def _log_retrieval(db: Session | None, run_id: int | None, query: str, top_k: int, rows: list[dict[str, Any]], latency_ms: int) -> None:
    if not db:
        return
    avg = sum(row.get("similarity", 0) for row in rows) / len(rows) if rows else 0
    db.add(RetrievalLog(
        run_id=run_id,
        query=query,
        top_k=top_k,
        returned_count=len(rows),
        avg_similarity=avg,
        no_result=not rows,
        latency_ms=latency_ms,
    ))
    db.commit()


class MilvusBackend:
    def __init__(self, uri: str):
        from pymilvus import MilvusClient

        self.client = MilvusClient(uri=uri)
        self.dims: dict[str, int] = {}

    def ensure_collection(self, collection: str, dim: int) -> None:
        if self.dims.get(collection) == dim:
            return
        if not self.client.has_collection(collection):
            self.client.create_collection(
                collection_name=collection,
                dimension=dim,
                vector_field_name="embedding",
                metric_type="COSINE",
                auto_id=True,
                enable_dynamic_field=True,
            )
        self.client.load_collection(collection)
        self.dims[collection] = dim

    def upsert(self, collection: str, id_field: str, row_id: int, data: dict[str, Any]) -> None:
        self.ensure_collection(collection, len(data["embedding"]))
        try:
            self.client.delete(collection_name=collection, filter=f"{id_field} == {row_id}")
        except Exception:
            pass
        self.client.insert(collection_name=collection, data=[data])

    def search(self, collection: str, embedding: list[float], top_k: int, filters: dict[str, Any] | None) -> list[dict[str, Any]]:
        self.ensure_collection(collection, len(embedding))
        hits = self.client.search(
            collection_name=collection,
            data=[embedding],
            anns_field="embedding",
            limit=top_k,
            filter=_expr(filters),
            output_fields=["*"],
            search_params={"metric_type": "COSINE"},
        )
        return [_parse_hit(hit) for hit in (hits[0] if hits else [])]


class VectorClient:
    """Milvus-first vector facade with guaranteed in-memory fallback."""

    def __init__(self):
        self.settings = get_settings()
        self.using_fallback = True
        self.backend: MilvusBackend | None = None
        if self.settings.use_milvus:
            try:
                self.backend = MilvusBackend(self.settings.resolved_milvus_uri)
                self.using_fallback = False
            except Exception as exc:
                print(f"[vectorstore] Milvus unavailable, using fallback: {exc}")
                self.backend = None
                self.using_fallback = True

    def _fallback_insert(self, collection: str, data: dict[str, Any]) -> None:
        fallback_store.insert(collection, data)

    def _milvus_insert(self, collection: str, row_id: int, data: dict[str, Any]) -> bool:
        if not self.backend:
            return False
        try:
            self.backend.upsert(collection, COLLECTIONS[collection], row_id, data)
            return True
        except Exception as exc:
            print(f"[vectorstore] Milvus insert failed, using fallback: {exc}")
            return False

    async def insert_feedback_embedding(self, feedback_id: int, project_id: int, text: str, metadata: dict[str, Any]) -> None:
        emb = await embed_text(text)
        data = {"feedback_id": feedback_id, "project_id": project_id, "text": text[:8000], "embedding": emb, **metadata}
        if not self._milvus_insert("feedback_embeddings", feedback_id, data):
            self._fallback_insert("feedback_embeddings", data)

    async def insert_document_embedding(self, chunk_id: int, project_id: int, uploaded_file_id: int, text: str, metadata: dict[str, Any]) -> None:
        emb = await embed_text(text)
        data = {"chunk_id": chunk_id, "project_id": project_id, "uploaded_file_id": uploaded_file_id, "text": text[:8000], "embedding": emb, **metadata}
        if not self._milvus_insert("document_embeddings", chunk_id, data):
            self._fallback_insert("document_embeddings", data)

    async def insert_prd_embedding(self, prd_id: int, project_id: int, opportunity_id: int | None, text: str) -> None:
        emb = await embed_text(text)
        data = {"prd_id": prd_id, "project_id": project_id, "opportunity_id": opportunity_id, "text": text[:8000], "embedding": emb}
        if not self._milvus_insert("prd_embeddings", prd_id, data):
            self._fallback_insert("prd_embeddings", data)

    async def _search(self, collection: str, query: str, db: Session, top_k: int, filters: dict[str, Any] | None, run_id: int | None):
        emb = await embed_text(query)
        if self.backend:
            start = time.perf_counter()
            try:
                rows = self.backend.search(collection, emb, top_k, filters)
                _log_retrieval(db, run_id, query, top_k, rows, int((time.perf_counter() - start) * 1000))
                return rows
            except Exception as exc:
                print(f"[vectorstore] Milvus search failed, using fallback: {exc}")
        return fallback_store.search(collection, query, emb, top_k, filters, db, run_id)

    async def semantic_search_feedback(self, query: str, db: Session, top_k: int = 8, filters: dict[str, Any] | None = None, run_id: int | None = None):
        return await self._search("feedback_embeddings", query, db, top_k, filters, run_id)

    async def semantic_search_documents(self, query: str, db: Session, top_k: int = 8, filters: dict[str, Any] | None = None, run_id: int | None = None):
        return await self._search("document_embeddings", query, db, top_k, filters, run_id)

    async def search_similar_feedback_by_topic(self, topic: str, db: Session, top_k: int = 8, project_id: int = 1, run_id: int | None = None):
        return await self.semantic_search_feedback(topic, db, top_k, {"project_id": project_id}, run_id)


vector_client = VectorClient()
