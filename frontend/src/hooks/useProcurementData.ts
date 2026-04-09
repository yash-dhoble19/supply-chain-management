import { useCallback, useEffect, useMemo, useState } from "react";
import { procurementService } from "../services/procurementService";
import type {
  ProcurementInsight,
  ProcurementSummary,
  PurchaseOrder,
  SpendOptimization,
  SupplierOverview,
  SupplierRow,
  TopPerformer,
} from "../types/procurement.types";

interface ProcurementState {
  summary: ProcurementSummary | null;
  insights: ProcurementInsight[];
  supplierOverview: SupplierOverview | null;
  supplierRows: SupplierRow[];
  topPerformers: TopPerformer[];
  spendOptimization: SpendOptimization | null;
  purchaseOrders: PurchaseOrder[];
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

const initialState: ProcurementState = {
  summary: null,
  insights: [],
  supplierOverview: null,
  supplierRows: [],
  topPerformers: [],
  spendOptimization: null,
  purchaseOrders: [],
  isLoading: true,
  error: null,
  lastUpdated: null,
};

const PROCUREMENT_CACHE_TTL_MS = 30_000;

let procurementCache:
  | {
      data: Omit<ProcurementState, "isLoading" | "error">;
      cachedAt: number;
    }
  | null = null;

export function useProcurementData() {
  const [state, setState] = useState<ProcurementState>(initialState);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    const cached =
      procurementCache && Date.now() - procurementCache.cachedAt < PROCUREMENT_CACHE_TTL_MS
        ? procurementCache
        : null;

    if (cached) {
      setState({
        ...cached.data,
        isLoading: false,
        error: null,
      });
    }

    async function loadProcurementData() {
      setState((current) => ({
        ...current,
        isLoading: !cached,
        error: null,
      }));

      try {
        const response = await procurementService.getBootstrap(controller.signal);

        const nextState = {
          summary: response.summary,
          insights: response.insights,
          supplierOverview: response.supplierOverview,
          supplierRows: response.supplierRows,
          topPerformers: response.topPerformers,
          spendOptimization: response.spendOptimization,
          purchaseOrders: response.purchaseOrders,
          lastUpdated: new Date(),
        };

        procurementCache = {
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
          error: error instanceof Error ? error.message : "Unable to load procurement data.",
        }));
      }
    }

    void loadProcurementData();

    return () => controller.abort();
  }, [reloadToken]);

  const refetch = useCallback(() => setReloadToken((current) => current + 1), []);

  return useMemo(
    () => ({
      ...state,
      refetch,
    }),
    [refetch, state],
  );
}

// anything
