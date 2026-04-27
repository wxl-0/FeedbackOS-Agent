from datetime import datetime
import json
from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session
from app.agents.cluster_agent import generate_clusters
from app.agents.compression_node import compress_evidence, compress_steps
from app.agents.metric_analyst_agent import analyze_metrics
from app.agents.opportunity_agent import generate_opportunities
from app.agents.prd_writer_agent import generate_prd
from app.agents.reviewer_agent import review_prd
from app.agents.state import AgentState
from app.db.models import AgentRun, AgentStep, ConversationMessage, FeedbackItem, InsightCluster, Opportunity, ProjectMemory, UploadedFile
from app.services.feedback_service import analyze_feedback_item, serialize_feedback
from app.services.observability_service import agent_step
from app.vectorstore.milvus_client import vector_client


def build_chat_final_output(db: Session, state: AgentState, project_id: int, conversation_id: str | None) -> str:
    task = state.get("task", "")
    reviewer = state.get("reviewer_result") or {}
    feedback_count = db.query(FeedbackItem).filter_by(project_id=project_id, conversation_id=conversation_id).count()
    clusters = db.query(InsightCluster).filter_by(project_id=project_id, conversation_id=conversation_id).order_by(InsightCluster.feedback_count.desc()).limit(3).all()
    opportunities = db.query(Opportunity).filter_by(project_id=project_id, conversation_id=conversation_id).order_by(Opportunity.priority_score.desc()).limit(3).all()
    selected_opp = db.get(Opportunity, state.get("selected_opportunity_id")) if state.get("selected_opportunity_id") else None
    prd_title = selected_opp.title if selected_opp else (opportunities[0].title if opportunities else "")
    quality_score = reviewer.get("quality_score")
    completeness = reviewer.get("prd_completeness_score")
    problems = reviewer.get("problems") or []

    if feedback_count == 0:
        return "我还没有在当前会话里找到可分析的反馈数据。你可以先用输入框右侧的加号上传 CSV、Excel、TXT、MD 或 DOCX 文件，我会先解析入库，再基于当前会话的数据继续分析。"

    task_lower = task.lower()
    asks_prd = "prd" in task_lower or "需求文档" in task or "产品需求" in task
    asks_review = "review" in task_lower or "评审" in task or "评分" in task
    asks_opportunity = "机会" in task or "优先级" in task or "p0" in task_lower

    lines: list[str] = []
    if asks_review:
        lines.append(f"我已经完成这版 PRD 的评审。Reviewer 评分是 {quality_score if quality_score is not None else 'N/A'}，完整度是 {completeness if completeness is not None else 'N/A'}。")
    elif asks_prd:
        lines.append(f"我已经基于当前会话的 {feedback_count} 条反馈生成了 PRD 草稿：{prd_title or '当前最高优先级机会点'}。你可以在右侧 PRD 面板直接编辑、保存或导出 Markdown/DOCX。")
    elif asks_opportunity:
        lines.append(f"我已经从当前会话的 {feedback_count} 条反馈里提炼机会点，并按影响、紧急度、置信度、战略匹配和成本做了优先级评分。")
    else:
        lines.append(f"我分析了当前会话的 {feedback_count} 条反馈，并完成了痛点聚类、机会点评估、PRD 草稿和 Reviewer 检查。")

    if clusters:
        cluster_text = "；".join([f"{c.cluster_name}（{c.feedback_count} 条，负面率 {round((c.negative_ratio or 0) * 100)}%）" for c in clusters])
        lines.append(f"主要痛点集中在：{cluster_text}。")

    if opportunities:
        opp_text = "；".join([f"{o.priority_level} {o.title}（{round(o.priority_score, 2)}）" for o in opportunities])
        lines.append(f"优先处理建议：{opp_text}。")

    if prd_title and not asks_prd:
        lines.append(f"我也生成了一版 PRD 草稿：{prd_title}，右侧 PRD 面板可以继续调整。")

    if quality_score is not None:
        lines.append(f"Reviewer 当前评分：{quality_score}。")
    if problems:
        lines.append(f"需要注意：{problems[0]}")
    else:
        lines.append("目前没有发现明显的结构性缺口，但建议你人工确认业务假设和上线范围。")

    return "\n".join(lines)


