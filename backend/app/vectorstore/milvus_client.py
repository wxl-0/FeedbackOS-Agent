from typing import Any
from sqlalchemy.orm import Session
from app.core.embeddings import embed_text
from app.vectorstore.fallback_vectorstore import fallback_store


class VectorClient:
    """Milvus facade with guaranteed in-memory fallback for local demos."""

    def __init__(self):
        self.using_fallback = True

    async def insert_feedback_embedding(self, feedback_id: int, project_id: int, text: str, metadata: dict[str, Any]) -> None:
        emb = await embed_text(text)
        fallback_store.insert("feedback_embeddings", {"feedback_id": feedback_id, "project_id": project_id, "text": text, "embedding": emb, **metadata})

    async def insert_document_embedding(self, chunk_id: int, project_id: int, uploaded_file_id: int, text: str, metadata: dict[str, Any]) -> None:
        emb = await embed_text(text)
        fallback_store.insert("document_embeddings", {"chunk_id": chunk_id, "project_id": project_id, "uploaded_file_id": uploaded_file_id, "text": text, "embedding": emb, **metadata})

    async def insert_prd_embedding(self, prd_id: int, project_id: int, opportunity_id: int | None, text: str) -> None:
        emb = await embed_text(text)
        fallback_store.insert("prd_embeddings", {"prd_id": prd_id, "project_id": project_id, "opportunity_id": opportunity_id, "text": text, "embedding": emb})

    async def semantic_search_feedback(self, query: str, db: Session, top_k: int = 8, filters: dict[str, Any] | None = None, run_id: int | None = None):
        emb = await embed_text(query)
        return fallback_store.search("feedback_embeddings", query, emb, top_k, filters, db, run_id)

    async def semantic_search_documents(self, query: str, db: Session, top_k: int = 8, filters: dict[str, Any] | None = None, run_id: int | None = None):
        emb = await embed_text(query)
        return fallback_store.search("document_embeddings", query, emb, top_k, filters, db, run_id)

    async def search_similar_feedback_by_topic(self, topic: str, db: Session, top_k: int = 8, project_id: int = 1, run_id: int | None = None):
        return await self.semantic_search_feedback(topic, db, top_k, {"project_id": project_id}, run_id)


vector_client = VectorClient()
