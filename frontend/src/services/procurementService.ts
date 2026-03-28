import { apiGet } from "./api";
import type {
  ProcurementInsight,
  ProcurementSummary,
  PurchaseOrder,
  SpendOptimization,
  SupplierOverviewResponse,
  TopPerformer,
} from "../types/procurement.types";

interface PurchaseOrderQueryOptions {
  limit?: number;
  page?: number;
  status?: string;
  priority?: string;
  supplier?: string;
  search?: string;
  dateRange?: string;
  startDate?: string;
  endDate?: string;
  sort?: "latest" | "oldest";
}

export const procurementService = {
  getSummary: (signal?: AbortSignal) => apiGet<ProcurementSummary>("/api/procurement/summary", signal),
  getInsights: (signal?: AbortSignal) => apiGet<ProcurementInsight[]>("/api/procurement/insights", signal),
  getSuppliersOverview: (signal?: AbortSignal) =>
    apiGet<SupplierOverviewResponse>("/api/procurement/suppliers/overview", signal),
  getTopPerformers: (signal?: AbortSignal) =>
    apiGet<TopPerformer[]>("/api/procurement/suppliers/top-performers", signal),
  getSpendOptimization: (signal?: AbortSignal) =>
    apiGet<SpendOptimization>("/api/procurement/spend-optimization", signal),
  getPurchaseOrders: (options?: PurchaseOrderQueryOptions, signal?: AbortSignal) => {
    const searchParams = new URLSearchParams();
    if (options?.limit) {
      searchParams.set("limit", String(options.limit));
    }
    if (options?.page) {
      searchParams.set("page", String(options.page));
    }
    if (options?.status) {
      searchParams.set("status", options.status);
    }
    if (options?.priority) {
      searchParams.set("priority", options.priority);
    }
    if (options?.supplier) {
      searchParams.set("supplier", options.supplier);
    }
    if (options?.search) {
      searchParams.set("search", options.search);
    }
    if (options?.dateRange) {
      searchParams.set("date_range", options.dateRange);
    }
    if (options?.startDate) {
      searchParams.set("start_date", options.startDate);
    }
    if (options?.endDate) {
      searchParams.set("end_date", options.endDate);
    }
    if (options?.sort) {
      searchParams.set("sort", options.sort);
    }
    const query = searchParams.toString();
    return apiGet<PurchaseOrder[]>(`/api/procurement/purchase-orders${query ? `?${query}` : ""}`, signal);
  },
};
