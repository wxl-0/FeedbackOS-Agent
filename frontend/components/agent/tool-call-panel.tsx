export function ToolCallPanel({ step }: { step?: any }) {
  return <aside className="card p-4"><h2 className="font-semibold">Tool Call Panel</h2>{step ? <pre className="mt-3 max-h-[520px] overflow-auto rounded-md bg-slate-50 p-3 text-xs">{JSON.stringify(step.output, null, 2)}</pre> : <p className="mt-3 text-sm text-muted">运行 Agent 后选择最近一步查看工具输出。</p>}</aside>;
}

