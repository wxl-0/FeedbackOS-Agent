"use client";
import { useEffect, useState } from "react";
import { Download, RefreshCw, Save, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";
import { PrdEditor } from "@/components/prd/prd-editor";
import { ReviewerPanel } from "@/components/agent/reviewer-panel";

export default function PrdStudioPage() {
  const [prds, setPrds] = useState<any[]>([]);
  const [current, setCurrent] = useState<any>();
  const [text, setText] = useState("");
  const [review, setReview] = useState<any>();
  useEffect(() => { api.prds().then(rows => { setPrds(rows); setCurrent(rows[0]); setText(rows[0]?.prd_markdown || ""); }); }, []);
  async function doReview() { if (current) setReview(await api.reviewPrd(current.id)); }
  return <div className="space-y-5"><div><h1 className="text-2xl font-semibold">PRD Studio</h1><p className="text-sm text-muted">编辑生成的 PRD，右侧查看 Reviewer 建议。</p></div><div className="grid grid-cols-[280px_1fr_340px] gap-4"><aside className="card p-4"><h2 className="font-semibold">Opportunity 摘要</h2><div className="mt-3 space-y-2">{prds.map(p => <button key={p.id} className="w-full rounded-md border border-line p-3 text-left text-sm hover:bg-slate-50" onClick={() => { setCurrent(p); setText(p.prd_markdown); }}>{p.title}<div className="text-xs text-muted">{p.version} · {p.status}</div></button>)}</div></aside><section className="space-y-3"><div className="flex gap-2"><button className="btn"><RefreshCw size={15} />重新生成</button><button className="btn" onClick={doReview}><ShieldCheck size={15} />Reviewer 评审</button><button className="btn"><Save size={15} />保存终稿</button><button className="btn"><Download size={15} />导出 Markdown</button></div><PrdEditor value={text} onChange={setText} /></section><ReviewerPanel data={review} /></div></div>;
}

