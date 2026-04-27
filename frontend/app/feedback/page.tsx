"use client";
import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { api } from "@/lib/api";

export default function FeedbackPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [module, setModule] = useState("");
  const [sentiment, setSentiment] = useState("");
  const load = () => api.feedback(`?${new URLSearchParams({ ...(module && { product_module: module }), ...(sentiment && { sentiment }) }).toString()}`).then(setRows);
  useEffect(() => { load(); }, []);
  return <div className="space-y-5">
    <div><h1 className="text-2xl font-semibold">Feedback Inbox</h1><p className="text-sm text-muted">展示入库反馈、摘要、标签、情绪和严重度。</p></div>
    <div className="card flex gap-3 p-4"><input className="input" placeholder="模块，如 支付" value={module} onChange={e => setModule(e.target.value)} /><select className="input" value={sentiment} onChange={e => setSentiment(e.target.value)}><option value="">全部情绪</option><option value="negative">negative</option><option value="neutral">neutral</option><option value="positive">positive</option></select><button className="btn btn-primary" onClick={load}><Search size={15} />筛选</button></div>
    <div className="grid gap-3">{rows.map(f => <article key={f.id} className="card p-4"><div className="flex justify-between gap-4"><p className="text-sm leading-6">{f.feedback_text}</p><button className="btn">相似反馈</button></div><div className="mt-3 text-sm text-muted">{f.feedback_summary}</div><div className="mt-3 flex gap-2"><span className="badge">{f.product_module || "其他"}</span><span className="badge">{f.sentiment_label}</span><span className="badge">{f.severity_label}</span><span className="badge">{f.issue_type}</span></div></article>)}</div>
  </div>;
}

