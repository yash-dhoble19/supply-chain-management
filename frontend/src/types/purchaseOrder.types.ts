export type PurchaseOrderStatus = "draft" | "approved" | "in_transit" | "received";

export interface PurchaseOrderLineItem {
  description: string;
  sku?: string;
  quantity: number;
  rate: number;
  amount: number;
}

export interface PurchaseOrderDocumentData {
  id: string;
  poNumber: string;
  issueDate: string;
  deliveryDate?: string | null;
  status: PurchaseOrderStatus;
  supplierName: string;
  supplierAddress?: string;
  supplierEmail?: string;
  companyName: string;
  companyAddress: string;
  billToCompany: string;
  billToAddress: string;
  priority?: string;
  notes?: string;
  subtotal: number;
  taxRate: number;
  tax: number;
  total: number;
  items: PurchaseOrderLineItem[];
  createdAt: string;
  previewUrl?: string;
}

export interface PurchaseOrderCreatePayload {
  insightId: string;
  sku: string;
  itemName: string;
  unitPrice: number;
  quantity: number;
  supplierName: string;
  estimatedLeadTime?: string;
  supplierId?: number;
  productId?: number;
  priority?: string;
  notes?: string;
}

export interface PurchaseOrderCreateResponse {
  id: string;
  poNumber: string;
  status: PurchaseOrderStatus;
  createdAt: string;
  previewUrl: string;
}

export interface PurchaseOrderStatusUpdatePayload {
  status: string;
}

// anything
