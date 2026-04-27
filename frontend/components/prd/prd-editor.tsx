"use client";
export function PrdEditor({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return <textarea className="min-h-[620px] w-full resize-y rounded-md border border-line bg-white p-4 font-mono text-sm leading-6 outline-none focus:border-brand" value={value} onChange={e => onChange(e.target.value)} />;
}

