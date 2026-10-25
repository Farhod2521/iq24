"use client";

import Image from "next/image";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { adminApi, type Book, type Subject } from "../../_lib/admin-api";
import { ApiError } from "../../_lib/api";
import { BookOpen } from "../../_components/icons";
import { Field, inputClass, Modal, primaryButton } from "./ui";

/** Create (book = null) or edit a book. Calls onSaved with the stored book. */
export function BookFormModal({
  book,
  onClose,
  onSaved,
}: {
  book: Book | null;
  onClose: () => void;
  onSaved: (book: Book) => void;
}) {
  const [subjects, setSubjects] = useState<Subject[] | null>(null);
  const [title, setTitle] = useState(book?.title ?? "");
  const [subjectId, setSubjectId] = useState(book?.subject_id ? String(book.subject_id) : "");
  const [year, setYear] = useState(book?.year ? String(book.year) : String(new Date().getFullYear()));
  const [description, setDescription] = useState(book?.description ?? "");
  const [cover, setCover] = useState<string | null>(book?.cover_url ?? null);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    adminApi
      .subjects()
      .then(setSubjects)
      .catch(() => setError("Fanlar ro'yxatini yuklab bo'lmadi"));
  }, []);

  async function pickCover(file: File | undefined) {
    if (!file) return;
    setError("");
    setUploading(true);
    try {
      setCover((await adminApi.upload(file)).url);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Rasmni yuklab bo'lmadi");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (title.trim().length < 2) return setError("Kitob nomini kiriting");
    if (!subjectId) return setError("Fanni tanlang");
    setError("");
    setSaving(true);
    const data = {
      title: title.trim(),
      subject_id: Number(subjectId),
      year: year ? Number(year) : null,
      test_count: book?.test_count ?? 0,
      description: description.trim() || null,
      cover_url: cover,
    };
    try {
      onSaved(book ? await adminApi.updateBook(book.id, data) : await adminApi.createBook(data));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Saqlab bo'lmadi");
      setSaving(false);
    }
  }

  return (
    <Modal title={book ? "Kitobni tahrirlash" : "Yangi kitob qo'shish"} onClose={onClose}>
      <form onSubmit={submit} noValidate className="grid gap-6 sm:grid-cols-[180px_1fr]">
        {/* cover */}
        <div className="flex flex-col items-center gap-3">
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            className="group relative grid aspect-[3/4] w-full place-items-center overflow-hidden rounded-2xl bg-gradient-to-b from-brand-50 to-white ring-1 ring-brand-100 transition hover:ring-brand-300"
          >
            {cover ? (
              <Image src={cover} alt="Muqova" fill unoptimized className="object-contain p-2" />
            ) : (
              <span className="flex flex-col items-center gap-2 px-4 text-center text-sm text-muted">
                <BookOpen className="size-8 text-brand-400" />
                Muqova rasmini yuklang
              </span>
            )}
            {uploading && (
              <span className="absolute inset-0 grid place-items-center bg-white/70">
                <span className="size-8 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
              </span>
            )}
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={(e) => pickCover(e.target.files?.[0])}
          />
          <div className="flex gap-3 text-xs font-semibold">
            <button type="button" onClick={() => fileRef.current?.click()} className="text-brand-600 hover:underline">
              {cover ? "Almashtirish" : "Tanlash"}
            </button>
            {cover && (
              <button type="button" onClick={() => setCover(null)} className="text-rose-600 hover:underline">
                Olib tashlash
              </button>
            )}
          </div>
          <p className="text-center text-[11px] text-muted">JPG, PNG yoki WEBP, 5 MB gacha</p>
        </div>

        {/* fields */}
        <div className="flex flex-col gap-4">
          <Field label="Kitob nomi">
            <input className={inputClass} value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Masalan: Matematika 1-qism" />
          </Field>
          <Field label="Fan">
            <select className={inputClass} value={subjectId} onChange={(e) => setSubjectId(e.target.value)} disabled={!subjects}>
              <option value="">{subjects ? "Fanni tanlang" : "Yuklanmoqda…"}</option>
              {subjects?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Nashr yili">
            <input className={inputClass} inputMode="numeric" value={year} onChange={(e) => setYear(e.target.value.replace(/\D/g, "").slice(0, 4))} />
          </Field>
          <Field label="Tavsif" hint="Ixtiyoriy">
            <textarea className={`${inputClass} resize-none`} rows={3} value={description} onChange={(e) => setDescription(e.target.value)} />
          </Field>

          {error && <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700 ring-1 ring-rose-100">{error}</p>}

          <div className="mt-2 flex justify-end gap-3">
            <button type="button" onClick={onClose} className="rounded-xl px-5 py-3 text-sm font-semibold text-muted hover:bg-brand-50">
              Bekor qilish
            </button>
            <button type="submit" disabled={saving || uploading} className={primaryButton}>
              {saving ? "Saqlanmoqda…" : book ? "Saqlash" : "Qo'shish"}
            </button>
          </div>
        </div>
      </form>
    </Modal>
  );
}
