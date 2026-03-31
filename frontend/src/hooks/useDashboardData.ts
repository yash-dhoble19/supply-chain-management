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

const DASHBOARD_CACHE_TTL_MS = 30_000;

let dashboardCache:
  | {
      data: Omit<DashboardState, "isLoading" | "error">;
      cachedAt: number;
    }
  | null = null;

export function useDashboardData() {
  const [state, setState] = useState<DashboardState>(initialState);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    const cached = dashboardCache && Date.now() - dashboardCache.cachedAt < DASHBOARD_CACHE_TTL_MS ? dashboardCache : null;

    if (cached) {
      setState({
        ...cached.data,
        isLoading: false,
        error: null,
      });
    }

    async function loadDashboard() {
      setState((current) => ({
        ...current,
        isLoading: !cached,
        error: null,
      }));

      try {
        const response = await dashboardService.getBootstrap(controller.signal);

        const nextState = {
          metrics: response.metrics,
          shipments: response.shipments,
          activities: response.activities,
          stats: response.stats,
          overview: response.overview,
          lastUpdated: new Date(),
        };

        dashboardCache = {
          data: nextState,
          cachedAt: Date.now(),
        };

        setState({
          ...nextState,
          isLoading: false,
          error: null,
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
