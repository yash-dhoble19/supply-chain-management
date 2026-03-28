import type { PurchaseOrder } from "../../types/procurement.types";
import { getPurchaseOrderStageIndex } from "../../utils/procurement";
import { StatusBadge } from "./StatusBadge";

const stages = ["Draft", "Approved", "In Transit", "Received"];

interface PurchaseOrderCardProps {
  order: PurchaseOrder;
  onViewDetails?: (orderId: string) => void;
}

function statusTone(status: string) {
  if (status.toLowerCase().includes("transit")) {
    return "high";
  }
  if (status.toLowerCase().includes("approved")) {
    return "monitor";
  }
  if (status.toLowerCase().includes("received")) {
    return "partner";
  }
  return "info";
}

function priorityTone(priority: string) {
  if (priority.toLowerCase().includes("critical")) {
    return "urgent";
  }
  if (priority.toLowerCase().includes("high")) {
    return "high";
  }
  return "monitor";
}

export function PurchaseOrderCard({ order, onViewDetails }: PurchaseOrderCardProps) {
  const activeStage = getPurchaseOrderStageIndex(order);

  return (
    <article className="rounded-xl bg-surface-container-lowest p-6 shadow-sm transition-shadow hover:shadow-md">
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12 lg:items-center">
        <div className="lg:col-span-3">
          <p className="mb-1 text-[10px] font-bold text-primary">#{order.poNumber}</p>
          <h5 className="text-2xl font-bold text-on-surface">{order.title}</h5>
          <p className="mt-1 text-sm text-on-surface-variant">{order.supplierName}</p>
        </div>

        <div className="space-y-3 lg:col-span-2">
          <StatusBadge label={order.status} tone={statusTone(order.status)} />
          <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-slate-500">
            Priority: <span className="text-on-surface">{order.priority}</span>
          </p>
          <StatusBadge label={order.priority} tone={priorityTone(order.priority)} />
        </div>

        <div className="space-y-3 lg:col-span-5">
          <div className="flex justify-between text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">
            {stages.map((stage) => (
              <span key={stage}>{stage}</span>
            ))}
          </div>
          <div className="flex items-center gap-1">
            {stages.map((stage, index) => {
              const isComplete = index <= activeStage;
              const isCurrent = index === activeStage;
              return (
                <div key={stage} className={`relative h-1.5 flex-1 rounded-full ${isComplete ? "bg-primary" : "bg-surface-container-high"}`}>
                  {isCurrent ? (
                    <div className="absolute -right-1 -top-1 h-3 w-3 rounded-full border-2 border-white bg-primary" />
                  ) : null}
                </div>
              );
            })}
          </div>
        </div>

        <div className="flex justify-end gap-2 lg:col-span-2">
          <button
            type="button"
            onClick={() => onViewDetails?.(order.id)}
            className="rounded-lg bg-surface-container-high px-4 py-2 text-xs font-bold text-on-surface transition hover:bg-surface-container"
          >
            View Details
          </button>
          <button className="flex h-10 w-10 items-center justify-center rounded-lg bg-surface-container-high text-slate-500 transition hover:bg-surface-container">
            <span className="material-symbols-outlined text-sm">more_vert</span>
          </button>
        </div>
      </div>
    </article>
  );
}
