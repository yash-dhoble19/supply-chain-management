import type { ExecutiveBrief } from "../../types/dashboard.types";

const toneClasses = {
  primary: "border-primary/20 bg-primary-fixed/40 text-on-primary-fixed",
  neutral: "border-slate-200 bg-slate-50 text-slate-700",
  success: "border-green-200 bg-green-50 text-green-800",
  warning: "border-amber-200 bg-amber-50 text-amber-800",
  danger: "border-red-200 bg-red-50 text-red-800",
};

interface ExecutiveBriefListProps {
  briefs: ExecutiveBrief[];
}

export function ExecutiveBriefList({ briefs }: ExecutiveBriefListProps) {
  return (
    <div className="space-y-4">
      {briefs.map((brief) => (
        <article key={brief.id} className={`rounded-xl border p-4 ${toneClasses[brief.tone]}`}>
          <h4 className="text-sm font-bold uppercase tracking-[0.18em]">{brief.title}</h4>
          <p className="mt-2 text-sm font-medium leading-6">{brief.description}</p>
        </article>
      ))}
    </div>
  );
}
