import { apiDownload, apiGet, apiPost, apiPut } from "./api";
import type {
  PurchaseOrderCreatePayload,
  PurchaseOrderCreateResponse,
  PurchaseOrderDocumentData,
  PurchaseOrderStatusUpdatePayload,
} from "../types/purchaseOrder.types";

export const purchaseOrderService = {
  create: (payload: PurchaseOrderCreatePayload, signal?: AbortSignal) =>
    apiPost<PurchaseOrderCreateResponse, PurchaseOrderCreatePayload>(
      "/api/procurement/purchase-orders/create",
      payload,
      signal,
    ),
  getById: (id: string, signal?: AbortSignal) =>
    apiGet<PurchaseOrderDocumentData>(`/api/procurement/purchase-orders/${id}`, signal),
  updateStatus: (id: string, payload: PurchaseOrderStatusUpdatePayload, signal?: AbortSignal) =>
    apiPut<PurchaseOrderDocumentData, PurchaseOrderStatusUpdatePayload>(
      `/api/procurement/purchase-orders/${id}/status`,
      payload,
      signal,
    ),
  downloadPdf: (id: string, signal?: AbortSignal) =>
    apiDownload(`/api/procurement/purchase-orders/${id}/pdf`, signal),
};

// anything
