import type { Shipment, ShipmentTone } from "../../types/dashboard.types";
import { formatEta } from "../../utils/formatters";

const statusStyles: Record<
  ShipmentTone,
  {
    pill: string;
    progress: string;
    progressText: string;
    detailIcon: string;
  }
> = {
  primary: {
    pill: "bg-blue-100 text-blue-700",
    progress: "bg-primary",
    progressText: "text-primary",
    detailIcon: "text-on-surface-variant",
  },
  warning: {
    pill: "bg-amber-100 text-amber-700",
    progress: "bg-tertiary",
    progressText: "text-tertiary",
    detailIcon: "text-tertiary",
  },
  success: {
    pill: "bg-green-100 text-green-700",
    progress: "bg-success",
    progressText: "text-success",
    detailIcon: "text-success",
  },
  neutral: {
    pill: "bg-slate-100 text-slate-700",
    progress: "bg-slate-400",
    progressText: "text-slate-600",
    detailIcon: "text-on-surface-variant",
  },
};

interface ShipmentCardProps {
  shipment: Shipment;
}

export function ShipmentCard({ shipment }: ShipmentCardProps) {
  const style = statusStyles[shipment.tone];

  return (
    <article className="rounded-xl border border-outline-variant/20 bg-surface-container-low p-4 shadow-sm transition-all hover:border-primary/50">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-on-surface-variant">
            Tracking ID: #{shipment.trackingNumber}
          </p>
          <p className="mt-1 text-sm font-bold leading-6 text-on-surface sm:text-base">
            {shipment.source} to {shipment.destination}
          </p>
        </div>
        <span className={`shrink-0 rounded-full px-2.5 py-1 text-[10px] font-bold uppercase ${style.pill}`}>
          {shipment.status}
        </span>
      </div>

      <div className="space-y-2.5">
        <div className="flex items-end justify-between text-[11px] font-semibold">
          <span className="text-on-surface-variant">Progress</span>
          <span className={style.progressText}>{shipment.progress}%</span>
        </div>

        <div className="h-2 w-full overflow-hidden rounded-full bg-surface-container-high">
          <div className={`h-full rounded-full ${style.progress}`} style={{ width: `${shipment.progress}%` }} />
        </div>

        <div className="flex items-center justify-between gap-4 pt-1">
          <div className="min-w-0 flex items-center gap-1.5">
            <span className={`material-symbols-outlined text-base ${style.detailIcon}`}>
              {shipment.tone === "warning" ? "warning" : shipment.tone === "success" ? "check_circle" : "schedule"}
            </span>
            <span className="truncate text-xs font-medium text-on-surface-variant">
              {shipment.tone === "warning" ? shipment.detail : formatEta(shipment.eta)}
            </span>
          </div>
          <span className="shrink-0 text-[10px] font-bold text-primary">View Details</span>
        </div>
      </div>
    </article>
  );
}

// anything