async def run_agent_workflow(db: Session, task: str, project_id: int = 1, user_id: str = "local_user", conversation_id: str | None = None) -> AgentState:
    run = AgentRun(project_id=project_id, conversation_id=conversation_id, user_task=task, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    async def orchestrator(state: AgentState) -> AgentState:
        with agent_step(db, run.id, "Orchestrator Agent", "route_task", "task_router", {"task": state["task"]}) as out:
            out["step_summary"] = "识别为基于已上传数据的反馈分析、机会点评估与 PRD 生成任务。"
        return {**state, "current_focus": "generate_opportunities_and_prd"}

    async def file_intake(state: AgentState) -> AgentState:
        with agent_step(db, run.id, "File Intake Agent", "verify_uploaded_sources", "sqlite_query") as out:
            files = db.query(UploadedFile).filter_by(project_id=project_id, conversation_id=conversation_id).count()
            count = db.query(FeedbackItem).filter_by(project_id=project_id, conversation_id=conversation_id).count()
            out["feedback_count"] = count
            out["file_count"] = files
            out["step_summary"] = f"确认当前会话中已有 {files} 个文件、{count} 条入库反馈；未读取完整原始文件。"
        return state

    async def data_intake(state: AgentState) -> AgentState:
        with agent_step(db, run.id, "Data Intake Agent", "normalize_existing_records", "sqlite_update") as out:
            rows = db.query(FeedbackItem).filter_by(project_id=project_id, conversation_id=conversation_id).filter(FeedbackItem.feedback_summary.is_(None)).limit(100).all()
            for item in rows:
                await analyze_feedback_item(db, item, run.id)
            out["step_summary"] = f"补齐 {len(rows)} 条反馈的标签与摘要。"
        return state

    async def feedback_analyst(state: AgentState) -> AgentState:
        with agent_step(db, run.id, "Feedback Analyst Agent", "label_distribution", "sqlite_query") as out:
            rows = db.query(FeedbackItem).filter_by(project_id=project_id, conversation_id=conversation_id).limit(200).all()
            out["step_summary"] = f"完成 {len(rows)} 条反馈的情绪、模块、严重度分析。"
        return state

    async def retrieval(state: AgentState) -> AgentState:
        with agent_step(db, run.id, "Retrieval Agent", "semantic_search_feedback", "vector_search", {"query": state["task"]}) as out:
            hits = await vector_client.semantic_search_feedback(state["task"], db, top_k=12, filters={"project_id": project_id, "conversation_id": conversation_id}, run_id=run.id)
            if not hits:
                rows = db.query(FeedbackItem).filter_by(project_id=project_id, conversation_id=conversation_id).limit(12).all()
                hits = [{**serialize_feedback(r), "feedback_id": r.id, "text": r.feedback_text, "similarity": 0} for r in rows]
            retrieved = [{"id": h.get("feedback_id") or h.get("id"), "feedback_text": h.get("text") or h.get("feedback_text"), "sentiment_label": h.get("sentiment_label"), "product_module": h.get("product_module")} for h in hits]
            out["retrieved_feedback"] = retrieved
            out["step_summary"] = f"召回 {len(hits)} 条相关反馈证据，并写入 retrieval_logs。"
        return {**state, "retrieved_feedback": retrieved}

    async def cluster(state: AgentState) -> AgentState:
        with agent_step(db, run.id, "Cluster Agent", "generate_clusters", "cluster_rules") as out:
            clusters = generate_clusters(db, project_id, conversation_id)
            out["step_summary"] = f"生成/更新 {len(clusters)} 个痛点聚类。"
        return state

    async def metric(state: AgentState) -> AgentState:
        with agent_step(db, run.id, "Metric Analyst Agent", "analyze_metrics", "metric_trend") as out:
            metric_summary = analyze_metrics(db, project_id, conversation_id)
            out["step_summary"] = metric_summary
        return {**state, "metric_summary": metric_summary}

    async def opportunity(state: AgentState) -> AgentState:
        with agent_step(db, run.id, "Opportunity Agent", "score_opportunities", "priority_formula") as out:
            opps = generate_opportunities(db, project_id, conversation_id)
            top = sorted(opps, key=lambda x: x.priority_score, reverse=True)
            selected = top[0].id if top else None
            out["step_summary"] = f"生成 {len(opps)} 个机会点，最高优先级为 {top[0].priority_level if top else 'N/A'}。"
        return {**state, "selected_opportunity_id": selected}

    async def compression(state: AgentState) -> AgentState:
        with agent_step(db, run.id, "Compression Node", "compress_evidence", "context_compression") as out:
            evidence_summary = compress_evidence(db, run.id, state.get("retrieved_feedback", []), state["task"])
            out["step_summary"] = f"压缩 {len(state.get('retrieved_feedback', []))} 条证据为 evidence_summary。"
        return {**state, "evidence_summary": evidence_summary}

    async def prd_writer(state: AgentState) -> AgentState:
        if not state.get("selected_opportunity_id"):
            return {**state, "draft_prd": ""}
        with agent_step(db, run.id, "PRD Writer Agent", "generate_prd", "prd_writer") as out:
            prd = await generate_prd(db, state["selected_opportunity_id"], project_id, state.get("metric_summary", ""), conversation_id)
            out["prd_id"] = prd.id
            out["step_summary"] = f"生成 PRD 草稿 #{prd.id}：{prd.title}。"
        return {**state, "draft_prd": prd.prd_markdown, "current_prd_id": prd.id}

    async def reviewer(state: AgentState) -> AgentState:
        prd_id = state.get("current_prd_id")
        result = await review_prd(db, prd_id, run.id) if prd_id else {"quality_score": 0, "need_human_review": True, "problems": ["没有可评审 PRD"]}
        return {**state, "reviewer_result": result, "needs_human_review": result.get("need_human_review", True)}

    async def final_compression(state: AgentState) -> AgentState:
        step_summaries = [s.step_summary or "" for s in db.query(AgentStep).filter_by(run_id=run.id).order_by(AgentStep.id).all()]
        conversation_summary = compress_steps(db, run.id, step_summaries)
        final_output = build_chat_final_output(db, state, project_id, conversation_id)
        return {**state, "conversation_summary": conversation_summary, "final_output": final_output}

    graph = StateGraph(AgentState)
    for name, node in [
        ("orchestrator", orchestrator),
        ("file_intake", file_intake),
        ("data_intake", data_intake),
        ("feedback_analyst", feedback_analyst),
        ("retrieval", retrieval),
        ("cluster", cluster),
        ("metric", metric),
        ("opportunity", opportunity),
        ("compression", compression),
        ("prd_writer", prd_writer),
        ("reviewer", reviewer),
        ("final_compression", final_compression),
    ]:
        graph.add_node(name, node)
    graph.add_edge(START, "orchestrator")
    graph.add_edge("orchestrator", "file_intake")
    graph.add_edge("file_intake", "data_intake")
    graph.add_edge("data_intake", "feedback_analyst")
    graph.add_edge("feedback_analyst", "retrieval")
    graph.add_edge("retrieval", "cluster")
    graph.add_edge("cluster", "metric")
    graph.add_edge("metric", "opportunity")
    graph.add_edge("opportunity", "compression")
    graph.add_edge("compression", "prd_writer")
    graph.add_edge("prd_writer", "reviewer")
    graph.add_edge("reviewer", "final_compression")
    graph.add_edge("final_compression", END)

    initial: AgentState = {
        "task": task,
        "project_id": project_id,
        "conversation_id": conversation_id or "",
        "user_id": user_id,
        "run_id": run.id,
        "messages": [{"role": "user", "content": task}],
        "agent_steps": [],
        "step_summaries": [],
    }
    app = graph.compile()
    try:
        state = await app.ainvoke(initial)
        db.add(ProjectMemory(project_id=project_id, conversation_id=conversation_id, memory_type="pending_agent_finding", content_json=json.dumps({"summary": state["final_output"], "run_id": run.id}, ensure_ascii=False), source="agent_run", confirmed_by_user=False))
        if conversation_id:
            db.add(ConversationMessage(conversation_id=conversation_id, role="assistant", content=state["final_output"]))
        run.status = "success"
        run.final_output = state["final_output"]
        run.finished_at = datetime.utcnow()
        db.commit()
        return state
    except Exception as exc:
        run.status = "failed"
        run.final_output = str(exc)
        run.finished_at = datetime.utcnow()
        db.commit()
        raise
