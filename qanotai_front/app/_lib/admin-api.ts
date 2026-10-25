// Superadmin endpoints (/api/admin/*). The backend rejects anyone who isn't a superadmin with 403.
import type { Solution } from "../_components/hand-solution";
import type { Explainer } from "../_components/notebook-explainer";
import { request } from "./api";

export type Growth = number | null;

export type Overview = {
  users: {
    total: number;
    new_today: number;
    new_today_growth: Growth;
    active_today: number;
    active_today_growth: Growth;
    weekly_growth: Growth;
  };
  subjects: number;
  books: number;
  tests: number;
  days: { label: string; date: string; new: number; active: number }[];
  per_subject: { id: number; name: string; color: SubjectColor; books: number; tests: number }[];
  activity: { kind: "user" | "book"; title: string; detail: string; at: string }[];
};

export type AdminUser = {
  id: number;
  full_name: string;
  email: string | null;
  phone: string | null;
  telegram_username: string | null;
  avatar_url: string | null;
  has_google: boolean;
  has_telegram: boolean;
  plan: string;
  created_at: string;
  last_login_at: string | null;
};

export type SubjectColor = "blue" | "violet" | "emerald" | "rose" | "amber" | "sky" | "slate";
export type Subject = { id: number; name: string; color: SubjectColor; books: number; tests: number };

export type Book = {
  id: number;
  title: string;
  subject_id: number;
  subject_name: string;
  year: number | null;
  description: string | null;
  cover_url: string | null;
  test_count: number;
  topic_count: number;
  created_at: string;
};
export type BookInput = Pick<Book, "title" | "subject_id" | "year" | "description" | "cover_url" | "test_count">;

export type TopicKind = "lesson" | "review" | "answers" | "section";
export type Topic = {
  id: number;
  position: number;
  kind: TopicKind;
  number: number | null;
  title: string;
  page: number | null;
  question_count: number;
};
export type TopicInput = Pick<Topic, "kind" | "number" | "title">;

export type Difficulty = "easy" | "medium" | "hard";
export type Question = {
  id: number;
  position: number;
  difficulty: Difficulty;
  text: string;
  options: string[];
  correct: number;
  explanation: string | null;
  /** figure shown with the question (/api/media/...) */
  image_url: string | null;
  /** step-by-step notebook solution */
  solution?: Solution | null;
  /** detailed illustrated notebook solution (physics) */
  explainer?: Explainer | null;
};
export type QuestionInput = Omit<Question, "id" | "position" | "image_url"> & {
  image_url?: string | null;
  /** AI drafts carry their figure as sanitized SVG; the backend stores it on save */
  figure_svg?: string;
};
export type TopicDetail = Topic & { book_id: number; book_title: string; questions: Question[] };

/** AI connection from .env (AI_URL / AI_KEY / AI_MODEL); the key never leaves the backend */
export type AiStatus = { configured: boolean; host: string; model: string };
export type GenerateResult = {
  questions: QuestionInput[];
  host: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  /** e.g. fewer questions with a figure came back than were asked for */
  warning: string;
};
export type BookDetail = Book & { topics: Topic[] };

const json = (method: string, body: unknown): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const adminApi = {
  overview: () => request<Overview>("/admin/overview"),
  users: (q: string, page: number) =>
    request<{ total: number; page: number; per_page: number; items: AdminUser[] }>(
      `/admin/users?${new URLSearchParams({ q, page: String(page) })}`,
    ),

  subjects: () => request<Subject[]>("/admin/subjects"),
  createSubject: (data: { name: string; color: SubjectColor }) => request<Subject>("/admin/subjects", json("POST", data)),
  updateSubject: (id: number, data: { name: string; color: SubjectColor }) =>
    request<Subject>(`/admin/subjects/${id}`, json("PUT", data)),
  deleteSubject: (id: number) => request<void>(`/admin/subjects/${id}`, { method: "DELETE" }),

  books: (params: { subject_id?: number; q?: string } = {}) => {
    const qs = new URLSearchParams();
    if (params.subject_id) qs.set("subject_id", String(params.subject_id));
    if (params.q) qs.set("q", params.q);
    return request<Book[]>(`/admin/books?${qs}`);
  },
  createBook: (data: BookInput) => request<Book>("/admin/books", json("POST", data)),
  updateBook: (id: number, data: BookInput) => request<Book>(`/admin/books/${id}`, json("PUT", data)),
  deleteBook: (id: number) => request<void>(`/admin/books/${id}`, { method: "DELETE" }),
  book: (id: number) => request<BookDetail>(`/admin/books/${id}`),

  createTopic: (bookId: number, data: TopicInput) => request<Topic>(`/admin/books/${bookId}/topics`, json("POST", data)),
  updateTopic: (id: number, data: TopicInput) => request<Topic>(`/admin/topics/${id}`, json("PUT", data)),
  deleteTopic: (id: number) => request<void>(`/admin/topics/${id}`, { method: "DELETE" }),
  reorderTopics: (bookId: number, ids: number[]) => request<Topic[]>(`/admin/books/${bookId}/topics/order`, json("PUT", { ids })),

  topic: (id: number) => request<TopicDetail>(`/admin/topics/${id}`),
  createQuestion: (topicId: number, data: QuestionInput) => request<Question>(`/admin/topics/${topicId}/questions`, json("POST", data)),
  updateQuestion: (id: number, data: QuestionInput) => request<Question>(`/admin/questions/${id}`, json("PUT", data)),
  deleteQuestion: (id: number) => request<void>(`/admin/questions/${id}`, { method: "DELETE" }),

  /** Claude drafts tests for a topic; nothing is stored until saveQuestions. */
  aiStatus: () => request<AiStatus>("/admin/ai/status"),
  generateQuestions: (
    topicId: number,
    data: { difficulty: Difficulty | "mixed"; count: number; figure_count: number; notes?: string },
  ) =>
    request<GenerateResult>(`/admin/topics/${topicId}/questions/generate`, json("POST", data)),
  saveQuestions: (topicId: number, questions: QuestionInput[]) =>
    request<Question[]>(`/admin/topics/${topicId}/questions/bulk`, json("POST", { questions })),

  upload: (file: File) => {
    const body = new FormData();
    body.append("file", file);
    return request<{ url: string }>("/admin/uploads", { method: "POST", body });
  },
};
