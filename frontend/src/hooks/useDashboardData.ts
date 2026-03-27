import { useEffect, useState } from "react";
import { dashboardService } from "../services/dashboardService";
import type { Activity, DashboardOverview, Metric, Shipment, Stats } from "../types/dashboard.types";

interface DashboardState {
  metrics: Metric[];
  shipments: Shipment[];
  activities: Activity[];
  stats: Stats[];
  overview: DashboardOverview | null;
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

const initialState: DashboardState = {
  metrics: [],
  shipments: [],
  activities: [],
  stats: [],
  overview: null,
  isLoading: true,
  error: null,
  lastUpdated: null,
};

export function useDashboardData() {
  const [state, setState] = useState<DashboardState>(initialState);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function loadDashboard() {
      setState((current) => ({
        ...current,
        isLoading: true,
        error: null,
      }));

      try {
        const [metrics, shipments, activities, stats, overview] = await Promise.all([
          dashboardService.getMetrics(controller.signal),
          dashboardService.getShipments(controller.signal),
          dashboardService.getActivities(controller.signal),
          dashboardService.getStats(controller.signal),
          dashboardService.getOverview(controller.signal),
        ]);

        setState({
          metrics,
          shipments,
          activities,
          stats,
          overview,
          isLoading: false,
          error: null,
          lastUpdated: new Date(),
        });
      } catch (error) {
        if (controller.signal.aborted) {
          return;
        }

        setState((current) => ({
          ...current,
          isLoading: false,
          error: error instanceof Error ? error.message : "Unable to load dashboard data.",
        }));
      }
    }

    void loadDashboard();

    return () => controller.abort();
  }, [reloadToken]);

  return {
    ...state,
    refetch: () => setReloadToken((current) => current + 1),
  };
}
