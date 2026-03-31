import type { Shipment } from "../../types/logistics.types";

interface ShipmentCardProps {
  shipment: Shipment;
  onTrack: (shipment: Shipment) => void;
  onStart: (shipment: Shipment) => void;
  isStarting: boolean;
  isActive: boolean;
}

const statusStyles: Record<Shipment["status"], string> = {
  CREATED: "bg-slate-200 text-slate-700",
  IN_TRANSIT: "bg-emerald-100 text-emerald-700",
  DELIVERED: "bg-sky-100 text-sky-700",
};

function formatEta(eta: string | null) {
  if (!eta) return "Pending";
  return new Date(eta).toLocaleString();
}

export function ShipmentCard({ shipment, onTrack, onStart, isStarting, isActive }: ShipmentCardProps) {
  return (
    <article
      className={`rounded-[28px] border p-5 shadow-sm transition ${
        isActive ? "border-sky-300 bg-sky-50/80" : "border-slate-200 bg-white/95"
      }`}
    >
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.24em] text-slate-500">{shipment.trackingId}</p>
            <h3 className="mt-2 text-lg font-bold text-slate-950">
              {shipment.origin} to {shipment.destination}
            </h3>
            <p className="mt-1 text-sm text-slate-600">{shipment.loadType} load profile</p>
          </div>
          <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${statusStyles[shipment.status]}`}>
            {shipment.status.replace("_", " ")}
          </span>
        </div>

        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-2xl bg-slate-100 px-4 py-3">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">Distance</p>
            <p className="mt-2 text-xl font-bold text-slate-900">{shipment.distanceKm.toFixed(2)} km</p>
          </div>
          <div className="rounded-2xl bg-slate-100 px-4 py-3">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">ETA</p>
            <p className="mt-2 text-sm font-semibold text-slate-900">{formatEta(shipment.eta)}</p>
          </div>
          <div className="rounded-2xl bg-slate-100 px-4 py-3">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">Fuel</p>
            <p className="mt-2 text-xl font-bold text-slate-900">{shipment.fuelLiters.toFixed(2)} L</p>
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
            <span>Progress</span>
            <span>{shipment.progress.toFixed(1)}%</span>
          </div>
          <div className="mt-2 h-3 rounded-full bg-slate-200">
            <div
              className="h-3 rounded-full bg-gradient-to-r from-sky-500 to-emerald-500 transition-all"
              style={{ width: `${Math.max(2, shipment.progress)}%` }}
            />
          </div>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <button
            type="button"
            onClick={() => onTrack(shipment)}
            disabled={shipment.status !== "IN_TRANSIT"}
            className="inline-flex items-center justify-center rounded-full bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-500"
          >
            Track live
          </button>
          <button
            type="button"
            onClick={() => onStart(shipment)}
            disabled={shipment.status !== "CREATED" || isStarting}
            className="inline-flex items-center justify-center rounded-full border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400"
          >
            {isStarting ? "Starting..." : shipment.status === "CREATED" ? "Start shipment" : "Shipment running"}
          </button>
        </div>
      </div>
    </article>
  );
}
