const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store", ...init });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const api = {
  createConversation: (title?: string) => request<any>("/api/conversations", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title }) }),
  conversations: () => request<any[]>("/api/conversations"),
  conversation: (id: string) => request<any>(`/api/conversations/${id}`),
  workspace: (id: string) => request<any>(`/api/conversations/${id}/workspace`),
  dashboard: () => request<any>("/api/dashboard"),
  files: (conversationId?: string) => request<any[]>(`/api/upload/files${conversationId ? `?conversation_id=${conversationId}` : ""}`),
  upload: (file: File, conversationId = "legacy") => {
    const fd = new FormData();
    fd.append("file", file);
    return request<any>(`/api/upload?conversation_id=${conversationId}`, { method: "POST", body: fd });
  },
  parseFile: (id: number) => request<any>(`/api/upload/files/${id}/parse`, { method: "POST" }),
  confirmSchema: (id: number, mapping: any) => request<any>(`/api/upload/files/${id}/confirm-schema`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ mapping }) }),
  ingestFile: (id: number) => request<any>(`/api/upload/files/${id}/ingest`, { method: "POST" }),
  feedback: (params = "") => request<any[]>(`/api/feedback${params}`),
  clusters: () => request<any[]>("/api/clusters"),
  generateClusters: (conversationId?: string) => request<any[]>(`/api/clusters/generate${conversationId ? `?conversation_id=${conversationId}` : ""}`, { method: "POST" }),
  opportunities: () => request<any[]>("/api/opportunities"),
  generateOpportunities: (conversationId?: string) => request<any[]>(`/api/opportunities/generate${conversationId ? `?conversation_id=${conversationId}` : ""}`, { method: "POST" }),
  runAgent: (task: string, conversation_id = "legacy") => request<any>("/api/agent/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ task, conversation_id }) }),
  steps: (runId: number) => request<any[]>(`/api/agent/runs/${runId}/steps`),
  prds: (conversationId?: string) => request<any[]>(`/api/prd${conversationId ? `?conversation_id=${conversationId}` : ""}`),
  generatePrd: (opportunity_id: number, conversation_id?: string) => request<any>("/api/prd/generate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ opportunity_id, conversation_id }) }),
  reviewPrd: (id: number) => request<any>(`/api/prd/${id}/review`, { method: "POST" }),
  memory: () => request<any>("/api/memory"),
  confirmMemory: (memory_id: number, confirmed = true) => request<any>("/api/memory/confirm", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ memory_id, memory_type: "project", confirmed }) }),
  evaluation: async (conversationId?: string) => {
    const qs = conversationId ? `?conversation_id=${conversationId}` : "";
    return {
    overview: await request<any>(`/api/evaluation/overview${qs}`),
    llm: await request<any>(`/api/evaluation/llm${qs}`),
    retrieval: await request<any>(`/api/evaluation/retrieval${qs}`),
    compression: await request<any>(`/api/evaluation/compression${qs}`),
    quality: await request<any>(`/api/evaluation/quality${qs}`)
  };
  }
};
