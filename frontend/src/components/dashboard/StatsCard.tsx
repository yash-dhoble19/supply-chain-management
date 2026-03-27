import type { Stats } from "../../types/dashboard.types";

interface StatsCardProps {
  stat: Stats;
}

export function StatsCard({ stat }: StatsCardProps) {
  return (
    <article className="group flex items-center gap-6 rounded-xl bg-surface-container-lowest p-6 shadow-sm">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 transition-colors group-hover:bg-primary-fixed">
        <span className="material-symbols-outlined text-slate-600 transition-colors group-hover:text-primary">
          {stat.icon}
        </span>
      </div>
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-on-surface-variant">{stat.label}</p>
        <p className="text-2xl font-bold text-on-surface">{stat.value}</p>
        <p className="mt-1 text-xs font-medium text-on-secondary-container">{stat.description}</p>
      </div>
    </article>
  );
}
