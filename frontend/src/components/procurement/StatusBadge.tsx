interface StatusBadgeProps {
  label: string;
  tone: "urgent" | "high" | "monitor" | "partner" | "vetted" | "risk" | "info";
}

const toneClasses: Record<StatusBadgeProps["tone"], string> = {
  urgent: "bg-red-100 text-red-700",
  high: "bg-blue-100 text-blue-700",
  monitor: "bg-amber-100 text-amber-700",
  partner: "bg-emerald-100 text-emerald-700",
  vetted: "bg-blue-100 text-blue-700",
  risk: "bg-red-100 text-red-700",
  info: "bg-slate-100 text-slate-700",
};

export function StatusBadge({ label, tone }: StatusBadgeProps) {
  return (
    <span className={`inline-flex rounded-md px-2 py-1 text-[10px] font-bold uppercase tracking-[0.16em] ${toneClasses[tone]}`}>
      {label}
    </span>
  );
}
