export function ReviewerPanel({ data }: { data?: any }) {
  if (!data) return <div className="card p-4 text-sm text-muted">Reviewer 结果会在 PRD 生成后出现。</div>;
  return <div className="card p-4"><h2 className="font-semibold">Reviewer</h2><div className="mt-3 grid grid-cols-3 gap-2 text-sm"><span className="badge">quality {data.quality_score}</span><span className="badge">complete {data.prd_completeness_score}</span><span className="badge">risk {data.hallucination_risk}</span></div><ul className="mt-3 list-disc pl-5 text-sm text-muted">{data.suggestions?.map((x: string) => <li key={x}>{x}</li>)}</ul></div>;
}

