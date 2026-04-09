import { apiGet } from "./api";
import type { Activity, DashboardOverview, Metric, Shipment, Stats } from "../types/dashboard.types";

export const dashboardService = {
  getBootstrap: (signal?: AbortSignal) =>
    apiGet<{
      metrics: Metric[];
      shipments: Shipment[];
      activities: Activity[];
      stats: Stats[];
      overview: DashboardOverview | null;
    }>("/api/dashboard/bootstrap", signal),
  getMetrics: (signal?: AbortSignal) => apiGet<Metric[]>("/api/dashboard/metrics", signal),
  getShipments: (signal?: AbortSignal) => apiGet<Shipment[]>("/api/dashboard/shipments", signal),
  getActivities: (signal?: AbortSignal) => apiGet<Activity[]>("/api/dashboard/activities", signal),
  getStats: (signal?: AbortSignal) => apiGet<Stats[]>("/api/dashboard/stats", signal),
  getOverview: (signal?: AbortSignal) => apiGet<DashboardOverview>("/api/dashboard/overview", signal),
};

// anything
