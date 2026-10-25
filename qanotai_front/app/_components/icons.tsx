import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

function Stroke({ children, ...props }: IconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  );
}

/** QANOT.AI eagle, traced from the brand artwork (same shape as public/images/qanot-logo.svg and app/icon.svg). */
export const LOGO_VIEWBOX = { w: 1318, h: 757 };
export const LOGO_PATH =
  "M656.6 745.9C651.9 737.2 636.2 712.3 628.6 701.5C604 666.6 572.2 634.3 539.9 611.4C525.1 600.8 511.9 592.8 499.1 586.4L486.7 580.2L496.6 574.5C528.8 555.8 551.8 540.6 566.5 528.5C577.7 519.2 594.6 502.3 591.5 503.5C548.2 520 521.6 526.2 482.5 529C440.4 532.1 387.4 523.5 350 507.5C335.3 501.2 309 486.2 309 484C309 483.6 312.5 482.7 316.8 482.1C326.5 480.5 354.7 473.6 363.7 470.6L370.5 468.3L357.5 467.6C306 464.8 269.5 452.2 237.4 425.9C228.4 418.6 212.8 402.1 207.2 394.2C203.4 388.7 203 387.6 205 387.8C232.7 390 264.1 391.2 284 390.6C317.3 389.7 336 388.8 336 388C336 387.7 330.7 386.8 324.2 386.1C274.6 380.8 221.8 363.2 183.8 339.3C167.7 329.2 159.2 322.3 144.5 307.6C129.9 292.9 120.1 280.1 110.1 262.5C102.3 248.9 94 226 96.8 226C97.3 226 102.6 227.5 108.6 229.4C135.3 237.9 170.9 246.7 201.4 252.5C228.1 257.5 274.9 263.9 297 265.4C304.3 266 304.2 265.9 291.5 263.1C244.2 252.7 199.9 236.4 163.4 216C97.5 179.3 52.9 128.7 20.9 54.4C11.9 33.5 3.8 7 6.4 7C6.6 7 14.5 11.6 24.1 17.1C102.7 62.9 147.3 82.7 253 119C320.4 142.1 352.8 154.9 385.3 171.2C427 192 454 210.8 481 237.9C511.3 268.3 524.2 287.9 555.4 351.1C574.8 390.5 581.7 401.8 593.5 413.5C609.2 429.1 626.8 435.8 641.3 431.6C651.7 428.6 657.2 421.4 657.2 410.9C657.2 403.9 654.8 398.3 648.8 391.5C646.6 389 645 386.7 645.2 386.5C645.5 386.2 649.4 386.5 654.1 387.1C685.8 391 712.1 400.8 726.2 413.9C731.7 419 734.9 421.1 739 422.5C752.6 426.9 763.7 435.7 769 446.2C770.6 449.6 771.8 452.5 771.6 452.8C771.4 453 767.7 452.4 763.4 451.5C747.5 447.9 733.2 451.1 726.1 459.7C718.5 468.9 719.3 483.9 728.1 496.6C738.9 512.3 771.3 539 813.9 567C824.3 573.9 832.9 579.7 832.9 580C832.9 580.3 827.7 583.1 821.2 586.2C800.9 596.2 778.9 611 755.5 630.5C724.4 656.4 694.3 692.8 670.6 733C658.6 753.5 660 752.2 656.6 745.9ZM844 526.6C835.4 525.4 823.5 522.3 820.2 520.1C819.5 519.7 817.4 513.2 815.5 505.7C808.2 476.3 795.8 451 779.2 431.5C770.2 421 754.1 408.5 741 402C737.4 400.2 734.3 398.6 734.1 398.4C733.9 398.2 736.1 394.2 739 389.5C741.9 384.7 751.8 366.2 760.9 348.2C770.1 330.2 780.1 311.4 783 306.5C819.1 245.5 864.1 204.8 933.8 170.1C970 152 997.9 140.8 1062.5 118.5C1179.7 77.9 1218.9 60.4 1300.9 11.6C1306.1 8.5 1310.8 6 1311.2 6C1312.7 6 1312 10.1 1308.4 21.3C1294.9 63.1 1272.3 106.1 1247 138C1205.4 190.5 1142.3 229.5 1060.5 253.4C1049.8 256.6 1028 261.7 1017.7 263.6C1001.1 266.5 1043.4 262.6 1073.5 258.4C1119.6 252 1162.3 242.6 1205.6 229.6C1213.9 227.1 1221.1 225 1221.5 225C1223.6 225 1218.2 240.7 1211.4 254.2C1179 318.6 1115.3 361.7 1026.5 379.5C1017.1 381.4 1002.8 383.7 994.5 384.8L979.5 386.6L988.5 387.3C1023 390.1 1073.4 390 1103.6 387C1109.1 386.5 1113.8 386 1114.2 386C1117.9 385.9 1105.2 401.8 1090.2 416.1C1055.7 449.1 1018.1 463.8 961.1 466.6L946.8 467.3L959.1 471.2C971.2 474.9 993.7 480.2 1003.5 481.6C1006.2 481.9 1008.9 482.5 1009.4 482.8C1010.9 483.7 993.8 494.1 978.5 501.6C937.9 521.3 883 531.5 844 526.6Z";

