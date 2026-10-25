"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { adminApi, type Subject, type SubjectColor } from "../../_lib/admin-api";
import { ApiError } from "../../_lib/api";
import { Layers } from "../../_components/icons";
import { useAdmin } from "../_components/shell";
import { card, Field, inputClass, Modal, PageHead, primaryButton, SUBJECT_COLORS } from "../_components/ui";

function SubjectForm({ subject, onClose, onSaved }: { subject: Subject | null; onClose: () => void; onSaved: (name: string) => void }) {
  const [name, setName] = useState(subject?.name ?? "");
  const [color, setColor] = useState<SubjectColor>(subject?.color ?? "blue");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (name.trim().length < 2) return setError("Fan nomini kiriting");
    setSaving(true);
    try {
      if (subject) await adminApi.updateSubject(subject.id, { name: name.trim(), color });
      else await adminApi.createSubject({ name: name.trim(), color });
      onSaved(name.trim());
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Saqlab bo'lmadi");
      setSaving(false);
    }
  }

  return (
    <Modal title={subject ? "Fanni tahrirlash" : "Yangi fan"} onClose={onClose}>
      <form onSubmit={submit} noValidate className="flex flex-col gap-5">
        <Field label="Fan nomi">
          <input className={inputClass} value={name} onChange={(e) => setName(e.target.value)} placeholder="Masalan: Biologiya" autoFocus />
        </Field>
        <fieldset>
          <legend className="text-sm font-semibold text-ink">Rang</legend>
          <div className="mt-2 flex flex-wrap gap-2">
            {(Object.keys(SUBJECT_COLORS) as SubjectColor[]).map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => setColor(c)}
                aria-pressed={color === c}
                className={`flex items-center gap-2 rounded-xl px-3 py-2 text-sm ring-1 transition ${
                  color === c ? "bg-brand-50 font-semibold text-ink ring-brand-400" : "text-muted ring-brand-100 hover:bg-brand-50/50"
                }`}
              >
                <span className={`size-3.5 rounded-full ${SUBJECT_COLORS[c].dot}`} /> {SUBJECT_COLORS[c].label}
              </button>
            ))}
          </div>
        </fieldset>
        {error && <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">{error}</p>}
        <div className="flex justify-end gap-3">
          <button type="button" onClick={onClose} className="rounded-xl px-5 py-3 text-sm font-semibold text-muted hover:bg-brand-50">
            Bekor qilish
          </button>
          <button type="submit" disabled={saving} className={primaryButton}>
            {saving ? "Saqlanmoqda…" : "Saqlash"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export function SubjectsView() {
  const { version, ask, notify } = useAdmin();
  const router = useRouter();
  const params = useSearchParams();
  const [subjects, setSubjects] = useState<Subject[] | null>(null);
  const [editing, setEditing] = useState<{ subject: Subject | null } | null>(null);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);

  // "?new=1" (from the dashboard's quick actions) opens the form straight away
  const wantsNew = params.get("new") === "1";
  const formOpen = editing ?? (wantsNew ? { subject: null } : null);

  useEffect(() => {
    adminApi
      .subjects()
      .then(setSubjects)
      .catch(() => setError("Fanlarni yuklab bo'lmadi"));
  }, [version, reload]);

  const close = useCallback(() => {
    setEditing(null);
    if (wantsNew) router.replace("/superadmin/subjects");
  }, [wantsNew, router]);

  function remove(s: Subject) {
    ask({
      title: "Fanni o'chirish",
      message: (
        <>
          <b className="text-ink">«{s.name}»</b> fani o&apos;chiriladi.
          {s.books > 0 && ` Unda ${s.books} ta kitob bor — avval ularni o'chirish kerak.`}
        </>
      ),
      onConfirm: async () => {
        await adminApi.deleteSubject(s.id);
        notify("Muvaffaqiyatli o'chirildi", "success", `«${s.name}» fani o'chirildi`);
        setReload((r) => r + 1);
      },
    });
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHead
        title="Fanlar"
        subtitle="Platformadagi fanlar, ulardagi kitoblar va testlar soni"
        action={
          <button type="button" onClick={() => setEditing({ subject: null })} className={primaryButton}>
            + Yangi fan
          </button>
        }
      />

      {error && <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">{error}</p>}

      {subjects === null ? (
        <div className="grid h-60 place-items-center">
          <span className="size-10 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
        </div>
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {subjects.map((s) => {
            const c = SUBJECT_COLORS[s.color] ?? SUBJECT_COLORS.blue;
            return (
              <li key={s.id} className={`flex items-center gap-4 p-5 ${card}`}>
                <span className={`grid size-12 shrink-0 place-items-center rounded-2xl ${c.soft}`}>
                  <Layers className="size-6" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate font-bold text-ink">{s.name}</p>
                  <p className="text-xs text-muted">
                    {s.books} ta kitob · {s.tests.toLocaleString("ru-RU")} ta test
                  </p>
                </div>
                <div className="flex shrink-0 gap-1.5">
                  <button
                    type="button"
                    onClick={() => setEditing({ subject: s })}
                    className="rounded-lg bg-brand-50 px-3 py-2 text-xs font-semibold text-brand-600 hover:bg-brand-100"
                  >
                    Tahrirlash
                  </button>
                  <button type="button" onClick={() => remove(s)} className="rounded-lg px-3 py-2 text-xs font-semibold text-rose-600 ring-1 ring-rose-100 hover:bg-rose-50">
                    O&apos;chirish
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}

      {formOpen && (
        <SubjectForm
          subject={formOpen.subject}
          onClose={close}
          onSaved={(name) => {
            notify(formOpen.subject ? "Fan saqlandi" : "Fan qo'shildi", "success", name);
            close();
            setReload((r) => r + 1);
          }}
        />
      )}
    </div>
  );
}
