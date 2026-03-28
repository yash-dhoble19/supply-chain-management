import { useEffect, useState } from "react";
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

export function useProcurementData() {
  const [state, setState] = useState<ProcurementState>(initialState);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function loadProcurementData() {
      setState((current) => ({
        ...current,
        isLoading: true,
        error: null,
      }));

      try {
        const [summary, insights, supplierResponse, topPerformers, spendOptimization, purchaseOrders] =
          await Promise.all([
            procurementService.getSummary(controller.signal),
            procurementService.getInsights(controller.signal),
            procurementService.getSuppliersOverview(controller.signal),
            procurementService.getTopPerformers(controller.signal),
            procurementService.getSpendOptimization(controller.signal),
            procurementService.getPurchaseOrders({ limit: 4 }, controller.signal),
          ]);

        setState({
          summary,
          insights,
          supplierOverview: supplierResponse.overview,
          supplierRows: supplierResponse.suppliers,
          topPerformers,
          spendOptimization,
          purchaseOrders,
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
          error: error instanceof Error ? error.message : "Unable to load procurement data.",
        }));
      }
    }

    void loadProcurementData();

    return () => controller.abort();
  }, [reloadToken]);

  return {
    ...state,
    refetch: () => setReloadToken((current) => current + 1),
  };
}
