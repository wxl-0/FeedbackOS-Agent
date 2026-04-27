"use client";
import { useEffect, useState } from "react";
import { FileText, Inbox, Lightbulb, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";
import { KpiCard } from "@/components/cards/kpi-card";
import { SentimentChart } from "@/components/charts/sentiment-chart";
import { PriorityChart } from "@/components/charts/priority-chart";
import { pct } from "@/lib/utils";

export default function DashboardPage() {
  const [data, setData] = useState<any>();
  useEffect(() => { api.dashboard().then(setData).catch(console.error); }, []);
  if (!data) return <div>Loading workspace...</div>;
  return <div className="space-y-6">
    <div><h1 className="text-2xl font-semibold">Dashboard</h1><p className="text-sm text-muted">从已上传并入库的数据中汇总反馈、机会点和生成质量。</p></div>
    <div className="grid grid-cols-4 gap-4">
      <KpiCard title="总反馈数" value={data.total_feedback} icon={<Inbox size={18} />} />
      <KpiCard title="负面反馈率" value={pct(data.negative_rate)} hint="基于 feedback_items" icon={<ShieldCheck size={18} />} />
      <KpiCard title="高优先级机会点" value={data.high_priority_opportunities} icon={<Lightbulb size={18} />} />
      <KpiCard title="PRD 草稿数" value={data.prd_drafts} icon={<FileText size={18} />} />
    </div>
    <div className="grid grid-cols-3 gap-4">
      <section className="card p-4"><h2 className="font-semibold">情绪分布</h2><SentimentChart data={data.sentiment_distribution || []} /></section>
      <section className="card p-4"><h2 className="font-semibold">优先级分布</h2><PriorityChart data={data.priority_distribution || []} /></section>
      <section className="card p-4"><h2 className="font-semibold">Top 痛点</h2><div className="mt-4 space-y-3">{(data.top_clusters || []).map((c: any) => <div key={c.id} className="rounded-md border border-line p-3"><div className="font-medium">{c.name}</div><div className="text-xs text-muted">{c.count} 条反馈，负面率 {pct(c.negative_ratio)}</div></div>)}</div></section>
    </div>
    <section className="card p-4"><h2 className="font-semibold">当前上传文件处理状态</h2><div className="mt-3 divide-y divide-line">{(data.recent_files || []).map((f: any) => <div key={f.id} className="grid grid-cols-5 py-3 text-sm"><span>{f.file_name}</span><span>{f.detected_data_type}</span><span>{f.parse_status}</span><span>{f.ingest_status}</span><span>{f.vector_status}</span></div>)}</div></section>
  </div>;
}

