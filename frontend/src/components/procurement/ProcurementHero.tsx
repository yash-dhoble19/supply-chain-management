import type { ProcurementSummary } from "../../types/procurement.types";
import { formatCurrency } from "../../utils/procurement";
import { SummaryMiniCard } from "./SummaryMiniCard";

interface ProcurementHeroProps {
  summary: ProcurementSummary;
}

const statusTone = {
  optimal: "bg-emerald-400 text-on-primary-fixed",
  warning: "bg-amber-300 text-slate-900",
  critical: "bg-red-300 text-slate-900",
};

export function ProcurementHero({ summary }: ProcurementHeroProps) {
  const leadDays = summary.leadTimeAverage;

  return (
    <section className="relative overflow-hidden rounded-[1.5rem] bg-[linear-gradient(135deg,#1f58cf_0%,#7d2d00_100%)] p-8 text-white shadow-xl">
      <div className="pointer-events-none absolute inset-y-0 right-0 w-1/3 bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.14),transparent_60%)] opacity-60" />
      <div className="relative z-10 grid grid-cols-1 gap-8 md:grid-cols-12 md:items-center">
        <div className="md:col-span-4 md:border-r md:border-white/10 md:pr-8">
          <div className="mb-4 flex items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-white/20 text-3xl font-bold backdrop-blur">
              {summary.systemHealthScore}
            </div>
            <div>
              <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.18em] ${statusTone[summary.healthStatus]}`}>
                {summary.healthStatus}
              </span>
              <h3 className="mt-2 text-2xl font-bold leading-tight">System Health</h3>
            </div>
          </div>
          <p className="max-w-md text-lg leading-9 text-white/88">{summary.aiBriefing}</p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 md:col-span-8">
          <SummaryMiniCard
            title="Critical Items"
            value={String(summary.criticalItems)}
            progress={Math.min(summary.criticalItems * 8, 100)}
            progressTone="red"
          />
          <SummaryMiniCard
            title="Pending POs"
            value={String(summary.pendingPOs)}
            progress={Math.min(summary.pendingPOs * 4, 100)}
            progressTone="blue"
          />
          <SummaryMiniCard
            title="Savings To Date"
            value={formatCurrency(summary.savingsToDate)}
            caption={summary.savingsChange}
          />
          <SummaryMiniCard
            title="Lead Time Avg"
            value={leadDays}
            caption={summary.leadTimeChange}
          />
        </div>
      </div>
    </section>
  );
}

// anything
