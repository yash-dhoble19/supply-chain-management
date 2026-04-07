import type { PurchaseOrderStatus } from "../types/purchaseOrder.types";

export function formatPurchaseOrderCurrency(value: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatPurchaseOrderDate(value?: string | null): string {
  if (!value) {
    return "Pending";
  }

  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}

export function getPurchaseOrderStatusLabel(status: PurchaseOrderStatus): string {
  return status.replace("_", " ").replace(/\b\w/g, (match) => match.toUpperCase());
}
