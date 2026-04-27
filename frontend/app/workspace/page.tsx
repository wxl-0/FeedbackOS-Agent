"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { Bot, Download, FileText, Loader2, Plus, Save, Send, User } from "lucide-react";
import { api } from "@/lib/api";

const tabs = ["当前文件", "Feedback Inbox", "Insight Cluster", "PRD"] as const;

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
      setConversation(undefined);
      setWorkspace(undefined);
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
    window.localStorage.removeItem("feedbackos.currentConversationId");
    setConversation(undefined);
    setWorkspace(undefined);
    setTask("");
    await refreshHistory();
  }

  async function ensureCurrentConversation() {
    if (conversation?.id) return conversation;
    const created = await api.createConversation("需求发现会话");
    window.localStorage.setItem("feedbackos.currentConversationId", created.id);
    setConversation(created);
    return created;
  }

  async function upload(file?: File) {
    if (!file) return;
    setBusy(true);
    try {
      const current = await ensureCurrentConversation();
      const uploaded = await api.upload(file, current.id);
      const parsed = await api.parseFile(uploaded.id);
      await api.confirmSchema(uploaded.id, parsed.schema?.mapping || {});
      await api.ingestFile(uploaded.id);
      await load(current.id);
      setActiveTab("当前文件");
    } finally {
      setBusy(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function send() {
    if (!task.trim()) return;
    setBusy(true);
    try {
      const current = await ensureCurrentConversation();
      await api.runAgent(task, current.id);
      setTask("");
      await load(current.id);
      setActiveTab("PRD");
    } finally {
      setBusy(false);
    }
  }

  return <div className="grid h-[calc(100vh-6.5rem)] grid-cols-[260px_minmax(0,1fr)_460px] gap-4">
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
          <div className="mt-2 text-xs text-muted">{row.message_count} messages · {row.file_count || 0} files</div>
        </button>)}
      </div>
    </aside>

    <section className="card flex min-h-0 flex-col overflow-hidden">
      <div className="border-b border-line p-4">
        <h1 className="text-xl font-semibold">Agent Workspace</h1>
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
        {activeTab === "Feedback Inbox" && <FeedbackPanel items={workspace?.feedback || []} />}
        {activeTab === "Insight Cluster" && <ClusterPanel clusters={workspace?.clusters || []} />}
        {activeTab === "PRD" && <PrdPanel prds={workspace?.prds || []} reviewer={workspace?.reviewer_result} onSaved={() => conversation?.id && load(conversation.id)} />}
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

function FeedbackPanel({ items }: { items: any[] }) {
  if (!items.length) return <p className="text-sm text-muted">当前会话还没有反馈数据。</p>;
  return <div className="space-y-3">{items.map(item => <article key={item.id} className="rounded-md border border-line p-3">
    <p className="text-sm leading-6">{item.feedback_text}</p>
    <p className="mt-2 text-xs text-muted">{item.feedback_summary}</p>
    <div className="mt-2 flex flex-wrap gap-2"><span className="badge">{item.product_module}</span><span className="badge">{item.sentiment_label}</span><span className="badge">{item.severity_label}</span><span className="badge">{item.issue_type}</span></div>
  </article>)}</div>;
}

function ClusterPanel({ clusters }: { clusters: any[] }) {
  if (!clusters.length) return <p className="text-sm text-muted">运行 Agent 后展示痛点聚类。</p>;
  return <div className="space-y-3">{clusters.map(cluster => <section key={cluster.id} className="rounded-md border border-line p-3">
    <div className="font-medium">{cluster.cluster_name}</div>
    <p className="mt-2 text-sm text-muted">{cluster.cluster_summary}</p>
    <div className="mt-2 flex flex-wrap gap-2"><span className="badge">{cluster.feedback_count} 条</span><span className="badge">负面率 {Math.round((cluster.negative_ratio || 0) * 100)}%</span><span className="badge">severity {cluster.severity_score}</span></div>
  </section>)}</div>;
}

function PrdPanel({ prds, reviewer, onSaved }: { prds: any[]; reviewer?: any; onSaved: () => void }) {
  const latest = prds[0];
  const [text, setText] = useState("");
  useEffect(() => { setText(latest?.prd_markdown || ""); }, [latest?.id, latest?.prd_markdown]);

  if (!latest) return <p className="text-sm text-muted">当前会话还没有 PRD 草稿。</p>;

  function exportMarkdown() {
    const blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${latest.title || "prd"}.md`;
    a.click();
    window.URL.revokeObjectURL(url);
  }

  async function save() {
    await api.updatePrd(latest.id, text);
    onSaved();
  }

  return <div className="space-y-3">
    <div className="flex flex-wrap gap-2">
      <button className="btn" onClick={save}><Save size={14} />保存</button>
      <button className="btn" onClick={exportMarkdown}><Download size={14} />Markdown</button>
      <button className="btn" onClick={() => api.exportPrdDocx(latest.title, text)}><FileText size={14} />DOCX</button>
    </div>
    {reviewer && <div className="rounded-md border border-line bg-slate-50 p-3 text-sm">
      <div className="font-medium">Reviewer 评分：{reviewer.quality_score ?? 0}</div>
      <div className="mt-1 text-xs text-muted">完整度 {reviewer.prd_completeness_score ?? 0} · 风险 {reviewer.hallucination_risk || "unknown"}</div>
    </div>}
    <textarea className="min-h-[560px] w-full resize-y rounded-md border border-line bg-white p-3 font-mono text-sm leading-6 outline-none focus:border-brand" value={text} onChange={(e) => setText(e.target.value)} />
  </div>;
}
