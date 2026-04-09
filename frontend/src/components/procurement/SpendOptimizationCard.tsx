import type { SpendOptimization } from "../../types/procurement.types";
import { formatCurrency } from "../../utils/procurement";

interface SpendOptimizationCardProps {
  spendOptimization: SpendOptimization;
}

export function SpendOptimizationCard({ spendOptimization }: SpendOptimizationCardProps) {
  return (
    <div className="rounded-xl bg-[linear-gradient(180deg,#123a91_0%,#0d2f79_100%)] p-6 text-white shadow-lg">
      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-white/60">Total Spend Optimization</p>
      <h4 className="mt-3 text-4xl font-bold">
        {formatCurrency(spendOptimization.totalValue)}{" "}
        <span className="text-base font-medium text-emerald-300">{spendOptimization.yoyChange}</span>
      </h4>

      <div className="mt-6 space-y-2">
        <div className="flex justify-between text-[10px] font-bold uppercase tracking-[0.18em]">
          <span>Budget Utilization</span>
          <span>{spendOptimization.budgetUtilization}%</span>
        </div>
        <div className="h-2 w-full rounded-full bg-white/10">
          <div
            className="h-2 rounded-full bg-white"
            style={{ width: `${Math.min(spendOptimization.budgetUtilization, 100)}%` }}
          />
        </div>
      </div>

      <button className="mt-6 w-full rounded-lg bg-white py-2.5 text-xs font-bold text-slate-900 transition hover:bg-slate-100">
        {spendOptimization.buttonLabel}
      </button>
    </div>
  );
}

// anything
