"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { MemoryCard } from "@/components/memory/memory-card";

export default function MemoryPage() {
  const [data, setData] = useState<any>();
  const load = () => api.memory().then(setData);
  useEffect(() => { load(); }, []);
  const project = data?.project_memory || [];
  return <div className="space-y-5"><div><h1 className="text-2xl font-semibold">Memory Center</h1><p className="text-sm text-muted">长期记忆在写入前需要人工确认；短期记忆保存在 Agent state 中。</p></div><div className="grid grid-cols-2 gap-4"><section className="card p-4"><h2 className="font-semibold">待确认记忆</h2><div className="mt-3 space-y-3">{project.filter((m: any) => !m.confirmed_by_user).map((m: any) => <MemoryCard key={m.id} item={m} onDone={load} />)}</div></section><section className="card p-4"><h2 className="font-semibold">已确认记忆</h2><div className="mt-3 space-y-3">{project.filter((m: any) => m.confirmed_by_user).map((m: any) => <MemoryCard key={m.id} item={m} onDone={load} />)}</div></section><section className="card p-4"><h2 className="font-semibold">决策记忆</h2><pre className="mt-3 whitespace-pre-wrap text-xs text-muted">{JSON.stringify(data?.decision_memory || [], null, 2)}</pre></section><section className="card p-4"><h2 className="font-semibold">用户偏好记忆</h2><pre className="mt-3 whitespace-pre-wrap text-xs text-muted">{JSON.stringify(data?.user_preference_memory || [], null, 2)}</pre></section></div></div>;
}