export function LogoMark(props: IconProps) {
  return (
    <svg viewBox={`0 0 ${LOGO_VIEWBOX.w} ${LOGO_VIEWBOX.h}`} aria-hidden="true" {...props}>
      <path fill="#0067fd" fillRule="evenodd" d={LOGO_PATH} />
    </svg>
  );
}

export const ArrowRight = (p: IconProps) => (
  <Stroke {...p}>
    <path d="M5 12h14M13 6l6 6-6 6" />
  </Stroke>
);
export const ChevronDown = (p: IconProps) => (
  <Stroke {...p}>
    <path d="m6 9 6 6 6-6" />
  </Stroke>
);
export const ChevronLeft = (p: IconProps) => (
  <Stroke {...p}>
    <path d="m15 18-6-6 6-6" />
  </Stroke>
);
export const ChevronRight = (p: IconProps) => (
  <Stroke {...p}>
    <path d="m9 18 6-6-6-6" />
  </Stroke>
);
export const Download = (p: IconProps) => (
  <Stroke {...p}>
    <path d="M12 3v12M7 10l5 5 5-5M5 21h14" />
  </Stroke>
);
export const PlayCircle = (p: IconProps) => (
  <Stroke {...p}>
    <circle cx="12" cy="12" r="10" />
    <path d="m10 8 6 4-6 4V8Z" fill="currentColor" stroke="none" />
  </Stroke>
);
export const Check = (p: IconProps) => (
  <Stroke {...p}>
    <path d="M20 6 9 17l-5-5" />
  </Stroke>
);
export const Globe = (p: IconProps) => (
  <Stroke {...p}>
    <circle cx="12" cy="12" r="10" />
    <path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20" />
  </Stroke>
);
export const LogIn = (p: IconProps) => (
  <Stroke {...p}>
    <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3" />
  </Stroke>
);
export const LogOut = (p: IconProps) => (
  <Stroke {...p}>
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" />
  </Stroke>
);
export const Lock = (p: IconProps) => (
  <Stroke {...p}>
    <rect x="4" y="11" width="16" height="10" rx="2" />
    <path d="M8 11V7a4 4 0 0 1 8 0v4" />
  </Stroke>
);
export const Bookmark = (p: IconProps) => (
  <Stroke {...p}>
    <path d="M6 3h12v18l-6-4-6 4V3Z" />
  </Stroke>
);
export const MoreHorizontal = (p: IconProps) => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...p}>
    <circle cx="5" cy="12" r="2" />
    <circle cx="12" cy="12" r="2" />
    <circle cx="19" cy="12" r="2" />
  </svg>
);
export const Pencil = (p: IconProps) => (
  <Stroke {...p}>
    <path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" />
  </Stroke>
);
export const Trash = (p: IconProps) => (
  <Stroke {...p}>
    <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6M10 11v6M14 11v6" />
  </Stroke>
);
export const Search = (p: IconProps) => (
  <Stroke {...p}>
    <circle cx="11" cy="11" r="7" />
    <path d="m20 20-3.5-3.5" />
  </Stroke>
);
export const Settings = (p: IconProps) => (
  <Stroke {...p}>
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z" />
  </Stroke>
);
export const Trophy = (p: IconProps) => (
  <Stroke {...p}>
    <path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0V4Z" />
    <path d="M17 5h3v2a3 3 0 0 1-3 3M7 5H4v2a3 3 0 0 0 3 3" />
  </Stroke>
);
export const Medal = (p: IconProps) => (
  <Stroke {...p}>
    <circle cx="12" cy="15" r="6" />
    <path d="M8.5 10.2 5 3h4l3 6M15.5 10.2 19 3h-4l-3 6" />
    <path d="m12 12.5.9 1.8 2 .3-1.4 1.4.3 2-1.8-.9-1.8.9.3-2-1.4-1.4 2-.3.9-1.8Z" />
  </Stroke>
);
export const CalendarCheck = (p: IconProps) => (
  <Stroke {...p}>
    <rect x="3" y="5" width="18" height="16" rx="2" />
    <path d="M8 3v4M16 3v4M3 10h18M9 15.5l2 2 4-4" />
  </Stroke>
);
export const Clock = (p: IconProps) => (
  <Stroke {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v5l3 2" />
  </Stroke>
);
export const TrendingUp = (p: IconProps) => (
  <Stroke {...p}>
    <path d="M3 17 9 11l4 4 8-8M15 7h6v6" />
  </Stroke>
);
export const Play = (p: IconProps) => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...p}>
    <path d="M8 5.5v13a1 1 0 0 0 1.5.9l10.4-6.5a1 1 0 0 0 0-1.8L9.5 4.6A1 1 0 0 0 8 5.5Z" />
  </svg>
);
export const Menu = (p: IconProps) => (
  <Stroke {...p}>
    <path d="M4 6h16M4 12h16M4 18h16" />
  </Stroke>
);
export const Close = (p: IconProps) => (
  <Stroke {...p}>
    <path d="M18 6 6 18M6 6l12 12" />
  </Stroke>
);
export const Users = (p: IconProps) => (
  <Stroke {...p}>
    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
    <circle cx="9" cy="7" r="4" />
    <path d="M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8" />
  </Stroke>
);
export const ClipboardList = (p: IconProps) => (
  <Stroke {...p}>
    <rect x="5" y="4" width="14" height="18" rx="2" />
    <path d="M9 2h6v4H9zM9 11h6M9 15h6M9 19h3" />
  </Stroke>
);
export const Layers = (p: IconProps) => (
  <Stroke {...p}>
    <path d="m12 2 10 5-10 5L2 7l10-5Z" />
    <path d="m2 12 10 5 10-5M2 17l10 5 10-5" />
  </Stroke>
);
export const Percent = (p: IconProps) => (
  <Stroke {...p}>
    <path d="M19 5 5 19" />
    <circle cx="6.5" cy="6.5" r="2.5" />
    <circle cx="17.5" cy="17.5" r="2.5" />
  </Stroke>
);
export const ListChecks = (p: IconProps) => (
  <Stroke {...p}>
    <path d="m3 7 2 2 4-4M3 17l2 2 4-4M13 6h8M13 12h8M13 18h8" />
  </Stroke>
);
export const FileText = (p: IconProps) => (
  <Stroke {...p}>
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6Z" />
    <path d="M14 2v6h6M8 13h8M8 17h6" />
  </Stroke>
);
export const Sparkles = (p: IconProps) => (
  <Stroke {...p}>
    <path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9L12 3Z" />
    <path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15Z" />
  </Stroke>
);
export const GraduationCap = (p: IconProps) => (
  <Stroke {...p}>
    <path d="M22 10 12 5 2 10l10 5 10-5Z" />
    <path d="M6 12v5c0 1.5 2.7 3 6 3s6-1.5 6-3v-5M22 10v6" />
  </Stroke>
);
export const Target = (p: IconProps) => (
  <Stroke {...p}>
    <circle cx="12" cy="12" r="10" />
    <circle cx="12" cy="12" r="6" />
    <circle cx="12" cy="12" r="2" />
  </Stroke>
);
export const BarChart = (p: IconProps) => (
  <Stroke {...p}>
    <path d="M3 3v18h18" />
    <path d="M8 17v-5M13 17V8M18 17v-9" />
  </Stroke>
);
export const Timer = (p: IconProps) => (
  <Stroke {...p}>
    <circle cx="12" cy="13" r="8" />
    <path d="M12 9v4l2 2M10 2h4" />
  </Stroke>
);
export const Smartphone = (p: IconProps) => (
  <Stroke {...p}>
    <rect x="6" y="2" width="12" height="20" rx="2.5" />
    <path d="M11 18h2" />
  </Stroke>
);
export const UserPlus = (p: IconProps) => (
  <Stroke {...p}>
    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
    <circle cx="9" cy="7" r="4" />
    <path d="M19 8v6M22 11h-6" />
  </Stroke>
);
export const BookOpen = (p: IconProps) => (
  <Stroke {...p}>
    <path d="M2 4h6a4 4 0 0 1 4 4v13a3 3 0 0 0-3-3H2V4ZM22 4h-6a4 4 0 0 0-4 4v13a3 3 0 0 1 3-3h7V4Z" />
  </Stroke>
);
export const Rocket = (p: IconProps) => (
  <Stroke {...p}>
    <path d="M4.5 16.5c-1.5 1.3-2 5-2 5s3.7-.5 5-2c.7-.8.7-2.1-.1-2.9a2.2 2.2 0 0 0-2.9-.1Z" />
    <path d="M12 15l-3-3a22 22 0 0 1 2-4A12.9 12.9 0 0 1 22 2c0 2.7-.8 7.5-6 11a22 22 0 0 1-4 2Z" />
    <path d="M9 12H4s.6-3 2-4c1.6-1.1 5 0 5 0M12 15v5s3-.6 4-2c1.1-1.6 0-5 0-5" />
  </Stroke>
);
export const Star = (p: IconProps) => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...p}>
    <path d="m12 2 3.1 6.3 6.9 1-5 4.9 1.2 6.8L12 17.8 5.8 21l1.2-6.8-5-4.9 6.9-1L12 2Z" />
  </svg>
);
export const Quote = (p: IconProps) => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...p}>
    <path d="M9.5 6C6 7.2 4 9.9 4 13.6V18h6v-6H7.1c.2-2.1 1.3-3.6 3.3-4.4L9.5 6Zm10 0C16 7.2 14 9.9 14 13.6V18h6v-6h-2.9c.2-2.1 1.3-3.6 3.3-4.4L19.5 6Z" />
  </svg>
);
export const HelpCircle = (p: IconProps) => (
  <Stroke {...p}>
    <circle cx="12" cy="12" r="10" />
    <path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3M12 17h.01" />
  </Stroke>
);
export const Heart = (p: IconProps) => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...p}>
    <path d="M12 21s-7.5-4.6-10-9.5C.4 8.2 2.3 4 6.2 4c2.2 0 3.6 1.2 5.8 3.5C14.2 5.2 15.6 4 17.8 4c3.9 0 5.8 4.2 4.2 7.5C19.5 16.4 12 21 12 21Z" />
  </svg>
);
export const Gift = (p: IconProps) => (
  <Stroke {...p}>
    <rect x="3" y="8" width="18" height="4" rx="1" />
    <path d="M12 8v13M19 12v9H5v-9M7.5 8a2.5 2.5 0 0 1 0-5C11 3 12 8 12 8s1-5 4.5-5a2.5 2.5 0 0 1 0 5" />
  </Stroke>
);
export const Crown = (p: IconProps) => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...p}>
    <path d="M2 7l5 4 5-7 5 7 5-4-2 12H4L2 7Zm2 14h16v1.5H4V21Z" />
  </svg>
);
export const Gem = (p: IconProps) => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...p}>
    <path d="M6 3h12l4 6-10 12L2 9l4-6Z" />
  </svg>
);
export const Bell = (p: IconProps) => (
  <Stroke {...p}>
    <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9M10.3 21a1.9 1.9 0 0 0 3.4 0" />
  </Stroke>
);
export const Home = (p: IconProps) => (
  <Stroke {...p}>
    <path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1V10Z" />
  </Stroke>
);
export const UserIcon = (p: IconProps) => (
  <Stroke {...p}>
    <circle cx="12" cy="8" r="4" />
    <path d="M4 21a8 8 0 0 1 16 0" />
  </Stroke>
);
export const Flame = (p: IconProps) => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...p}>
    <path d="M12 2s5 4.5 5 10a5 5 0 0 1-10 0c0-2 1-3.5 1-3.5S9 11 11 11c0-4 1-9 1-9Zm0 20a7 7 0 0 1-7-7c0-1.5.4-2.9 1-4 .3 2.6 2 4 3.5 4.2C9 9.6 12 6 12 6s4 4 4 8a4 4 0 0 1 3-1.6c.6 1 1 2.2 1 3.6a8 8 0 0 1-8 6Z" opacity=".25" />
    <path d="M12 2s5 4.5 5 10a5 5 0 0 1-10 0c0-2 1-3.5 1-3.5S9 11 11 11c0-4 1-9 1-9Z" />
  </svg>
);

