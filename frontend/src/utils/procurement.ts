import type { ProcurementInsight, PurchaseOrder } from "../types/procurement.types";

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: value >= 1000 ? "compact" : "standard",
    maximumFractionDigits: 1,
  }).format(value);
}

export function getPriorityFilterLabel(filter: "all" | "urgent" | "high"): string {
  if (filter === "urgent") {
    return "Critical";
  }
  if (filter === "high") {
    return "High Priority";
  }
  return "All";
}

export function matchesProcurementQuery(
  query: string,
  values: Array<string | number | undefined | null>,
): boolean {
  if (!query.trim()) {
    return true;
  }

  const normalizedQuery = query.trim().toLowerCase();
  return values.some((value) => String(value ?? "").toLowerCase().includes(normalizedQuery));
}

export function filterInsights(
  insights: ProcurementInsight[],
  filter: "all" | "urgent" | "high",
): ProcurementInsight[] {
  if (filter === "all") {
    return insights;
  }
  return insights.filter((insight) => insight.priority === filter);
}

export function getPurchaseOrderStageIndex(order: PurchaseOrder): number {
  return ["draft", "approved", "in_transit", "received"].indexOf(order.lifecycleStage);
}
