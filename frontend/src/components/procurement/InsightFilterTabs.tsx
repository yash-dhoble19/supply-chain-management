import { getPriorityFilterLabel } from "../../utils/procurement";

type InsightFilter = "all" | "urgent" | "high";

interface InsightFilterTabsProps {
  activeFilter: InsightFilter;
  onChange: (filter: InsightFilter) => void;
}

const filters: InsightFilter[] = ["all", "urgent", "high"];

export function InsightFilterTabs({ activeFilter, onChange }: InsightFilterTabsProps) {
  return (
    <div className="flex rounded-lg bg-surface-container-high p-1">
      {filters.map((filter) => (
        <button
          key={filter}
          type="button"
          onClick={() => onChange(filter)}
          className={`rounded-md px-6 py-2 text-sm transition ${
            activeFilter === filter
              ? "bg-surface-container-lowest font-bold text-on-surface shadow-sm"
              : "font-medium text-on-surface-variant hover:text-on-surface"
          }`}
        >
          {getPriorityFilterLabel(filter)}
        </button>
      ))}
    </div>
  );
}
