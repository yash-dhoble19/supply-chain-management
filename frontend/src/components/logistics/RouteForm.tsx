import type { ChangeEvent } from "react";
import { LOGISTICS_LOAD_TYPES } from "../../types/logistics.types";
import type { ShipmentPlannerForm } from "../../types/logistics.types";

interface RouteFormProps {
  form: ShipmentPlannerForm;
  onChange: (field: keyof ShipmentPlannerForm, value: string) => void;
  onPlan: () => void;
  onCreate: () => void;
  isPlanning: boolean;
  isCreating: boolean;
  canCreate: boolean;
}

const inputClassName =
  "w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-100";

export function RouteForm({
  form,
  onChange,
  onPlan,
  onCreate,
  isPlanning,
  isCreating,
  canCreate,
}: RouteFormProps) {
  const handleInputChange =
    (field: keyof ShipmentPlannerForm) => (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      onChange(field, event.target.value);
    };

  return (
    <section className="rounded-[28px] border border-slate-200/70 bg-white/95 p-6 shadow-[0_20px_50px_rgba(15,23,42,0.08)]">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-l font-bold uppercase tracking-[0.24em] text-sky-600">Route Planner</p>
          <h3 className="mt-2 text-2xl font-bold tracking-tight text-slate-950">Create a live shipment</h3>
          <p className="mt-2 max-w-2xl text-sm text-slate-600">
            Enter the origin, destination and load type. Distance, ETA, and fuel estimates come
            from real route geometry before a shipment is saved.
          </p>
        </div>
      </div>

      <div className="mt-6 grid gap-4 xl:grid-cols-2">
        <label className="block">
          <span className="mb-2 block text-sm font-semibold text-slate-800">Origin</span>
          <input
            value={form.origin}
            onChange={handleInputChange("origin")}
            className={inputClassName}
            placeholder="Warehouse or pickup address"
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-semibold text-slate-800">Destination</span>
          <input
            value={form.destination}
            onChange={handleInputChange("destination")}
            className={inputClassName}
            placeholder="Delivery address"
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-semibold text-slate-800">Load type</span>
          <select value={form.loadType} onChange={handleInputChange("loadType")} className={inputClassName}>
            {LOGISTICS_LOAD_TYPES.map((loadType) => (
              <option key={loadType} value={loadType}>
                {loadType}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="mt-6 flex flex-col gap-3 sm:flex-row">
        <button
          type="button"
          onClick={onPlan}
          disabled={isPlanning}
          className="inline-flex items-center justify-center rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isPlanning ? "Calculating route..." : "Plan route"}
        </button>
        <button
          type="button"
          onClick={onCreate}
          disabled={!canCreate || isCreating}
          className="inline-flex items-center justify-center rounded-full border border-sky-200 bg-sky-50 px-5 py-3 text-sm font-semibold text-sky-700 transition hover:bg-sky-100 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isCreating ? "Creating shipment..." : "Create shipment"}
        </button>
      </div>
    </section>
  );
}
