import { apiGet, apiPost, apiPut, apiDelete } from "./api";
import type {
  InventorySummary,
  InventoryListResponse,
  InventoryItem,
  InventoryActivityItem,
} from "../types/inventory.types";

interface InventoryUpdatePayload {
  target_stock?: number;
  quantity_change?: number;
  reason: string;
}

export const inventoryService = {
  getBootstrap: (options?: { page?: number; limit?: number; search?: string }, signal?: AbortSignal) => {
    const searchParams = new URLSearchParams();
    if (options?.page) searchParams.set("page", String(options.page));
    if (options?.limit) searchParams.set("limit", String(options.limit));
    if (options?.search) searchParams.set("search", options.search);
    const query = searchParams.toString();
    return apiGet<{
      inventory: InventoryListResponse;
      summary: InventorySummary;
      activity: InventoryActivityItem[];
    }>(`/api/inventory/bootstrap${query ? `?${query}` : ""}`, signal);
  },
  getInventory: (options?: { page?: number; limit?: number; search?: string }, signal?: AbortSignal) => {
    const searchParams = new URLSearchParams();
    if (options?.page) searchParams.set("page", String(options.page));
    if (options?.limit) searchParams.set("limit", String(options.limit));
    if (options?.search) searchParams.set("search", options.search);
    const query = searchParams.toString();
    return apiGet<InventoryListResponse>(`/api/inventory/${query ? `?${query}` : ""}`, signal);
  },
  getSummary: (signal?: AbortSignal) => apiGet<InventorySummary>("/api/inventory/summary", signal),
  updateStock: (productId: number, payload: InventoryUpdatePayload, signal?: AbortSignal) =>
    apiPut<{ message: string; product_id: number; current_stock: number }, InventoryUpdatePayload>(
      `/api/inventory/${productId}`,
      payload,
      signal,
    ),
  getActivity: (signal?: AbortSignal, limit: number = 20) =>
    apiGet<InventoryActivityItem[]>(`/api/inventory/activity?limit=${limit}`, signal),
  createProduct: (payload: {
    sku: string;
    name: string;
    category: string;
    stage: string;
    current_stock: number;
    safety_stock_level: number;
    optimal_stock_level: number;
    unit_price: number;
  }) => apiPost<{message:string;product:any}, typeof payload>("/api/products/", payload),
  updateProduct: (productId: number, payload: Partial<{
    sku: string;
    name: string;
    category: string;
    stage: string;
    current_stock: number;
    safety_stock_level: number;
    optimal_stock_level: number;
    unit_price: number;
  }>) => apiPut<{message:string}, typeof payload>(`/api/products/${productId}`, payload),
  deleteProduct: (productId: number) => apiDelete<{message:string;product:any}>(`/api/products/${productId}`),
  logStockMovement: (payload: { product_id: number; quantity_change: number; reason: string }) =>
    apiPost<{ message: string; new_stock: number }, typeof payload>("/inventory/logs", payload),
  exportCsv: async (items: InventoryItem[]) => {
    const headers = ["SKU", "Name", "Category", "Stage", "Stock", "Status", "Capacity", "Total Value"];
    const rows = items.map((item) => [
      item.sku,
      item.name,
      item.category,
      item.stage,
      String(item.stock),
      item.status,
      `${item.capacity}%`,
      `$${item.total_value.toFixed(2)}`,
    ]);

    const csv = [headers, ...rows].map((row) => row.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "inventory_export.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  },
};

// anything
