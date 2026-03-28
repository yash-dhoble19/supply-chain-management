export interface ProcurementSummary {
  systemHealthScore: number;
  healthStatus: "optimal" | "warning" | "critical";
  aiBriefing: string;
  criticalItems: number;
  pendingPOs: number;
  savingsToDate: number;
  savingsChange: string;
  leadTimeAverage: string;
  leadTimeChange: string;
}

export interface ProcurementInsight {
  id: string;
  productId: number;
  supplierId: number;
  sku: string;
  title: string;
  priority: "urgent" | "high" | "monitor" | "normal";
  reasoning: string;
  unitPrice: number;
  supplierScore: number;
  estimatedLeadTime: string;
  estimatedLeadTimeDays: number;
  replenishmentQty: number;
  actionLabel: string;
  actionType?: string;
  supplierName: string;
  estimatedCost: number;
}

export interface SupplierOverview {
  avgReliability: number;
  onTimeDelivery: number;
  qualityRate: number;
  esgCompliance: string;
}

export interface SupplierRow {
  id: string;
  name: string;
  location: string;
  verdict: string;
  score: number;
  reliability: number;
  onTimeDelivery: number;
  qualityRate: number;
  deliverySpeedDays: number;
  pricePerUnit: number;
}

export interface SupplierOverviewResponse {
  overview: SupplierOverview;
  suppliers: SupplierRow[];
}

export interface TopPerformer {
  id: string;
  rank: number;
  name: string;
  metricLabel: string;
  score: number;
}

export interface SpendOptimization {
  totalValue: number;
  yoyChange: string;
  budgetUtilization: number;
  buttonLabel: string;
}

export interface PurchaseOrder {
  id: string;
  poNumber: string;
  title: string;
  supplierName: string;
  status: string;
  priority: string;
  lifecycleStage: "draft" | "approved" | "in_transit" | "received";
  createdAt?: string;
  expectedDelivery?: string | null;
}