export const Telegram = (p: IconProps) => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...p}>
    <path d="M21.9 4.3 18.7 19.4c-.2 1.1-.9 1.3-1.8.8l-4.9-3.6-2.4 2.3c-.3.3-.5.5-1 .5l.4-5 9.1-8.2c.4-.4-.1-.5-.6-.2L6.2 13 1.4 11.5c-1-.3-1.1-1 .2-1.5l18.9-7.3c.9-.3 1.6.2 1.4 1.6Z" />
  </svg>
);
export const Instagram = (p: IconProps) => (
  <Stroke {...p}>
    <rect x="3" y="3" width="18" height="18" rx="5" />
    <circle cx="12" cy="12" r="4" />
    <path d="M17.5 6.5h.01" />
  </Stroke>
);
export const Youtube = (p: IconProps) => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...p}>
    <path d="M23 7.2a3 3 0 0 0-2.1-2.1C19 4.6 12 4.6 12 4.6s-7 0-8.9.5A3 3 0 0 0 1 7.2 31 31 0 0 0 .5 12a31 31 0 0 0 .5 4.8 3 3 0 0 0 2.1 2.1c1.9.5 8.9.5 8.9.5s7 0 8.9-.5a3 3 0 0 0 2.1-2.1 31 31 0 0 0 .5-4.8 31 31 0 0 0-.5-4.8ZM9.7 15.1V8.9l5.8 3.1-5.8 3.1Z" />
  </svg>
);

