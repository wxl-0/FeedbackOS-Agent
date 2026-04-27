"use client";
import { useEffect, useState } from "react";
import { Network } from "lucide-react";
import { api } from "@/lib/api";
import { pct } from "@/lib/utils";

export default function ClustersPage() {
  const [rows, setRows] = useState<any[]>([]);
  const load = () => api.clusters().then(setRows);
  useEffect(() => { load(); }, []);
  async function generate() { await api.generateClusters(); await load(); }
  return <div className="space-y-5"><div className="flex items-center justify-between"><div><h1 className="text-2xl font-semibold">Insight Clusters</h1><p className="text-sm text-muted">基于标签、语义召回与规则生成痛点聚类。</p></div><button className="btn btn-primary" onClick={generate}><Network size={15} />生成 clusters</button></div><div className="grid grid-cols-2 gap-4">{rows.map(c => <section key={c.id} className="card p-4"><h2 className="font-semibold">{c.cluster_name}</h2><p className="mt-2 text-sm text-muted">{c.cluster_summary}</p><div className="mt-3 flex gap-2"><span className="badge">{c.feedback_count} 条反馈</span><span className="badge">负面率 {pct(c.negative_ratio)}</span><span className="badge">severity {c.severity_score}</span></div><div className="mt-4 space-y-2">{c.representative_quotes?.map((q: any) => <blockquote key={q.id} className="rounded-md bg-slate-50 p-3 text-sm">#{q.id} {q.text}</blockquote>)}</div></section>)}</div></div>;
}
