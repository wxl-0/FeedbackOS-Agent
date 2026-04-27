"use client";
import { Check, X } from "lucide-react";
import { api } from "@/lib/api";

export function MemoryCard({ item, onDone }: { item: any; onDone: () => void }) {
  return <div className="rounded-md border border-line bg-white p-3"><div className="text-sm font-medium">{item.memory_type || item.decision_title || item.preference_key}</div><pre className="mt-2 max-h-28 overflow-auto whitespace-pre-wrap text-xs text-muted">{JSON.stringify(item.content || item.decision_content || item.preference_value, null, 2)}</pre><div className="mt-3 flex gap-2"><button className="btn" onClick={async () => { await api.confirmMemory(item.id, true); onDone(); }}><Check size={14} />确认</button><button className="btn" onClick={async () => { await api.confirmMemory(item.id, false); onDone(); }}><X size={14} />拒绝</button></div></div>;
}

