import { useState } from "react";
import type { ProcurementInsight } from "../types/procurement.types";
import type { PurchaseOrderDocumentData } from "../types/purchaseOrder.types";
import { purchaseOrderService } from "../services/purchaseOrderService";

interface UsePurchaseOrderOptions {
  onCreated?: () => void | Promise<void>;
  onUpdated?: () => void | Promise<void>;
}

export function usePurchaseOrder(options: UsePurchaseOrderOptions = {}) {
  const [activeOrder, setActiveOrder] = useState<PurchaseOrderDocumentData | null>(null);
  const [isPreviewOpen, setPreviewOpen] = useState(false);
  const [creatingInsightId, setCreatingInsightId] = useState<string | null>(null);
  const [isLoadingOrder, setLoadingOrder] = useState(false);
  const [isDownloadingPdf, setDownloadingPdf] = useState(false);
  const [isUpdatingStatus, setUpdatingStatus] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function createFromInsight(insight: ProcurementInsight) {
    setError(null);
    setCreatingInsightId(insight.id);

    try {
      const created = await purchaseOrderService.create({
        insightId: insight.id,
        sku: insight.sku,
        itemName: insight.title,
        unitPrice: insight.unitPrice,
        quantity: insight.replenishmentQty,
        supplierName: insight.supplierName,
        estimatedLeadTime: insight.estimatedLeadTime,
        supplierId: insight.supplierId,
        productId: insight.productId,
        priority: insight.priority,
        notes: insight.reasoning,
      });

      const order = await purchaseOrderService.getById(created.id);
      setActiveOrder(order);
      setPreviewOpen(true);
      await options.onCreated?.();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to create purchase order.");
    } finally {
      setCreatingInsightId(null);
    }
  }

  async function openPreview(orderId: string) {
    setError(null);
    setLoadingOrder(true);

    try {
      const order = await purchaseOrderService.getById(orderId);
      setActiveOrder(order);
      setPreviewOpen(true);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to load purchase order preview.");
    } finally {
      setLoadingOrder(false);
    }
  }

  function closePreview() {
    setPreviewOpen(false);
  }

  async function downloadPdf(orderId = activeOrder?.id) {
    if (!orderId) {
      return;
    }

    setError(null);
    setDownloadingPdf(true);

    try {
      const { blob, filename } = await purchaseOrderService.downloadPdf(orderId);
      const downloadUrl = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = downloadUrl;
      anchor.download = filename ?? `purchase-order-${orderId}.pdf`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to download purchase order PDF.");
    } finally {
      setDownloadingPdf(false);
    }
  }

  async function approvePurchaseOrder(orderId = activeOrder?.id) {
    if (!orderId) {
      return;
    }

    setError(null);
    setUpdatingStatus(true);

    try {
      const updatedOrder = await purchaseOrderService.updateStatus(orderId, { status: "APPROVED" });
      setActiveOrder(updatedOrder);
      await options.onUpdated?.();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to update purchase order.");
    } finally {
      setUpdatingStatus(false);
    }
  }

  return {
    activeOrder,
    isPreviewOpen,
    creatingInsightId,
    isLoadingOrder,
    isDownloadingPdf,
    isUpdatingStatus,
    error,
    createFromInsight,
    openPreview,
    closePreview,
    downloadPdf,
    approvePurchaseOrder,
  };
}
