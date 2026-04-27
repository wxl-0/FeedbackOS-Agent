"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { Bot, Loader2, Plus, Send, User } from "lucide-react";
import { api } from "@/lib/api";
import { AgentTimeline } from "@/components/agent/agent-timeline";
import { ReviewerPanel } from "@/components/agent/reviewer-panel";

const tabs = ["当前文件", "Agent 执行轨迹", "检索证据", "PRD 草稿", "Reviewer 评审", "Evaluation 指标"] as const;

export default function WorkspacePage() {
  const [conversation, setConversation] = useState<any>();
  const [conversations, setConversations] = useState<any[]>([]);
  const [workspace, setWorkspace] = useState<any>();
  const [task, setTask] = useState("");
  const [activeTab, setActiveTab] = useState<(typeof tabs)[number]>("当前文件");
  const [busy, setBusy] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function refreshHistory() {
    setConversations(await api.conversations());
  }

  async function load(id: string) {
    setWorkspace(await api.workspace(id));
    await refreshHistory();
  }

  useEffect(() => {
    const cached = window.localStorage.getItem("feedbackos.currentConversationId");
    async function boot() {
      await refreshHistory();
      if (cached) {
        try {
          const data = await api.conversation(cached);
          setConversation(data);
          await load(cached);
          return;
        } catch {}
      }
      const created = await api.createConversation("需求发现会话");
      window.localStorage.setItem("feedbackos.currentConversationId", created.id);
      setConversation(created);
      await load(created.id);
    }
    boot().catch(console.error);
  }, []);

  const messages = useMemo(() => workspace?.conversation?.messages || [], [workspace]);

  async function switchConversation(id: string) {
    const data = await api.conversation(id);
    window.localStorage.setItem("feedbackos.currentConversationId", id);
    setConversation(data);
    await load(id);
  }

  async function newConversation() {
    const created = await api.createConversation("需求发现会话");
    window.localStorage.setItem("feedbackos.currentConversationId", created.id);
    setConversation(created);
    setTask("");
    await load(created.id);
  }

  async function upload(file?: File) {
    if (!file || !conversation?.id) return;
    setBusy(true);
    try {
      const uploaded = await api.upload(file, conversation.id);
      const parsed = await api.parseFile(uploaded.id);
      await api.confirmSchema(uploaded.id, parsed.schema?.mapping || {});
      await api.ingestFile(uploaded.id);
      await load(conversation.id);
      setActiveTab("当前文件");
    } finally {
      setBusy(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function send() {
    if (!conversation?.id || !task.trim()) return;
    setBusy(true);
    try {
      await api.runAgent(task, conversation.id);
      setTask("");
      await load(conversation.id);
      setActiveTab("Agent 执行轨迹");
    } finally {
      setBusy(false);
    }
  }

  return <div className="grid h-[calc(100vh-6.5rem)] grid-cols-[260px_minmax(0,1fr)_430px] gap-4">
    <aside className="card min-h-0 overflow-hidden">
      <div className="flex items-center justify-between border-b border-line p-3">
        <div className="text-sm font-semibold">会话历史</div>
        <button className="btn h-8 w-8 px-0" onClick={newConversation} title="新会话"><Plus size={15} /></button>
      </div>
      <div className="h-[calc(100%-3.5rem)] space-y-2 overflow-y-auto p-3">
        {conversations.length === 0 && <p className="text-sm text-muted">暂无会话</p>}
        {conversations.map(row => <button key={row.id} onClick={() => switchConversation(row.id)} className={`w-full rounded-md border p-3 text-left text-sm hover:bg-slate-50 ${conversation?.id === row.id ? "border-brand bg-[#e9f3f2]" : "border-line bg-white"}`}>
          <div className="truncate font-medium">{row.title}</div>
          <div className="mt-1 truncate text-xs text-muted">{row.id}</div>
          <div className="mt-2 text-xs text-muted">{row.message_count} messages</div>
        </button>)}
      </div>
    </aside>

    <section className="card flex min-h-0 flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-line p-4">
        <div>
          <h1 className="text-xl font-semibold">Agent Workspace</h1>
          <p className="text-xs text-muted">conversation_id: {conversation?.id || "creating..."}</p>
        </div>
      </div>

      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-4">
        {messages.length === 0 && <div className="rounded-lg border border-dashed border-line bg-slate-50 p-8 text-center text-sm text-muted">上传文件开始分析</div>}
        {messages.map((m: any) => <div key={m.id} className={`flex gap-3 ${m.role === "user" ? "justify-end" : "justify-start"}`}>
          {m.role !== "user" && <div className="mt-1 flex h-8 w-8 items-center justify-center rounded-full bg-[#e9f3f2] text-brand"><Bot size={16} /></div>}
          <div className={`max-w-[72%] rounded-lg border border-line p-3 text-sm leading-6 ${m.role === "user" ? "bg-brand text-white" : "bg-white"}`}>{m.content}</div>
          {m.role === "user" && <div className="mt-1 flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 text-muted"><User size={16} /></div>}
        </div>)}
      </div>

      <div className="border-t border-line p-4">
        <input ref={fileRef} type="file" className="hidden" accept=".csv,.xlsx,.xls,.txt,.md,.docx" onChange={(e) => upload(e.target.files?.[0])} />
        <div className="flex gap-2">
          <input className="input flex-1" placeholder="输入你想让 Agent 分析的问题..." value={task} onChange={(e) => setTask(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") send(); }} />
          <button className="btn btn-primary w-10 px-0" disabled={busy || !task.trim()} onClick={send} title="发送">{busy ? <Loader2 className="animate-spin" size={16} /> : <Send size={16} />}</button>
          <button className="btn w-10 px-0" disabled={busy} onClick={() => fileRef.current?.click()} title="上传文件"><Plus size={16} /></button>
        </div>
      </div>
    </section>

    <aside className="card min-h-0 overflow-hidden">
      <div className="flex flex-wrap gap-2 border-b border-line p-3">
        {tabs.map(tab => <button key={tab} className={`rounded-md px-2.5 py-1.5 text-xs ${activeTab === tab ? "bg-brand text-white" : "bg-slate-50 text-muted hover:text-ink"}`} onClick={() => setActiveTab(tab)}>{tab}</button>)}
      </div>
      <div className="h-[calc(100%-4rem)] overflow-y-auto p-4">
        {activeTab === "当前文件" && <FilePanel files={workspace?.files || []} />}
        {activeTab === "Agent 执行轨迹" && <AgentTimeline steps={workspace?.steps || []} />}
        {activeTab === "检索证据" && <EvidencePanel items={workspace?.retrieved_feedback || []} />}
        {activeTab === "PRD 草稿" && <PrdPanel prds={workspace?.prds || []} />}
        {activeTab === "Reviewer 评审" && <ReviewerPanel data={workspace?.reviewer_result} />}
        {activeTab === "Evaluation 指标" && <EvaluationPanel data={workspace?.evaluation} />}
      </div>
    </aside>
  </div>;
}

function FilePanel({ files }: { files: any[] }) {
  if (!files.length) return <p className="text-sm text-muted">当前会话还没有文件。</p>;
  return <div className="space-y-3">{files.map(file => <div key={file.id} className="rounded-md border border-line p-3">
    <div className="font-medium">{file.file_name}</div>
    <div className="mt-1 text-xs text-muted">{file.detected_data_type} · rows {file.row_count} · chunks {file.chunk_count}</div>
    <div className="mt-2 flex flex-wrap gap-2 text-xs"><span className="badge">{file.parse_status}</span><span className="badge">{file.ingest_status}</span><span className="badge">{file.vector_status}</span></div>
  </div>)}</div>;
}

function EvidencePanel({ items }: { items: any[] }) {
  if (!items.length) return <p className="text-sm text-muted">运行 Agent 后展示当前会话召回证据。</p>;
  return <div className="space-y-3">{items.map(item => <blockquote key={item.id} className="rounded-md border border-line bg-slate-50 p-3 text-sm">
    #{item.id} {item.feedback_text}
    <div className="mt-2 flex gap-2"><span className="badge">{item.product_module}</span><span className="badge">{item.sentiment_label}</span></div>
  </blockquote>)}</div>;
}

function PrdPanel({ prds }: { prds: any[] }) {
  if (!prds.length) return <p className="text-sm text-muted">当前会话还没有 PRD 草稿。</p>;
  return <article className="prose prose-sm max-w-none whitespace-pre-wrap rounded-md border border-line bg-white p-3 text-sm leading-6">{prds[0].prd_markdown}</article>;
}

function EvaluationPanel({ data }: { data: any }) {
  if (!data) return <p className="text-sm text-muted">暂无指标。</p>;
  const rows = [
    ["Agent Run", data.overview?.agent_run_total],
    ["成功率", data.overview?.agent_run_success_rate],
    ["LLM 调用", data.llm?.llm_call_count],
    ["检索次数", data.retrieval?.retrieval_count],
    ["PRD 完整度", data.quality?.prd_completeness_avg],
    ["平均压缩率", data.compression?.avg_compression_rate],
  ];
  return <div className="grid grid-cols-2 gap-3">{rows.map(([k, v]) => <div key={String(k)} className="rounded-md border border-line p-3"><div className="text-xs text-muted">{k}</div><div className="mt-1 text-lg font-semibold">{String(v ?? 0)}</div></div>)}</div>;
}
