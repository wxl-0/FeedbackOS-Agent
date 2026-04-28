import copy
import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import CompressionLog


TEXT_FIELDS = {
    "text",
    "feedback_text",
    "feedback_summary",
    "chunk_text",
    "chunk_summary",
    "prd_markdown",
    "problem_statement",
}


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 2)


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _truncate_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n...[truncated by context window]"


def _compact_value(value: Any, text_limit: int = 800) -> Any:
    if isinstance(value, str):
        return _truncate_text(value, text_limit)
    if isinstance(value, list):
        return [_compact_value(item, text_limit) for item in value]
    if isinstance(value, dict):
        compacted = {}
        for key, item in value.items():
            limit = text_limit if key in TEXT_FIELDS else max(text_limit, 1200)
            compacted[key] = _compact_value(item, limit)
        return compacted
    return value


class ContextBuilder:
    """Builds bounded LLM input payloads before every model call.

    The system never sends raw uploaded files to the LLM. Agents pass structured
    records, retrieved evidence, summaries and task metadata through this builder,
    which applies a simple token budget and records compression metrics.
    """

    def __init__(self, db: Session, run_id: int | None, prompt_type: str):
        settings = get_settings()
        self.db = db
        self.run_id = run_id
        self.prompt_type = prompt_type
        self.max_input_tokens = settings.max_context_tokens
        self.reserved_output_tokens = settings.context_reserved_output_tokens
        self.effective_budget = max(1000, self.max_input_tokens - self.reserved_output_tokens)

    def build(self, payload: dict[str, Any]) -> dict[str, Any]:
        original = copy.deepcopy(payload)
        compacted = copy.deepcopy(payload)

        compacted = self._compact_lists(compacted)
        compacted = _compact_value(compacted)
        compacted["_context_window"] = {
            "max_input_tokens": self.max_input_tokens,
            "reserved_output_tokens": self.reserved_output_tokens,
            "policy": "structured records only; evidence trimmed before LLM call",
        }

        compacted = self._fit_budget(compacted)
        original_tokens = estimate_tokens(_json_dumps(original))
        compacted_tokens = estimate_tokens(_json_dumps(compacted))
        if compacted_tokens < original_tokens or original_tokens > self.effective_budget:
            self._log(original_tokens, compacted_tokens, compacted)
        return compacted

    def _compact_lists(self, payload: dict[str, Any]) -> dict[str, Any]:
        for key in ("evidence", "retrieved_feedback", "feedback", "documents"):
            rows = payload.get(key)
            if isinstance(rows, list):
                payload[key] = rows[: self._list_limit(key)]
        messages = payload.get("messages")
        if isinstance(messages, list) and len(messages) > 10:
            payload["conversation_summary"] = self._summarize_messages(messages[:-6])
            payload["messages"] = messages[-6:]
        return payload

    def _list_limit(self, key: str) -> int:
        if key in {"evidence", "retrieved_feedback"}:
            return 12
        return 8

    def _summarize_messages(self, messages: list[dict[str, Any]]) -> str:
        snippets = []
        for msg in messages[-8:]:
            role = msg.get("role", "unknown")
            content = _truncate_text(str(msg.get("content", "")), 180)
            snippets.append(f"{role}: {content}")
        return "\n".join(snippets)

    def _fit_budget(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = payload
        for text_limit in (600, 420, 260, 160):
            tokens = estimate_tokens(_json_dumps(result))
            if tokens <= self.effective_budget:
                break
            result = _compact_value(result, text_limit)
        return result

    def _log(self, original_tokens: int, compacted_tokens: int, payload: dict[str, Any]) -> None:
        summary = {
            "prompt_type": self.prompt_type,
            "original_tokens": original_tokens,
            "compacted_tokens": compacted_tokens,
            "effective_budget": self.effective_budget,
        }
        self.db.add(CompressionLog(
            run_id=self.run_id,
            compression_type="llm_context_window",
            original_tokens=original_tokens,
            compressed_tokens=compacted_tokens,
            compression_rate=1 - compacted_tokens / max(1, original_tokens),
            summary_text=_json_dumps(summary),
        ))
        self.db.commit()
