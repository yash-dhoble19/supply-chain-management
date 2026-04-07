import type { OverviewSeriesItem } from "../../types/dashboard.types";

const toneClasses = {
  primary: "bg-primary",
  warning: "bg-tertiary",
  success: "bg-success",
  danger: "bg-error",
  neutral: "bg-slate-400",
};

interface BarListCardProps {
  title: string;
  items: OverviewSeriesItem[];
}

export function BarListCard({ title, items }: BarListCardProps) {
  const maxValue = items.length ? Math.max(...items.map((item) => item.value), 1) : 1;

  return (
    <div className="rounded-xl border border-outline-variant/10 bg-surface-container-low p-5">
      <h4 className="text-sm font-bold uppercase tracking-[0.18em] text-on-surface-variant">{title}</h4>
      <div className="mt-5 space-y-4">
        {items.map((item) => (
          <div key={item.id}>
            <div className="mb-2 flex items-center justify-between gap-3 text-sm">
              <span className="font-semibold text-on-surface">{item.label}</span>
              <span className="font-bold text-on-surface-variant">{item.value}</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-surface-container-high">
              <div
                className={`h-full rounded-full ${toneClasses[item.tone]}`}
                style={{ width: `${Math.max((item.value / maxValue) * 100, item.value > 0 ? 12 : 0)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
