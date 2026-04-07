import type { SupplierManagementFilters } from "../../types/procurement.types";

interface SupplierFilterState {
  supplierType: string;
  status: string;
  productCategory: string;
  location: string;
  performanceTier: string;
  deliveryReliabilityRange: string;
  sort: "highest_score" | "most_orders" | "lowest_price" | "fastest_delivery" | "recently_added";
}

interface SupplierFilterBarProps {
  searchTerm: string;
  onSearchChange: (value: string) => void;
  filters: SupplierManagementFilters | null;
  values: SupplierFilterState;
  onChange: (next: Partial<SupplierFilterState>) => void;
  onReset: () => void;
}

function SelectField({
  label,
  value,
  options,
  onChange,
  labels,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
  labels?: Record<string, string>;
}) {
  return (
    <label className="space-y-2">
      <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-on-secondary-container">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-11 w-full rounded-xl border border-outline-variant/20 bg-white px-3 text-sm text-on-surface outline-none transition focus:border-primary/40 focus:ring-2 focus:ring-primary/10"
      >
        <option value="all">All</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {labels?.[option] ?? option}
          </option>
        ))}
      </select>
    </label>
  );
}

export function SupplierFilterBar({
  searchTerm,
  onSearchChange,
  filters,
  values,
  onChange,
  onReset,
}: SupplierFilterBarProps) {
  const reliabilityLabels: Record<string, string> = {
    "95-100": "95-100%",
    "90-94": "90-94%",
    "80-89": "80-89%",
    "0-79": "Below 80%",
  };

  const sortLabels: Record<string, string> = {
    highest_score: "Highest Score",
    most_orders: "Most Orders",
    lowest_price: "Lowest Price",
    fastest_delivery: "Fastest Delivery",
    recently_added: "Recently Added",
  };

  return (
    <section className="rounded-[1.5rem] border border-outline-variant/15 bg-surface-container-lowest p-5 shadow-sm">
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.4fr)_repeat(3,minmax(0,1fr))]">
        <label className="space-y-2 xl:col-span-1">
          <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-on-secondary-container">
            Search Supplier Directory
          </span>
          <div className="flex h-11 items-center gap-3 rounded-xl border border-outline-variant/20 bg-white px-3 transition focus-within:border-primary/40 focus-within:ring-2 focus-within:ring-primary/10">
            <span className="material-symbols-outlined text-lg text-primary">search</span>
            <input
              type="text"
              value={searchTerm}
              onChange={(event) => onSearchChange(event.target.value)}
              placeholder="Name, email, phone, product, or location"
              className="w-full bg-transparent text-sm text-on-surface outline-none placeholder:text-on-surface-variant"
            />
          </div>
        </label>

        <SelectField
          label="Supplier Type"
          value={values.supplierType}
          options={filters?.supplier_types ?? []}
          onChange={(supplierType) => onChange({ supplierType })}
        />
        <SelectField
          label="Status"
          value={values.status}
          options={filters?.statuses ?? []}
          onChange={(status) => onChange({ status })}
        />
        <SelectField
          label="Product Category"
          value={values.productCategory}
          options={filters?.product_categories ?? []}
          onChange={(productCategory) => onChange({ productCategory })}
        />
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[repeat(4,minmax(0,1fr))_auto]">
        <SelectField
          label="Location"
          value={values.location}
          options={filters?.locations ?? []}
          onChange={(location) => onChange({ location })}
        />
        <SelectField
          label="Performance Tier"
          value={values.performanceTier}
          options={filters?.performance_tiers ?? []}
          onChange={(performanceTier) => onChange({ performanceTier })}
        />
        <SelectField
          label="Delivery Reliability"
          value={values.deliveryReliabilityRange}
          options={filters?.delivery_reliability_ranges ?? []}
          labels={reliabilityLabels}
          onChange={(deliveryReliabilityRange) => onChange({ deliveryReliabilityRange })}
        />
        <SelectField
          label="Sort"
          value={values.sort}
          options={[
            "highest_score",
            "most_orders",
            "lowest_price",
            "fastest_delivery",
            "recently_added",
          ]}
          labels={sortLabels}
          onChange={(sort) =>
            onChange({
              sort: sort as SupplierFilterState["sort"],
            })
          }
        />

        <div className="flex items-end">
          <button
            type="button"
            onClick={onReset}
            className="inline-flex h-11 items-center justify-center rounded-xl border border-outline-variant/20 bg-white px-4 text-sm font-semibold text-on-surface transition hover:border-primary/20 hover:bg-surface-container-low"
          >
            Reset Filters
          </button>
        </div>
      </div>
    </section>
  );
}
