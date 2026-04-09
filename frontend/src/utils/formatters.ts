import type { Activity, Metric } from "../types/dashboard.types";

const compactNumberFormatter = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 1,
});

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  notation: "compact",
  maximumFractionDigits: 1,
});

const dateTimeFormatter = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

export function formatMetricValue(metric: Metric): string {
  if (metric.format === "currency") {
    return currencyFormatter.format(metric.value);
  }

  if (metric.format === "percent") {
    return `${metric.value}%`;
  }

  return compactNumberFormatter.format(metric.value);
}

export function formatRelativeTime(timestamp: string): string {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return "Unknown";
  }

  const deltaMs = date.getTime() - Date.now();
  const minutes = Math.round(deltaMs / 60000);
  const absMinutes = Math.abs(minutes);

  if (absMinutes < 1) {
    return "Just now";
  }

  if (absMinutes < 60) {
    return `${absMinutes} min${absMinutes === 1 ? "" : "s"} ago`;
  }

  const hours = Math.round(absMinutes / 60);
  if (hours < 24) {
    return `${hours} hr${hours === 1 ? "" : "s"} ago`;
  }

  const days = Math.round(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}

export function formatEta(timestamp?: string | null): string {
  if (!timestamp) {
    return "ETA pending";
  }

  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return "ETA pending";
  }

  return `ETA: ${dateTimeFormatter.format(date)}`;
}

export function formatLastUpdated(lastUpdated: Date | null): string {
  if (!lastUpdated) {
    return "Loading";
  }

  return formatRelativeTime(lastUpdated.toISOString());
}

export function matchesDashboardQuery(query: string, values: Array<string | undefined | null>): boolean {
  if (!query.trim()) {
    return true;
  }

  const normalizedQuery = query.trim().toLowerCase();
  return values.some((value) => value?.toLowerCase().includes(normalizedQuery));
}

export function getActivityAriaLabel(activity: Activity): string {
  return `${activity.title}. ${activity.description}. ${formatRelativeTime(activity.timestamp)}.`;
}

// anything
