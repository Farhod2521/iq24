// SAMPLE DATA. The backend has no lessons, tests or progress yet, so the dashboard renders these
// placeholder numbers. Replace each export with an API call once those endpoints exist — the widgets
// only depend on the shapes below. (The user's name and avatar already come from /api/auth/me.)

export const topStats = { streakDays: 12, coins: 320, points: 1250 };

export const dailyGoal = {
  lessonsDone: 3,
  lessonsTotal: 5,
  tasks: [
    { label: "1 ta dars ko'rish", done: true },
    { label: "5 ta test yechish", done: true },
    { label: "15 daqiqa o'qish", done: false },
    { label: "Yangi mavzu boshlash", done: false },
  ],
};

export const weekDays = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"];
export const weeklyLessons: Record<string, number[]> = {
  "Bu hafta": [1, 3.5, 3.4, 3, 6, 3.3, 4],
  "O'tgan hafta": [2, 2.5, 4, 1.5, 3, 5, 2],
};

export const weeklySummary = [
  { kind: "lessons", value: "24", label: "Bajarilgan darslar" },
  { kind: "accuracy", value: "78%", label: "To'g'ri javoblar" },
  { kind: "time", value: "12 soat", label: "O'qish vaqti" },
  { kind: "growth", value: "+320", label: "O'sish" },
] as const;
