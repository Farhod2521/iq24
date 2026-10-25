"use client";

import { useState } from "react";
import { HandSolution, type Solution } from "./hand-solution";
import { NotebookExplainer, type Explainer } from "./notebook-explainer";

const TABS = [
  { key: "short", label: "Qisqa yechim" },
  { key: "detailed", label: "Batafsil (rasmli) yechim" },
] as const;

/** A question's handwritten solutions: the short notebook one, and — when there is one — the detailed one. */
export function Solutions({ solution, explainer }: { solution?: Solution | null; explainer?: Explainer | null }) {
  const [tab, setTab] = useState<(typeof TABS)[number]["key"]>(solution ? "short" : "detailed");
  if (!explainer) return solution ? <HandSolution solution={solution} /> : null;
  return (
    <div className="flex flex-col gap-3">
      <div role="tablist" className="flex w-fit gap-1 rounded-xl bg-slate-100 p-1">
        {TABS.filter((t) => t.key === "detailed" || solution).map((t) => (
          <button
            key={t.key}
            type="button"
            role="tab"
            aria-selected={tab === t.key}
            onClick={() => setTab(t.key)}
            className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${tab === t.key ? "bg-white text-brand-700 shadow" : "text-muted hover:text-ink"}`}
          >
            {t.label}
          </button>
        ))}
      </div>
      {tab === "short" && solution ? <HandSolution solution={solution} /> : <NotebookExplainer explainer={explainer} />}
    </div>
  );
}
