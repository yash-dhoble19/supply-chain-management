import type { ProcurementInsight } from "../../types/procurement.types";
import { formatCurrency } from "../../utils/procurement";
import { QuickPOButton } from "./QuickPOButton";
import { StatusBadge } from "./StatusBadge";

interface InsightCardProps {
  insight: ProcurementInsight;
  onQuickPO?: (insight: ProcurementInsight) => void;
  isCreatingPurchaseOrder?: boolean;
}

const priorityTone = {
  urgent: "border-red-500",
  high: "border-primary",
  monitor: "border-tertiary",
  normal: "border-slate-300",
};

export function InsightCard({
  insight,
  onQuickPO,
  isCreatingPurchaseOrder = false,
}: InsightCardProps) {
  const badgeTone = insight.priority === "urgent" ? "urgent" : insight.priority === "high" ? "high" : "monitor";
  const actionIcon = insight.actionType === "draft_email" ? "mail" : "receipt_long";

  return (
    <article className={`space-y-5 rounded-xl border-l-4 bg-surface-container-lowest p-6 shadow-sm ${priorityTone[insight.priority]}`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-on-secondary-container">
            SKU: {insight.sku}
          </p>
          <h4 className="mt-2 text-2xl font-bold leading-tight text-on-surface">{insight.title}</h4>
        </div>
        <StatusBadge label={insight.priority} tone={badgeTone} />
      </div>

      <div className="rounded-xl bg-surface-container-low p-4">
        <div className="mb-2 flex items-center gap-2">
          <span className="material-symbols-outlined text-sm text-primary">psychology</span>
          <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-primary">AI Reasoning</p>
        </div>
        <p className="text-sm leading-7 text-on-surface-variant">{insight.reasoning}</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">Unit Price</p>
          <p className="text-lg font-bold text-on-surface">{formatCurrency(insight.unitPrice)}</p>
        </div>
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">Supplier Score</p>
          <p className="text-lg font-bold text-on-surface">{insight.supplierScore}/100</p>
        </div>
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">Est. Lead Time</p>
          <p className="text-lg font-bold text-on-surface">{insight.estimatedLeadTime}</p>
        </div>
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">Replen. Qty</p>
          <p className="text-lg font-bold text-on-surface">{insight.replenishmentQty.toLocaleString()} units</p>
        </div>
      </div>

      <div className="flex gap-2 pt-2">
        {insight.actionType === "quick_po" ? (
          <QuickPOButton onClick={() => onQuickPO?.(insight)} isLoading={isCreatingPurchaseOrder} />
        ) : (
          <button className="flex-1 rounded-lg bg-surface-container-high py-2.5 text-xs font-bold text-on-surface shadow-sm transition hover:bg-surface-container">
            {insight.actionLabel}
          </button>
        )}
        <button className="rounded-lg bg-surface-container-high px-3 py-2.5 text-on-surface transition hover:bg-surface-container">
          <span className="material-symbols-outlined text-sm">{actionIcon}</span>
        </button>
      </div>
    </article>
  );
}

// anything
