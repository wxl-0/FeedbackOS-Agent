from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    task: str
    user_id: str
    project_id: int
    conversation_id: str
    run_id: int
    messages: list[dict[str, str]]
    conversation_summary: str
    current_focus: str
    uploaded_file_id: int | None
    selected_cluster_id: int | None
    selected_opportunity_id: int | None
    retrieved_feedback: list[dict[str, Any]]
    evidence_summary: dict[str, Any]
    metric_summary: str
    agent_steps: list[dict[str, Any]]
    step_summaries: list[str]
    draft_prd: str
    reviewer_result: dict[str, Any]
    needs_human_review: bool
    final_output: str
