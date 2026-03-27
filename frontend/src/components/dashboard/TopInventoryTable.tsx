import type { TopInventoryItem } from "../../types/dashboard.types";

const statusClasses: Record<string, string> = {
  Healthy: "bg-green-100 text-green-700",
  Low: "bg-amber-100 text-amber-700",
  Critical: "bg-red-100 text-red-700",
};

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  notation: "compact",
  maximumFractionDigits: 1,
});

interface TopInventoryTableProps {
  items: TopInventoryItem[];
}

export function TopInventoryTable({ items }: TopInventoryTableProps) {
  return (
    <div className="overflow-hidden rounded-xl border border-outline-variant/10 bg-surface-container-low">
      <div className="grid grid-cols-[1.8fr_1fr_0.9fr_0.9fr] gap-3 border-b border-outline-variant/10 px-5 py-4 text-xs font-bold uppercase tracking-[0.18em] text-on-surface-variant">
        <span>Product</span>
        <span>Exposure</span>
        <span>Stock</span>
        <span>Status</span>
      </div>
      <div>
        {items.map((item) => (
          <div
            key={item.id}
            className="grid grid-cols-[1.8fr_1fr_0.9fr_0.9fr] gap-3 border-b border-outline-variant/10 px-5 py-4 last:border-b-0"
          >
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-on-surface">{item.name}</p>
              <p className="truncate text-xs text-on-surface-variant">
                {item.sku} • {item.category}
              </p>
            </div>
            <p className="text-sm font-bold text-on-surface">{currencyFormatter.format(item.value)}</p>
            <p className="text-sm font-semibold text-on-surface">{item.stock}</p>
            <div>
              <span className={`rounded-full px-2.5 py-1 text-[10px] font-bold ${statusClasses[item.status] || "bg-slate-100 text-slate-700"}`}>
                {item.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
