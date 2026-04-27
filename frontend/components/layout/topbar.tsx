import { Activity, MessageSquareText, ShieldCheck } from "lucide-react";

export function Topbar() {
  return <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-line bg-canvas/90 px-6 backdrop-blur">
    <div>
      <div className="text-sm font-semibold">Agent Workspace</div>
      <div className="text-xs text-muted">每个会话独立绑定文件，Agent 只分析当前 conversation_id 下的数据</div>
    </div>
    <div className="flex items-center gap-2 text-xs text-muted">
      <span className="badge"><MessageSquareText size={13} /> Chat-first</span>
      <span className="badge"><Activity size={13} /> Scoped workflow</span>
      <span className="badge"><ShieldCheck size={13} /> Evidence gated</span>
    </div>
  </header>;
}
