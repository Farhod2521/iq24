// Thin client for the FastAPI backend. All calls go to same-origin /api/* (proxied by next.config.ts),
// so the httpOnly session cookie rides along automatically.

export type User = {
  id: number;
  full_name: string;
  email: string | null;
  phone: string | null;
  avatar_url: string | null;
  telegram_username: string | null;
  has_google: boolean;
  has_telegram: boolean;
  plan: string;
  is_superadmin: boolean;
  created_at: string;
};

export type TelegramStart = { token: string; url: string; expires_in: number };
export type TelegramStatus = "pending" | "confirmed" | "rejected" | "expired" | "used";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, { cache: "no-store", ...init });
  if (!res.ok) {
    const detail = (await res.json().catch(() => null))?.detail;
    // FastAPI sends a string for HTTPException, a list of field errors for validation failures
    const message = typeof detail === "string" ? detail : detail ? "Ma'lumotlar noto'g'ri to'ldirilgan" : null;
    throw new ApiError(res.status, message ?? "Server bilan bog'lanib bo'lmadi");
  }
  return res.status === 204 ? (undefined as T) : res.json();
}

/** The signed-in user, or null when nobody is signed in. */
export async function getMe(): Promise<User | null> {
  try {
    return await request<User>("/auth/me");
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) return null;
    throw e;
  }
}

export const logout = () => request<void>("/auth/logout", { method: "POST" });
export const startTelegramLogin = () => request<TelegramStart>("/auth/telegram/start", { method: "POST" });
export const telegramLoginStatus = (token: string) =>
  request<{ status: TelegramStatus }>(`/auth/telegram/status/${encodeURIComponent(token)}`).then((r) => r.status);

export const GOOGLE_LOGIN_URL = "/api/auth/google/login";

export const LOGIN_ERRORS: Record<string, string> = {
  google: "Google orqali kirishda xatolik yuz berdi. Qaytadan urinib ko'ring.",
  google_not_configured: "Google orqali kirish hali sozlanmagan.",
};

/** A book as students see it, with the tests actually written for it. */
export type CatalogBook = {
  id: number;
  title: string;
  subject: string;
  year: number | null;
  cover_url: string | null;
  topics: number;
  tests: number;
};

export const getCatalogBooks = () => request<CatalogBook[]>("/catalog/books");

import type { Solution } from "../_components/hand-solution";
import type { Explainer } from "../_components/notebook-explainer";

export type CatalogTopic = {
  id: number;
  kind: "lesson" | "review" | "answers" | "section";
  number: number | null;
  title: string;
  tests: number;
  best_percent: number | null;
  attempts: number;
};
export type CatalogBookPage = CatalogBook & { description: string | null; topic_list: CatalogTopic[] };

export type Difficulty = "easy" | "medium" | "hard";
export type TestQuestion = { id: number; difficulty: Difficulty; text: string; options: string[]; image_url: string | null };
export type TopicTest = {
  topic_id: number;
  topic_title: string;
  topic_number: number | null;
  book_id: number;
  book_title: string;
  questions: TestQuestion[];
};
export type TestResult = {
  attempt_id: number;
  total: number;
  correct: number;
  wrong: number;
  skipped: number;
  percent: number;
  duration_seconds: number;
  best_percent: number;
  previous_percent: number | null;
  by_level: { difficulty: Difficulty; total: number; correct: number }[];
  review: (TestQuestion & {
    chosen: number | null;
    correct: number;
    is_correct: boolean;
    explanation: string | null;
    solution?: Solution | null;
    explainer?: Explainer | null;
  })[];
};

export const getCatalogBook = (id: number) => request<CatalogBookPage>(`/catalog/books/${id}`);
export const getTopicTest = (topicId: number) => request<TopicTest>(`/catalog/topics/${topicId}/test`);
export const submitTopicTest = (topicId: number, answers: Record<number, number | null>, durationSeconds: number) =>
  request<TestResult>(`/catalog/topics/${topicId}/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers, duration_seconds: durationSeconds }),
  });
