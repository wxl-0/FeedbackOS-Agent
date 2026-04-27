"use client";
import { useRef, useState } from "react";
import { UploadCloud } from "lucide-react";
import { api } from "@/lib/api";

export function FileUploadPanel({ onUploaded }: { onUploaded: () => void }) {
  const ref = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  async function upload(file?: File) {
    if (!file) return;
    setBusy(true);
    try { await api.upload(file); onUploaded(); } finally { setBusy(false); }
  }
  return <div className="card border-dashed p-6">
    <input ref={ref} type="file" className="hidden" accept=".csv,.xlsx,.xls,.txt,.md,.docx" onChange={(e) => upload(e.target.files?.[0])} />
    <button className="btn btn-primary" disabled={busy} onClick={() => ref.current?.click()}><UploadCloud size={16} />上传文件</button>
    <p className="mt-3 text-sm text-muted">支持 CSV、Excel、TXT、Markdown、DOCX。上传后需解析、确认字段映射、再入库向量化。</p>
  </div>;
}

