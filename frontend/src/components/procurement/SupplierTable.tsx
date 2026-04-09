import type { SupplierRow } from "../../types/procurement.types";
import { StatusBadge } from "./StatusBadge";

interface SupplierTableProps {
  rows: SupplierRow[];
}

function verdictTone(verdict: string) {
  if (verdict.toLowerCase().includes("partner")) {
    return "partner";
  }
  if (verdict.toLowerCase().includes("risk")) {
    return "risk";
  }
  return "vetted";
}

export function SupplierTable({ rows }: SupplierTableProps) {
  if (rows.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-outline-variant/40 bg-surface-container-low px-6 py-10 text-center shadow-sm">
        <p className="text-sm font-semibold text-on-surface">No supplier records match this search.</p>
        <p className="mt-1 text-sm text-on-surface-variant">
          Try a broader search to see supplier performance data.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl bg-surface-container-lowest shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead className="bg-surface-container-low">
            <tr>
              <th className="px-6 py-4 text-[11px] font-bold uppercase tracking-[0.18em] text-on-surface-variant">Supplier</th>
              <th className="px-6 py-4 text-[11px] font-bold uppercase tracking-[0.18em] text-on-surface-variant text-center">Verdict</th>
              <th className="px-6 py-4 text-[11px] font-bold uppercase tracking-[0.18em] text-on-surface-variant">Score</th>
              <th className="px-6 py-4 text-[11px] font-bold uppercase tracking-[0.18em] text-on-surface-variant">Reliability</th>
              <th className="px-6 py-4 text-[11px] font-bold uppercase tracking-[0.18em] text-on-surface-variant">On-time</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-outline-variant/10">
            {rows.map((row) => (
              <tr key={row.id} className="transition-colors hover:bg-surface-container-low">
                <td className="px-6 py-5">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded bg-slate-100 text-sm font-bold text-primary">
                      {row.name.slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <p className="text-sm font-bold text-on-surface">{row.name}</p>
                      <p className="text-[10px] text-slate-500">{row.location}</p>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-5 text-center">
                  <StatusBadge label={row.verdict} tone={verdictTone(row.verdict)} />
                </td>
                <td className="px-6 py-5 text-lg font-bold text-primary">{row.score}</td>
                <td className="px-6 py-5">
                  <div className="h-1.5 w-32 overflow-hidden rounded-full bg-surface-container-high">
                    <div className="h-full rounded-full bg-primary" style={{ width: `${row.reliability}%` }} />
                  </div>
                </td>
                <td className="px-6 py-5">
                  <div className="h-1.5 w-32 overflow-hidden rounded-full bg-surface-container-high">
                    <div className="h-full rounded-full bg-emerald-500" style={{ width: `${row.onTimeDelivery}%` }} />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// anything