export const GooglePlayLogo = (p: IconProps) => (
  <svg viewBox="0 0 24 26" aria-hidden="true" {...p}>
    <path fill="#34A853" d="M1 1.2 13.4 13 1 24.8c-.4-.3-.6-.8-.6-1.4V2.6c0-.6.2-1.1.6-1.4Z" />
    <path fill="#FBBC04" d="m17.5 17.1-4.1-4.1 4.1-4.1 4.7 2.7c1.3.8 1.3 2 0 2.8l-4.7 2.7Z" />
    <path fill="#EA4335" d="M17.5 17.1 13.4 13 1 24.8c.5.4 1.2.5 2 .1l14.5-7.8Z" />
    <path fill="#4285F4" d="M17.5 8.9 3 1.1C2.2.7 1.5.8 1 1.2L13.4 13l4.1-4.1Z" />
  </svg>
);
export const AppleLogo = (p: IconProps) => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...p}>
    <path d="M16.4 12.6c0-2.6 2.1-3.8 2.2-3.9-1.2-1.8-3.1-2-3.7-2-1.6-.2-3.1.9-3.9.9-.8 0-2-.9-3.4-.9-1.7 0-3.3 1-4.2 2.6-1.8 3.1-.5 7.7 1.3 10.2.9 1.2 1.9 2.6 3.2 2.6 1.3-.1 1.8-.8 3.3-.8 1.6 0 2 .8 3.4.8 1.4 0 2.3-1.3 3.1-2.5 1-1.4 1.4-2.8 1.4-2.9 0 0-2.7-1-2.7-4.1ZM13.9 4.9c.7-.9 1.2-2 1-3.2-1 0-2.3.7-3 1.6-.7.7-1.2 1.9-1.1 3.1 1.2.1 2.3-.6 3.1-1.5Z" />
  </svg>
);
