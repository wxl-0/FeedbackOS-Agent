"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { KpiCard } from "@/components/cards/kpi-card";
import { EvaluationChart } from "@/components/charts/evaluation-chart";
import { pct } from "@/lib/utils";

export default function EvaluationPage() {
  const [data, setData] = useState<any>();
  const [error, setError] = useState<string>("");

  useEffect(() => {
    api.evaluation().then(setData).catch((err) => setError(err.message || "Evaluation 加载失败"));
  }, []);

  if (error) return <div className="card p-4 text-sm text-red-700">{error}</div>;
  if (!data) return <div>Loading evaluation...</div>;

  const cards = [
    ["Agent Run 总次数", data.overview.agent_run_total],
    ["Agent Run 成功率", pct(data.overview.agent_run_success_rate)],
    ["平均 Agent Step 数", data.overview.avg_agent_steps],
    ["LLM 调用次数", data.llm.llm_call_count],
    ["输入 token 总量", data.llm.input_tokens],
    ["输出 token 总量", data.llm.output_tokens],
    ["检索次数", data.retrieval.retrieval_count],
    ["机会点证据覆盖率", pct(data.retrieval.opportunity_evidence_coverage)],
    ["PRD 完整度平均分", data.quality.prd_completeness_avg],
    ["Reviewer 平均分", data.quality.reviewer_avg_score],
    ["需要人工确认比例", pct(data.quality.human_review_rate)],
    ["平均上下文压缩率", pct(data.compression.avg_compression_rate)]
  ];

  return <div className="space-y-5">
    <div>
      <h1 className="text-2xl font-semibold">Evaluation</h1>
      <p className="text-sm text-muted">运行、LLM、检索、生成质量与上下文压缩指标。</p>
    </div>
    <div className="grid grid-cols-4 gap-4">{cards.map(([k, v]) => <KpiCard key={String(k)} title={String(k)} value={String(v)} />)}</div>
    <div className="grid grid-cols-2 gap-4">
      <section className="card p-4"><h2 className="font-semibold">LLM 调用与成本</h2><pre className="mt-3 rounded-md bg-slate-50 p-3 text-xs">{JSON.stringify(data.llm, null, 2)}</pre></section>
      <section className="card p-4"><h2 className="font-semibold">检索与证据</h2><pre className="mt-3 rounded-md bg-slate-50 p-3 text-xs">{JSON.stringify(data.retrieval, null, 2)}</pre></section>
      <section className="card p-4"><h2 className="font-semibold">生成质量</h2><EvaluationChart data={[{ name: "PRD", value: data.quality.prd_completeness_avg }, { name: "Reviewer", value: data.quality.reviewer_avg_score }]} /></section>
      <section className="card p-4"><h2 className="font-semibold">上下文压缩</h2><pre className="mt-3 rounded-md bg-slate-50 p-3 text-xs">{JSON.stringify(data.compression, null, 2)}</pre></section>
    </div>
  </div>;
}
