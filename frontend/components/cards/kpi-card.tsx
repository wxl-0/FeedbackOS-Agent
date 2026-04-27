import { ReactNode } from "react";

export function KpiCard({ title, value, hint, icon }: { title: string; value: ReactNode; hint?: string; icon?: ReactNode }) {
  return <div className="card p-4">
    <div className="flex items-center justify-between">
      <div className="text-sm text-muted">{title}</div>
      <div className="text-brand">{icon}</div>
    </div>
    <div className="mt-3 text-2xl font-semibold">{value}</div>
    {hint && <div className="mt-1 text-xs text-muted">{hint}</div>}
  </div>;
}

