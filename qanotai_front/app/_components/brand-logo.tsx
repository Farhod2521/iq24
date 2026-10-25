import Image from "next/image";

/*
 * The IQ24 logo, assembled from its pieces (public/brand: I, Q, the graduation cap, 2, 4 — cut from the artwork,
 * so together they are exactly the original). Animated: the letters spring up one after another, the cap drops
 * onto the Q and settles with a wobble, then a light sweeps across the whole mark (and again every few seconds).
 * Hover tips the cap. Pure CSS (globals.css, .iq24*), so it also works in server components; reduced motion shows
 * the finished logo.
 */
const PARTS = [
  { key: "I", box: { left: 4.453, top: 27.959, width: 10.372, height: 63.36 } },
  { key: "Q", box: { left: 14.656, top: 32.92, width: 38.557, height: 63.472 } },
  { key: "2", box: { left: 51.635, top: 35.513, width: 23.055, height: 55.693 } },
  { key: "4", box: { left: 71.026, top: 36.077, width: 27.959, height: 55.13 } },
] as const;
const CAP = { left: 14.487, top: 3.608, width: 42.052, height: 40.586 };

const pct = (b: { left: number; top: number; width: number; height: number }) => ({
  left: `${b.left}%`,
  top: `${b.top}%`,
  width: `${b.width}%`,
  height: `${b.height}%`,
});

export function BrandLogo({ className = "h-9", animated = true }: { className?: string; animated?: boolean }) {
  return (
    <span role="img" aria-label="IQ24" className={`iq24 ${animated ? "iq24-anim" : ""} ${className}`}>
      {PARTS.map((p, i) => (
        <span key={p.key} className="iq24-part iq24-letter" style={{ ...pct(p.box), animationDelay: `${i * 90}ms` }}>
          <Image src={`/brand/iq24-${p.key}.webp`} alt="" fill unoptimized priority className="object-contain" />
        </span>
      ))}
      <span className="iq24-part iq24-cap" style={pct(CAP)}>
        <span className="iq24-cap-tilt">
          <Image src="/brand/iq24-cap.webp" alt="" fill unoptimized priority className="object-contain" />
        </span>
      </span>
      <span className="iq24-shine" aria-hidden="true" />
    </span>
  );
}
