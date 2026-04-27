import { Activity, Database, ShieldCheck } from "lucide-react";

export function Topbar() {
  return <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-line bg-canvas/90 px-6 backdrop-blur">
    <div>
      <div className="text-sm font-semibold">AI Product Discovery Workspace</div>
      <div className="text-xs text-muted">数据来自上传文件或人工确认，不内置业务样例数据</div>
    </div>
    <div className="flex items-center gap-2 text-xs text-muted">
      <span className="badge"><Database size={13} /> SQLite</span>
      <span className="badge"><Activity size={13} /> Vector fallback ready</span>
      <span className="badge"><ShieldCheck size={13} /> Backend env keys only</span>
    </div>
  </header>;
}

