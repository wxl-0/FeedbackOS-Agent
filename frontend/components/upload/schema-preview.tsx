export function SchemaPreview({ file }: { file: any }) {
  const mapping = file?.schema?.mapping || {};
  return <div className="rounded-md border border-line bg-slate-50 p-3 text-xs">
    <div className="mb-2 font-medium text-ink">字段映射结果</div>
    {Object.keys(mapping).length ? Object.entries(mapping).map(([k, v]) => <div key={k} className="flex justify-between gap-4 py-1"><span className="text-muted">{k}</span><span>{String(v || "-")}</span></div>) : <div className="text-muted">文本文件无表格字段映射</div>}
  </div>;
}

