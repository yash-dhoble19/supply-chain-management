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

export interface SupplierManagementSummary {
  total_suppliers: number;
  active_suppliers: number;
  preferred_suppliers: number;
  avg_supplier_score: number;
  total_purchase_orders: number;
  total_spend: number;
}

export interface SupplierManagementFilters {
  supplier_types: string[];
  statuses: string[];
  product_categories: string[];
  locations: string[];
  performance_tiers: string[];
  delivery_reliability_ranges: string[];
}

export interface RecentSupplierPurchaseOrder {
  id: string;
  po_number: string;
  product_name: string;
  status: string;
  priority: string;
  total_value: number;
  created_at: string | null;
  expected_delivery: string | null;
}

export interface SupplierManagementRecord {
  supplier_id: string;
  supplier_name: string;
  supplier_code: string;
  company_name: string;
  contact_person: string | null;
  email: string;
  phone: string | null;
  website: string | null;
  product_name: string;
  product_category: string;
  supplied_products: string[];
  unit_price: number;
  currency: string;
  delivery_cost: number;
  average_delivery_days: number;
  minimum_order_quantity: number | null;
  supplier_score: number;
  reliability_percent: number;
  on_time_delivery_percent: number;
  total_orders: number;
  total_spend: number;
  status: string;
  raw_status: string;
  preferred_supplier: boolean;
  supplier_type: string;
  address: string | null;
  location: string;
  city: string | null;
  state: string | null;
  country: string | null;
  postal_code: string | null;
  gst_number: string | null;
  tax_id: string | null;
  notes: string | null;
  performance_tier: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface SupplierManagementDetail extends SupplierManagementRecord {
  recent_purchase_orders: RecentSupplierPurchaseOrder[];
}

export interface SupplierManagementListResponse {
  summary: SupplierManagementSummary;
  filters: SupplierManagementFilters;
  items: SupplierManagementRecord[];
  pagination: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
    filtered_items: number;
  };
}

export interface SupplierMutationResponse {
  message: string;
  supplier: SupplierManagementDetail;
}

export interface SupplierUpsertPayload {
  supplier_name: string;
  email: string;
  company_name?: string | null;
  supplier_code?: string | null;
  contact_person?: string | null;
  phone?: string | null;
  website?: string | null;
  product_name?: string | null;
  product_category?: string | null;
  unit_price: number;
  currency: string;
  delivery_cost: number;
  average_delivery_days: number;
  minimum_order_quantity?: number | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  postal_code?: string | null;
  supplier_type: string;
  status: string;
  preferred_supplier: boolean;
  supplier_score?: number | null;
  reliability_percent: number;
  on_time_delivery_percent: number;
  gst_number?: string | null;
  tax_id?: string | null;
  notes?: string | null;
}
