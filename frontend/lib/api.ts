import { API_URL } from "./config";
import { getToken } from "./auth";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!(options.body instanceof FormData) && options.body) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export interface DocumentItem {
  id: string;
  filename: string;
  status: string;
  mime_type: string;
  size: number;
  created_at: string;
}

export interface SearchResultItem {
  chunk_id: string;
  document_id: string;
  content: string;
  score: number;
}

export interface ChatSource {
  chunk_id: string;
  document_id: string;
  score: number;
  excerpt: string;
}

export interface ChatResponse {
  conversation_id: string;
  answer: string;
  sources: ChatSource[];
}

export const api = {
  register: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) }),

  login: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),

  getDocuments: () => request<DocumentItem[]>("/documents"),

  uploadDocument: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<DocumentItem>("/documents/upload", { method: "POST", body: form });
  },

  deleteDocument: (id: string) => request<void>(`/documents/${id}`, { method: "DELETE" }),

  reindexDocument: (id: string) => request<DocumentItem>(`/documents/${id}/reindex`, { method: "POST" }),

  search: (query: string, top_k = 5) =>
    request<{ results: SearchResultItem[] }>("/search", { method: "POST", body: JSON.stringify({ query, top_k }) }),

  chat: (message: string, conversation_id?: string) =>
    request<ChatResponse>("/chat", { method: "POST", body: JSON.stringify({ message, conversation_id, stream: false }) }),

  agent: (question: string) =>
    request<{ answer: string; tool_calls: unknown[] }>("/agent", { method: "POST", body: JSON.stringify({ question }) }),

  feedback: (question: string, answer: string, sources: unknown[], rating: 1 | -1) =>
    request<{ status: string }>("/feedback", { method: "POST", body: JSON.stringify({ question, answer, sources, rating }) }),

  health: () => request<{ status: string }>("/health"),
};
