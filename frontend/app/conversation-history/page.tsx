"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { MessageSquareText } from "lucide-react";
import { api } from "@/lib/api";

export default function ConversationHistoryPage() {
  const [rows, setRows] = useState<any[]>([]);
  useEffect(() => { api.conversations().then(setRows).catch(console.error); }, []);
  function open(id: string) {
    window.localStorage.setItem("feedbackos.currentConversationId", id);
  }
  return <div className="space-y-5">
    <div><h1 className="text-2xl font-semibold">Conversation History</h1><p className="text-sm text-muted">每个会话拥有独立 conversation_id 和独立文件分析范围。</p></div>
    <div className="grid gap-3">{rows.map(row => <Link key={row.id} href="/workspace" onClick={() => open(row.id)} className="card block p-4 hover:bg-slate-50">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3"><MessageSquareText size={18} className="text-brand" /><div><div className="font-medium">{row.title}</div><div className="text-xs text-muted">{row.id}</div></div></div>
        <span className="badge">{row.message_count} messages</span>
      </div>
      <div className="mt-2 text-xs text-muted">updated {row.updated_at}</div>
    </Link>)}</div>
  </div>;
}
