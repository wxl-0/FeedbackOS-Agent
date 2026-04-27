"use client";
import { useEffect, useState } from "react";
import { FileText, Lightbulb } from "lucide-react";
import { api } from "@/lib/api";
import { PriorityChart } from "@/components/charts/priority-chart";

export default function OpportunitiesPage() {
  const [rows, setRows] = useState<any[]>([]);
  const load = () => api.opportunities().then(setRows);
  useEffect(() => { load(); }, []);
  async function generate() { await api.generateOpportunities(); await load(); }
  async function prd(id: number) { await api.generatePrd(id); alert("PRD 已生成，可到 PRD Studio 查看"); }
  return <div className="space-y-5"><div className="flex items-center justify-between"><div><h1 className="text-2xl font-semibold">Opportunity Board</h1><p className="text-sm text-muted">使用优先级公式将痛点聚类转换为 P0/P1/P2 机会点。</p></div><button className="btn btn-primary" onClick={generate}><Lightbulb size={15} />生成 opportunities</button></div><section className="card p-4"><PriorityChart data={["P0","P1","P2"].map(p => ({ name: p, value: rows.filter(r => r.priority_level === p).length }))} /></section><div className="grid gap-3">{rows.map(o => <article key={o.id} className="card p-4"><div className="flex justify-between gap-4"><div><h2 className="font-semibold">{o.title}</h2><p className="mt-1 text-sm text-muted">{o.problem_statement}</p></div><button className="btn" onClick={() => prd(o.id)}><FileText size={15} />生成 PRD</button></div><div className="mt-3 flex gap-2"><span className="badge">{o.priority_level}</span><span className="badge">score {o.priority_score}</span><span className="badge">impact {o.impact_score}</span><span className="badge">evidence {o.evidence_ids?.length || 0}</span></div></article>)}</div></div>;
}
