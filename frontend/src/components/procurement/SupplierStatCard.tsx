interface SupplierStatCardProps {
  label: string;
  value: string;
}

export function SupplierStatCard({ label, value }: SupplierStatCardProps) {
  return (
    <div className="rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-5 shadow-sm">
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-on-secondary-container">{label}</p>
      <p className="mt-2 text-3xl font-bold text-on-surface">{value}</p>
    </div>
  );
}
