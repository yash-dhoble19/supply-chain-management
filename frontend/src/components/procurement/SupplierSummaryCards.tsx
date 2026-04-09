import type { SupplierManagementSummary } from "../../types/procurement.types";
import { formatSupplierCurrency } from "../../utils/suppliers";

interface SupplierSummaryCardsProps {
  summary: SupplierManagementSummary;
}

const cards = [
  {
    key: "total_suppliers",
    label: "Total Suppliers",
    description: "Network-wide supplier coverage",
    icon: "account_tree",
  },
  {
    key: "active_suppliers",
    label: "Active Suppliers",
    description: "Ready for live procurement flow",
    icon: "bolt",
  },
  {
    key: "preferred_suppliers",
    label: "Preferred Suppliers",
    description: "Strategic and vetted partners",
    icon: "workspace_premium",
  },
  {
    key: "avg_supplier_score",
    label: "Avg Supplier Score",
    description: "Blended performance and cost fit",
    icon: "speed",
  },
  {
    key: "total_purchase_orders",
    label: "Total Purchase Orders",
    description: "Order volume tied to supplier network",
    icon: "receipt_long",
  },
];

export function SupplierSummaryCards({ summary }: SupplierSummaryCardsProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
      {cards.map((card, index) => {
        const value =
          card.key === "avg_supplier_score"
            ? `${summary.avg_supplier_score}`
            : card.key === "total_purchase_orders"
              ? summary.total_purchase_orders.toLocaleString()
              : summary[card.key as keyof SupplierManagementSummary].toLocaleString();

        return (
          <article
            key={card.key}
            className={`rounded-[1.35rem] border border-white/70 p-5 shadow-sm ${
              index === 0
                ? "bg-[linear-gradient(135deg,#153b9e_0%,#2554c7_55%,#8cc5ff_100%)] text-white shadow-lg"
                : "bg-surface-container-lowest text-on-surface"
            }`}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p
                  className={`text-[11px] font-bold uppercase tracking-[0.22em] ${
                    index === 0 ? "text-white/70" : "text-on-secondary-container"
                  }`}
                >
                  {card.label}
                </p>
                <p className={`mt-3 text-3xl font-bold tracking-tight ${index === 0 ? "text-white" : "text-on-surface"}`}>
                  {value}
                </p>
              </div>
              <div
                className={`flex h-11 w-11 items-center justify-center rounded-2xl ${
                  index === 0 ? "bg-white/15 text-white" : "bg-primary-fixed text-primary"
                }`}
              >
                <span className="material-symbols-outlined text-[22px]">{card.icon}</span>
              </div>
            </div>
            <p className={`mt-4 text-sm leading-6 ${index === 0 ? "text-white/82" : "text-on-surface-variant"}`}>
              {card.description}
            </p>
            {card.key === "total_purchase_orders" ? (
              <p className="mt-3 text-xs font-semibold text-emerald-300">
                {formatSupplierCurrency(summary.total_spend)} linked spend
              </p>
            ) : null}
          </article>
        );
      })}
    </div>
  );
}

// anything
