"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Bot, ChevronLeft, ChevronRight, Download, FileText, Loader2, Plus, Save, Send, User } from "lucide-react";
import { EvaluationChart } from "@/components/charts/evaluation-chart";
import { api } from "@/lib/api";

const tabs = ["当前文件", "Feedback Inbox", "Insight Cluster", "PRD", "Reviewer", "Evaluation"] as const;
type Tab = (typeof tabs)[number];

function pct(value: number | undefined) {
  return `${Math.round((value || 0) * 100)}%`;
}

function formatTime(value?: string) {
  if (!value) return "";
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export default function WorkspacePage() {
  const [conversation, setConversation] = useState<any>();
  const [conversations, setConversations] = useState<any[]>([]);
  const [workspace, setWorkspace] = useState<any>();
  const [task, setTask] = useState("");
  const [activeTab, setActiveTab] = useState<Tab>("当前文件");
  const [busy, setBusy] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(true);
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
  const gridCols = historyOpen ? "grid-cols-[250px_380px_minmax(620px,1fr)]" : "grid-cols-[44px_380px_minmax(620px,1fr)]";

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
    const created = await api.createConversation(`需求发现 ${formatTime(new Date().toISOString())}`);
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

  return (
    <div className={`grid h-[calc(100vh-5.5rem)] gap-4 ${gridCols}`}>
      <aside className="card min-h-0 overflow-hidden">
        <div className="flex items-center justify-between border-b border-line p-2">
          {historyOpen && <div className="text-sm font-semibold">会话历史</div>}
          <button className="btn h-8 w-8 px-0" onClick={() => setHistoryOpen(!historyOpen)} title={historyOpen ? "隐藏历史" : "展开历史"}>
            {historyOpen ? <ChevronLeft size={15} /> : <ChevronRight size={15} />}
          </button>
        </div>
        {historyOpen && (
          <div className="h-[calc(100%-3.25rem)] space-y-2 overflow-y-auto p-3">
            <button className="btn btn-primary w-full" onClick={newConversation}>
              <Plus size={15} /> 新会话
            </button>
            {conversations.length === 0 && <p className="text-sm text-muted">暂无会话</p>}
            {conversations.map((row) => (
              <button
                key={row.id}
                onClick={() => switchConversation(row.id)}
                className={`w-full rounded-md border p-3 text-left text-sm hover:bg-slate-50 ${conversation?.id === row.id ? "border-brand bg-[#e9f3f2]" : "border-line bg-white"}`}
              >
                <div className="truncate font-medium">{row.title}</div>
                <div className="mt-2 text-xs text-muted">最后更新 {formatTime(row.updated_at)}</div>
              </button>
            ))}
          </div>
        )}
      </aside>

      <section className="card flex min-h-0 flex-col overflow-hidden">
        <div className="border-b border-line p-4">
          <h1 className="text-lg font-semibold">FeedBackOS</h1>
        </div>

        <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-4">
          {messages.length === 0 && <div className="rounded-lg border border-dashed border-line bg-slate-50 p-8 text-center text-sm text-muted">上传文件开始分析</div>}
          {messages.map((m: any) => (
            <div key={m.id} className={`flex gap-3 ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              {m.role !== "user" && <div className="mt-1 flex h-8 w-8 items-center justify-center rounded-full bg-[#e9f3f2] text-brand"><Bot size={16} /></div>}
              <div className={`max-w-[82%] whitespace-pre-wrap rounded-lg border border-line p-3 text-sm leading-6 ${m.role === "user" ? "bg-brand text-white" : "bg-white"}`}>{m.content}</div>
              {m.role === "user" && <div className="mt-1 flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 text-muted"><User size={16} /></div>}
            </div>
          ))}
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
          {tabs.map((tab) => (
            <button key={tab} className={`rounded-md px-2.5 py-1.5 text-xs ${activeTab === tab ? "bg-brand text-white" : "bg-slate-50 text-muted hover:text-ink"}`} onClick={() => setActiveTab(tab)}>
              {tab}
            </button>
          ))}
        </div>
        <div className="h-[calc(100%-4rem)] overflow-y-auto p-4">
          {activeTab === "当前文件" && <FilePanel files={workspace?.files || []} />}
          {activeTab === "Feedback Inbox" && <FeedbackPanel items={workspace?.feedback || []} />}
          {activeTab === "Insight Cluster" && <ClusterPanel clusters={workspace?.clusters || []} />}
          {activeTab === "PRD" && <PrdPanel prds={workspace?.prds || []} reviewer={workspace?.reviewer_result} onSaved={() => conversation?.id && load(conversation.id)} />}
          {activeTab === "Reviewer" && <ReviewerPanel reviewer={workspace?.reviewer_result} />}
          {activeTab === "Evaluation" && <EvaluationPanel data={workspace?.evaluation} />}
        </div>
      </aside>
    </div>
  );
}

function FilePanel({ files }: { files: any[] }) {
  if (!files.length) return <p className="text-sm text-muted">当前会话还没有文件。</p>;
  return <div className="grid grid-cols-2 gap-3">{files.map((file) => (
    <div key={file.id} className="rounded-md border border-line p-3">
      <div className="truncate font-medium">{file.file_name}</div>
      <div className="mt-1 text-xs text-muted">{file.detected_data_type} · rows {file.row_count} · chunks {file.chunk_count}</div>
      <div className="mt-2 flex flex-wrap gap-2 text-xs">
        <span className="badge">{file.parse_status}</span>
        <span className="badge">{file.ingest_status}</span>
        <span className="badge">{file.vector_status}</span>
      </div>
    </div>
  ))}</div>;
}

function FeedbackPanel({ items }: { items: any[] }) {
  const [sentiment, setSentiment] = useState("all");
  if (!items.length) return <p className="text-sm text-muted">当前会话还没有反馈数据。</p>;
  const filtered = sentiment === "all" ? items : items.filter((item) => item.sentiment_label === sentiment);
  return <div className="space-y-3">
    <div className="flex items-center justify-between gap-3 rounded-md border border-line bg-slate-50 p-3">
      <div>
        <div className="text-sm font-medium">情绪筛选</div>
        <div className="text-xs text-muted">当前显示 {filtered.length} / {items.length} 条反馈</div>
      </div>
      <select className="input h-9 w-36 bg-white" value={sentiment} onChange={(e) => setSentiment(e.target.value)}>
        <option value="all">全部情绪</option>
        <option value="positive">正向</option>
        <option value="neutral">中性</option>
        <option value="negative">负向</option>
      </select>
    </div>
    {filtered.length === 0 && <p className="rounded-md border border-dashed border-line p-6 text-center text-sm text-muted">没有匹配当前情绪条件的反馈。</p>}
    <div className="grid grid-cols-2 gap-3">{filtered.map((item) => (
      <article key={item.id} className="rounded-md border border-line p-3">
        <p className="line-clamp-2 text-sm leading-6">{item.feedback_summary || item.feedback_text}</p>
        <div className="mt-2 flex flex-wrap gap-2">
          <span className="badge">{item.product_module}</span>
          <span className="badge">{item.sentiment_label}</span>
          <span className="badge">{item.severity_label}</span>
          <span className="badge">{item.issue_type}</span>
        </div>
      </article>
    ))}</div>
  </div>;
}

function ClusterPanel({ clusters }: { clusters: any[] }) {
  if (!clusters.length) return <p className="text-sm text-muted">运行 Agent 后展示痛点聚类。</p>;
  return <div className="grid grid-cols-2 gap-3">{clusters.map((cluster) => (
    <section key={cluster.id} className="rounded-md border border-line p-3">
      <div className="font-medium">{cluster.cluster_name}</div>
      <p className="mt-2 text-sm text-muted">{cluster.cluster_summary}</p>
      <div className="mt-2 flex flex-wrap gap-2">
        <span className="badge">{cluster.feedback_count} 条</span>
        <span className="badge">负面率 {Math.round((cluster.negative_ratio || 0) * 100)}%</span>
        <span className="badge">severity {cluster.severity_score}</span>
      </div>
    </section>
  ))}</div>;
}

function PrdPanel({ prds, reviewer, onSaved }: { prds: any[]; reviewer?: any; onSaved: () => void }) {
  const [selectedId, setSelectedId] = useState<number | undefined>();
  const selected = prds.find((prd) => prd.id === selectedId) || prds[0];
  const [text, setText] = useState("");
  useEffect(() => {
    if (prds[0]?.id && !selectedId) setSelectedId(prds[0].id);
  }, [prds, selectedId]);
  useEffect(() => { setText(selected?.prd_markdown || ""); }, [selected?.id, selected?.prd_markdown]);

  if (!selected) return <p className="text-sm text-muted">当前会话还没有 PRD 草稿。你可以在聊天里说“写一份针对支付体验痛点的 PRD”。</p>;

  function exportMarkdown() {
    const blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${selected.title || "prd"}.md`;
    a.click();
    window.URL.revokeObjectURL(url);
  }

  async function save() {
    await api.updatePrd(selected.id, text);
    onSaved();
  }

  return <div className="grid min-h-[650px] grid-cols-[190px_minmax(0,1fr)] gap-3">
    <aside className="rounded-md border border-line bg-slate-50 p-3">
      <div className="mb-3 text-sm font-semibold">历史 PRD</div>
      <div className="space-y-2">
        {prds.map((prd) => (
          <button
            key={prd.id}
            className={`w-full rounded-md border p-3 text-left text-sm hover:bg-white ${selected.id === prd.id ? "border-brand bg-white text-brand" : "border-line bg-white/70 text-ink"}`}
            onClick={() => setSelectedId(prd.id)}
          >
            <div className="line-clamp-2 font-medium">{prd.title}</div>
            <div className="mt-1 text-xs text-muted">#{prd.id} · {prd.version} · {prd.status}</div>
          </button>
        ))}
      </div>
    </aside>
    <section className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="font-semibold">{selected.title}</div>
          <div className="text-xs text-muted">#{selected.id} · {selected.version} · {selected.status}</div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button className="btn" onClick={save}><Save size={14} />保存</button>
          <button className="btn" onClick={exportMarkdown}><Download size={14} />Markdown</button>
          <button className="btn" onClick={() => api.exportPrdDocx(selected.title, text)}><FileText size={14} />DOCX</button>
        </div>
      </div>
      {reviewer && selected.id === prds[0]?.id && <div className="rounded-md border border-line bg-slate-50 p-3 text-sm">
        <div className="font-medium">最新 Reviewer 评分：{reviewer.quality_score ?? 0}</div>
      </div>}
      <textarea className="min-h-[620px] w-full resize-y rounded-md border border-line bg-white p-3 font-mono text-sm leading-6 outline-none focus:border-brand" value={text} onChange={(e) => setText(e.target.value)} />
    </section>
  </div>;
}

function ReviewerPanel({ reviewer }: { reviewer?: any }) {
  if (!reviewer) return <p className="text-sm text-muted">当前会话还没有 Reviewer 评审结果。生成 PRD 后会在这里展示质量评分、问题和建议。</p>;
  const scoreCards = [
    ["综合评分", reviewer.quality_score ?? 0],
    ["证据覆盖", reviewer.evidence_coverage_score ?? 0],
  ];
  return <div className="space-y-4">
    <div className="grid grid-cols-2 gap-3">
      {scoreCards.map(([label, value]) => (
        <div key={String(label)} className="rounded-md border border-line bg-white p-3">
          <div className="text-xs text-muted">{label}</div>
          <div className="mt-1 text-xl font-semibold">{value}</div>
        </div>
      ))}
    </div>
    <section className="rounded-md border border-line bg-white p-4">
      <h3 className="text-sm font-semibold">发现的问题</h3>
      {(reviewer.problems || []).length ? (
        <ul className="mt-3 space-y-2 text-sm text-muted">
          {reviewer.problems.map((item: string, index: number) => <li key={index}>• {item}</li>)}
        </ul>
      ) : <p className="mt-3 text-sm text-muted">暂无明显问题。</p>}
    </section>
    <section className="rounded-md border border-line bg-white p-4">
      <h3 className="text-sm font-semibold">优化建议</h3>
      {(reviewer.suggestions || []).length ? (
        <ul className="mt-3 space-y-2 text-sm text-muted">
          {reviewer.suggestions.map((item: string, index: number) => <li key={index}>• {item}</li>)}
        </ul>
      ) : <p className="mt-3 text-sm text-muted">暂无建议。</p>}
    </section>
  </div>;
}

function EvaluationPanel({ data }: { data?: any }) {
  if (!data) return <p className="text-sm text-muted">当前会话暂无 Evaluation 指标。</p>;
  const cards = [
    ["Agent Run 总次数", data.overview?.agent_run_total],
    ["Agent Run 成功率", pct(data.overview?.agent_run_success_rate)],
    ["平均 Step 数", data.overview?.avg_agent_steps],
    ["LLM 调用次数", data.llm?.llm_call_count],
    ["输入 Token", data.llm?.input_tokens],
    ["输出 Token", data.llm?.output_tokens],
    ["证据覆盖率", pct(data.retrieval?.opportunity_evidence_coverage)],
    ["Reviewer 平均分", data.quality?.reviewer_avg_score],
    ["平均压缩率", pct(data.compression?.avg_compression_rate)],
  ];

  return <div className="space-y-4">
    <div className="grid grid-cols-3 gap-3">
      {cards.map(([label, value]) => (
        <div key={String(label)} className="rounded-md border border-line bg-white p-3">
          <div className="text-xs text-muted">{label}</div>
          <div className="mt-1 text-lg font-semibold">{value ?? 0}</div>
        </div>
      ))}
    </div>
    <div className="grid grid-cols-2 gap-3">
      <section className="rounded-md border border-line bg-white p-3">
        <h3 className="text-sm font-semibold">生成质量</h3>
        <EvaluationChart data={[{ name: "PRD", value: data.quality?.prd_completeness_avg || 0 }, { name: "Reviewer", value: data.quality?.reviewer_avg_score || 0 }]} />
      </section>
      <section className="rounded-md border border-line bg-white p-3">
        <h3 className="text-sm font-semibold">LLM 调用</h3>
        <pre className="mt-3 max-h-56 overflow-auto rounded-md bg-slate-50 p-3 text-xs">{JSON.stringify(data.llm, null, 2)}</pre>
      </section>
      <section className="rounded-md border border-line bg-white p-3">
        <h3 className="text-sm font-semibold">检索与证据</h3>
        <pre className="mt-3 max-h-56 overflow-auto rounded-md bg-slate-50 p-3 text-xs">{JSON.stringify(data.retrieval, null, 2)}</pre>
      </section>
      <section className="rounded-md border border-line bg-white p-3">
        <h3 className="text-sm font-semibold">上下文压缩</h3>
        <pre className="mt-3 max-h-56 overflow-auto rounded-md bg-slate-50 p-3 text-xs">{JSON.stringify(data.compression, null, 2)}</pre>
      </section>
    </div>
  </div>;
}
