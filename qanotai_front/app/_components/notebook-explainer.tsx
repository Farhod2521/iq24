import { MathText } from "./math-text";
import { INK, PAPER } from "./hand-solution";

/** Detailed illustrated notebook solution as stored on a question (backend: app/solution.py Explainer). */
export type ExplainerBlock = {
  type: "text" | "formula" | "figure" | "step" | "tip";
  title?: string;
  text?: string;
  tex?: string;
  where?: string[];
  /** figure block: sanitized SVG drawn by the backend (allowlisted elements only) */
  svg?: string;
};
export type Explainer = { blocks: ExplainerBlock[] };

function Block({ b, step }: { b: ExplainerBlock; step: number }) {
  switch (b.type) {
    case "figure":
      return (
        <figure className="flex flex-col items-center gap-2">
          {b.title && (
            <figcaption className="self-start text-[1.6rem]">
              <MathText text={b.title} />:
            </figcaption>
          )}
          {/* sketch drawn in the notebook: the backend renders and sanitizes it; CSS (.nb-fig) gives it pen ink */}
          <div className="nb-fig w-full max-w-[34rem]" dangerouslySetInnerHTML={{ __html: b.svg ?? "" }} />
        </figure>
      );
    case "formula":
      return (
        <div className="flex flex-col gap-3">
          <div className="w-fit border-2 border-current px-6 py-3 text-[1.9rem]">
            <MathText text={`$${b.tex ?? ""}$`} />
          </div>
          {b.where && b.where.length > 0 && (
            <div className="ml-4 text-[1.5rem] leading-snug">
              <p>bu yerda:</p>
              {b.where.map((w, i) => (
                <p key={i} className="ml-4">
                  <MathText text={w} />
                </p>
              ))}
            </div>
          )}
        </div>
      );
    case "step":
      return (
        <div>
          <p className="text-[1.75rem] leading-tight">
            <span className="rounded-lg bg-brand-100/70 px-2">
              <MathText text={b.title || `${step}-qadam`} />
            </span>
          </p>
          {b.text && (
            <p className="mt-2 ml-6 whitespace-pre-wrap text-[1.6rem] leading-snug">
              <MathText text={b.text} />
            </p>
          )}
        </div>
      );
    case "tip":
      return (
        <div className="-rotate-[0.6deg] border-l-4 border-rose-400 pl-4 text-[1.6rem] leading-snug text-rose-700">
          <span className="mr-2 font-bold">Eslatma!</span>
          <MathText text={b.text ?? ""} />
        </div>
      );
    default:
      return (
        <p className="whitespace-pre-wrap text-[1.6rem] leading-snug">
          {b.title && <span className="mr-2 underline decoration-2 underline-offset-4">{b.title}:</span>}
          <MathText text={b.text ?? ""} />
        </p>
      );
  }
}

/** The second handwritten solution: same notebook page, slow and picture-first, for students who are lost. */
export function NotebookExplainer({ explainer }: { explainer: Explainer }) {
  // running number of each "step" block, for steps the model left untitled
  const steps = explainer.blocks.map((_, i) => explainer.blocks.slice(0, i + 1).filter((x) => x.type === "step").length);
  return (
    <div className={`overflow-x-auto rounded-2xl p-6 font-hand font-semibold ring-1 ring-brand-100 sm:p-8 ${INK}`} style={PAPER}>
      <div className="flex max-w-3xl flex-col gap-6">
        {explainer.blocks.map((b, i) => (
          <Block key={i} b={b} step={steps[i]} />
        ))}
      </div>
    </div>
  );
}
