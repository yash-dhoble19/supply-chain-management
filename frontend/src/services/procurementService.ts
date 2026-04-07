import { apiDelete, apiGet, apiPost, apiPut } from "./api";
import type {
  ProcurementInsight,
  ProcurementSummary,
  PurchaseOrder,
  SpendOptimization,
  SupplierManagementDetail,
  SupplierManagementListResponse,
  SupplierMutationResponse,
  SupplierOverviewResponse,
  SupplierUpsertPayload,
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

interface SupplierQueryOptions {
  search?: string;
  supplierType?: string;
  status?: string;
  productCategory?: string;
  location?: string;
  performanceTier?: string;
  deliveryReliabilityRange?: string;
  sort?: "highest_score" | "most_orders" | "lowest_price" | "fastest_delivery" | "recently_added";
  page?: number;
  pageSize?: number;
}

export const procurementService = {
  getBootstrap: (signal?: AbortSignal) =>
    apiGet<{
      summary: ProcurementSummary | null;
      insights: ProcurementInsight[];
      supplierOverview: SupplierOverviewResponse["overview"] | null;
      supplierRows: SupplierOverviewResponse["suppliers"];
      topPerformers: TopPerformer[];
      spendOptimization: SpendOptimization | null;
      purchaseOrders: PurchaseOrder[];
    }>("/api/procurement/bootstrap", signal),
  getSummary: (signal?: AbortSignal) => apiGet<ProcurementSummary>("/api/procurement/summary", signal),
  getInsights: (signal?: AbortSignal) => apiGet<ProcurementInsight[]>("/api/procurement/insights", signal),
  getSuppliersOverview: (signal?: AbortSignal) =>
    apiGet<SupplierOverviewResponse>("/api/procurement/suppliers/overview", signal),
  getTopPerformers: (signal?: AbortSignal) =>
    apiGet<TopPerformer[]>("/api/procurement/suppliers/top-performers", signal),
  getSpendOptimization: (signal?: AbortSignal) =>
    apiGet<SpendOptimization>("/api/procurement/spend-optimization", signal),
  getSuppliers: (options?: SupplierQueryOptions, signal?: AbortSignal) => {
    const searchParams = new URLSearchParams();
    if (options?.search) {
      searchParams.set("search", options.search);
    }
    if (options?.supplierType && options.supplierType !== "all") {
      searchParams.set("supplier_type", options.supplierType);
    }
    if (options?.status && options.status !== "all") {
      searchParams.set("status", options.status);
    }
    if (options?.productCategory && options.productCategory !== "all") {
      searchParams.set("product_category", options.productCategory);
    }
    if (options?.location && options.location !== "all") {
      searchParams.set("location", options.location);
    }
    if (options?.performanceTier && options.performanceTier !== "all") {
      searchParams.set("performance_tier", options.performanceTier);
    }
    if (options?.deliveryReliabilityRange && options.deliveryReliabilityRange !== "all") {
      searchParams.set("delivery_reliability_range", options.deliveryReliabilityRange);
    }
    if (options?.sort) {
      searchParams.set("sort", options.sort);
    }
    if (options?.page) {
      searchParams.set("page", String(options.page));
    }
    if (options?.pageSize) {
      searchParams.set("page_size", String(options.pageSize));
    }
    const query = searchParams.toString();
    return apiGet<SupplierManagementListResponse>(`/api/procurement/suppliers${query ? `?${query}` : ""}`, signal);
  },
  getSupplierById: (id: string, signal?: AbortSignal) =>
    apiGet<SupplierManagementDetail>(`/api/procurement/suppliers/${id}`, signal),
  createSupplier: (payload: SupplierUpsertPayload, signal?: AbortSignal) =>
    apiPost<SupplierMutationResponse, SupplierUpsertPayload>("/api/procurement/suppliers", payload, signal),
  updateSupplier: (id: string, payload: SupplierUpsertPayload, signal?: AbortSignal) =>
    apiPut<SupplierMutationResponse, SupplierUpsertPayload>(`/api/procurement/suppliers/${id}`, payload, signal),
  deleteSupplier: (id: string, signal?: AbortSignal) =>
    apiDelete<{ message: string }>(`/api/procurement/suppliers/${id}`, signal),
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
