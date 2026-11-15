import type {
  AnalyzeResponse,
  ClassifierResponse,
  HistoryEntry,
  Outcome,
  StatsResponse,
  TargetCode,
  TranslateResponse,
} from "./types";

export const API_URL: string = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(
  /\/$/,
  "",
);

const UNREACHABLE = `L'API ne répond pas (${API_URL}). Lancez-la avec uvicorn, puis réessayez.`;

/** Transforme une réponse d'erreur de l'API en phrase compréhensible. */
export function describeError(status: number, detail: unknown): string {
  if (status === 422) return "Le texte est vide ou dépasse 5 000 caractères.";
  if (typeof detail === "string" && detail) return detail;
  return `L'API a répondu par une erreur (code ${status}).`;
}

async function call<T>(path: string, init?: RequestInit): Promise<Outcome<T>> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, init);
  } catch {
    return { ok: false, message: UNREACHABLE };
  }
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = (body as { detail?: unknown } | null)?.detail;
    return { ok: false, message: describeError(response.status, detail) };
  }
  return { ok: true, data: body as T };
}

function post<T>(path: string, payload: unknown): Promise<Outcome<T>> {
  return call<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export const checkHealth = () => call<{ status: string }>("/health");
export const analyze = (text: string) => post<AnalyzeResponse>("/analyze", { text });
export const sentiment = (text: string) => post<ClassifierResponse>("/sentiment", { text });
export const offensive = (text: string) => post<ClassifierResponse>("/offensive", { text });
export const translate = (text: string, targets: TargetCode[]) =>
  post<TranslateResponse>("/translate", { text, targets });
export const addHistory = (entry: HistoryEntry) => post<{ id: number }>("/history", entry);
export const getStats = () => call<StatsResponse>("/stats");
export const clearHistory = () => call<null>("/history", { method: "DELETE" });
