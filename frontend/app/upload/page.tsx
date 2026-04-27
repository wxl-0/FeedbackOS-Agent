"use client";
import { useEffect, useState } from "react";
import { Check, Database, ScanLine } from "lucide-react";
import { api } from "@/lib/api";
import { FileUploadPanel } from "@/components/upload/file-upload-panel";
import { IngestionStatus } from "@/components/upload/ingestion-status";
import { SchemaPreview } from "@/components/upload/schema-preview";

export default function UploadPage() {
  const [files, setFiles] = useState<any[]>([]);
  const load = () => api.files().then(setFiles).catch(console.error);
  useEffect(() => { load(); }, []);
  async function act(fn: Promise<any>) { await fn; await load(); }
  return <div className="space-y-6">
    <div><h1 className="text-2xl font-semibold">Upload Center</h1><p className="text-sm text-muted">数据入口：先解析、清洗、入库、向量化，Agent 不读取完整原始文件。</p></div>
    <FileUploadPanel onUploaded={load} />
    <div className="grid gap-4">
      {files.map(file => <section key={file.id} className="card p-4">
        <div className="flex items-start justify-between gap-4">
          <div><h2 className="font-semibold">{file.file_name}</h2><p className="text-sm text-muted">{file.file_type} · {file.file_size} bytes · {file.detected_data_type}</p></div>
          <div className="flex gap-2">
            <button className="btn" onClick={() => act(api.parseFile(file.id))}><ScanLine size={15} />开始解析</button>
            <button className="btn" onClick={() => act(api.confirmSchema(file.id, file.schema?.mapping || {}))}><Check size={15} />确认映射</button>
            <button className="btn btn-primary" onClick={() => act(api.ingestFile(file.id))}><Database size={15} />确认入库</button>
          </div>
        </div>
        <div className="mt-4"><IngestionStatus file={file} /></div>
        <div className="mt-4 grid grid-cols-2 gap-4"><SchemaPreview file={file} /><pre className="max-h-48 overflow-auto rounded-md border border-line bg-slate-50 p-3 text-xs">{JSON.stringify(file.preview?.slice(0, 5), null, 2)}</pre></div>
        {file.error_message && <div className="mt-3 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{file.error_message}</div>}
      </section>)}
    </div>
  </div>;
}
