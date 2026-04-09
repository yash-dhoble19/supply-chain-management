import type { TopPerformer } from "../../types/procurement.types";

interface TopPerformerCardProps {
  performers: TopPerformer[];
}

export function TopPerformerCard({ performers }: TopPerformerCardProps) {
  return (
    <div className="space-y-4 rounded-xl bg-surface-container-lowest p-6 shadow-sm">
      <h4 className="flex items-center gap-2 text-base font-bold text-on-surface">
        <span className="material-symbols-outlined text-primary">emoji_events</span>
        Top Performers
      </h4>
      {performers.length === 0 ? (
        <div className="rounded-lg border border-dashed border-outline-variant/40 bg-surface-container-low px-4 py-8 text-center">
          <p className="text-sm font-semibold text-on-surface">No top performers found.</p>
          <p className="mt-1 text-sm text-on-surface-variant">
            Supplier rankings will appear here when matching data is available.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {performers.map((performer) => (
            <div key={performer.id} className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="text-xs font-bold text-slate-400">{String(performer.rank).padStart(2, "0")}</span>
                <div className="flex h-8 w-8 items-center justify-center rounded-full border border-primary/20 bg-primary-fixed text-xs font-bold text-primary">
                  {performer.name.slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <p className="text-xs font-bold text-on-surface">{performer.name}</p>
                  <p className="text-[10px] font-medium text-emerald-600">{performer.metricLabel}</p>
                </div>
              </div>
              <span className="rounded bg-primary-fixed px-2 py-0.5 text-xs font-bold text-on-primary-fixed">
                {performer.score}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// anything
