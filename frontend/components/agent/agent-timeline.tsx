export function AgentTimeline({ steps }: { steps: any[] }) {
  return <div className="space-y-3">{steps.map((s, i) => <div key={s.id || i} className="rounded-md border border-line bg-white p-3"><div className="flex items-center justify-between"><div className="font-medium">{i + 1}. {s.agent_name}</div><span className="badge">{s.status} · {s.latency_ms}ms</span></div><div className="text-xs text-muted">{s.step_name} · {s.tool_name}</div><p className="mt-2 text-sm">{s.step_summary}</p></div>)}</div>;
}

