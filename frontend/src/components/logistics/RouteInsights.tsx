import type { LogisticsRoutePlan } from "../../types/logistics.types";

interface RouteInsightsProps {
  plan: LogisticsRoutePlan | null;
  error: string | null;
}

const metricStyles = [
  "from-sky-500/15 to-sky-100/80 text-sky-900",
  "from-emerald-500/15 to-emerald-100/80 text-emerald-900",
  "from-amber-500/15 to-amber-100/80 text-amber-900",
];

export function RouteInsights({ plan, error }: RouteInsightsProps) {
  if (error) {
    return (
      <section className="rounded-[28px] border border-red-200 bg-red-50 p-6 text-sm text-red-700 shadow-sm">
        {error}
      </section>
    );
  }

  if (!plan) {
    return (
      <section className="rounded-[28px] border border-dashed border-slate-300 bg-white/70 p-6 shadow-sm">
        <p className="text-sm font-semibold text-slate-900">Route metrics will appear here.</p>
        <p className="mt-2 text-sm text-slate-600">
          Plan a route to calculate the actual road distance, ETA, and fuel estimate before creating the shipment.
        </p>
      </section>
    );
  }

  const metrics = [
    { label: "Distance", value: `${plan.distance_km.toFixed(2)} km` },
    { label: "ETA", value: `${plan.eta_hours.toFixed(2)} hrs` },
    { label: "Fuel", value: `${plan.fuel_liters.toFixed(2)} L` },
  ];

  return (
    <section className="rounded-[28px] border border-slate-200/70 bg-white/95 p-6 shadow-[0_20px_50px_rgba(15,23,42,0.08)]">
      <div className="flex flex-col gap-2">
        <p className="text-xs font-bold uppercase tracking-[0.24em] text-sky-600">Dynamic estimates</p>
        <h3 className="text-xl font-bold text-slate-950">
          {plan.origin} to {plan.destination}
        </h3>
        <p className="text-sm text-slate-600">
          Based on the current road route and the <span className="font-semibold text-slate-900">{plan.load_type}</span>{" "}
          transport profile.
        </p>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-3">
        {metrics.map((metric, index) => (
          <article
            key={metric.label}
            className={`rounded-3xl bg-gradient-to-br ${metricStyles[index]} p-5 shadow-sm`}
          >
            <p className="text-xs font-bold uppercase tracking-[0.2em] opacity-70">{metric.label}</p>
            <p className="mt-4 text-3xl font-bold tracking-tight">{metric.value}</p>
          </article>
        ))}
      </div>

      <div className="mt-6 grid gap-4 rounded-3xl bg-slate-950 px-5 py-4 text-sm text-slate-200 md:grid-cols-2">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-400">Average speed</p>
          <p className="mt-2 text-lg font-semibold text-white">{plan.average_speed_kmh.toFixed(2)} km/h</p>
        </div>
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-400">Fuel consumption</p>
          <p className="mt-2 text-lg font-semibold text-white">
            {plan.fuel_consumption_rate.toFixed(3)} liters per km
          </p>
        </div>
      </div>
    </section>
  );
}
