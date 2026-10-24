import { ListChecks, Shield, Sparkles } from "lucide-react";

const POINTS = [
  {
    icon: Shield,
    title: "Role-based access",
    text: "Analyst, Supervisor, and Auditor permissions enforced by the server.",
  },
  {
    icon: ListChecks,
    title: "Every action audited",
    text: "Sign-ins, views, denials, and changes are recorded.",
  },
  {
    icon: Sparkles,
    title: "Evidence-cited AI copilot",
    text: "Every answer links to the source records it used.",
  },
];

export function LoginBrandPanel() {
  return (
    <aside className="brand-panel flex w-[620px] shrink-0 flex-col justify-between px-16 pt-[72px] pb-14 text-white">
      <div className="flex flex-col gap-9">
        <div className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-[10px] bg-white/15 font-bold">
            ◆
          </span>
          <span className="text-lg font-bold">OpenFraud Investigator</span>
        </div>
        <p className="text-[34px] leading-[1.2] font-bold">
          Trace the money.
          <br />
          Connect the evidence.
          <br />
          Investigate with AI.
        </p>
        <ul className="flex flex-col gap-4">
          {POINTS.map(({ icon: Icon, title, text }) => (
            <li key={title} className="flex gap-3.5">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[10px] bg-white/10">
                <Icon aria-hidden size={18} />
              </span>
              <span>
                <span className="block text-sm font-semibold">{title}</span>
                <span className="block text-xs text-white/75">{text}</span>
              </span>
            </li>
          ))}
        </ul>
      </div>
      <p className="text-[11px] text-white/60">
        Open source · MIT · Not production-ready · Makes no compliance claims
      </p>
    </aside>
  );
}
