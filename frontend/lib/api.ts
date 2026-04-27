const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store", ...init });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const api = {
  dashboard: () => request<any>("/api/dashboard"),
  files: () => request<any[]>("/api/upload/files"),
  upload: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return request<any>("/api/upload", { method: "POST", body: fd });
  },
  parseFile: (id: number) => request<any>(`/api/upload/files/${id}/parse`, { method: "POST" }),
  confirmSchema: (id: number, mapping: any) => request<any>(`/api/upload/files/${id}/confirm-schema`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ mapping }) }),
  ingestFile: (id: number) => request<any>(`/api/upload/files/${id}/ingest`, { method: "POST" }),
  feedback: (params = "") => request<any[]>(`/api/feedback${params}`),
  clusters: () => request<any[]>("/api/clusters"),
  generateClusters: () => request<any[]>("/api/clusters/generate", { method: "POST" }),
  opportunities: () => request<any[]>("/api/opportunities"),
  generateOpportunities: () => request<any[]>("/api/opportunities/generate", { method: "POST" }),
  runAgent: (task: string) => request<any>("/api/agent/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ task }) }),
  steps: (runId: number) => request<any[]>(`/api/agent/runs/${runId}/steps`),
  prds: () => request<any[]>("/api/prd"),
  generatePrd: (opportunity_id: number) => request<any>("/api/prd/generate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ opportunity_id }) }),
  reviewPrd: (id: number) => request<any>(`/api/prd/${id}/review`, { method: "POST" }),
  memory: () => request<any>("/api/memory"),
  confirmMemory: (memory_id: number, confirmed = true) => request<any>("/api/memory/confirm", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ memory_id, memory_type: "project", confirmed }) }),
  evaluation: async () => ({
    overview: await request<any>("/api/evaluation/overview"),
    llm: await request<any>("/api/evaluation/llm"),
    retrieval: await request<any>("/api/evaluation/retrieval"),
    compression: await request<any>("/api/evaluation/compression"),
    quality: await request<any>("/api/evaluation/quality")
  })
};

