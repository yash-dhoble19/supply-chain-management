export type MetricTone = "primary" | "danger" | "warning" | "success" | "neutral";
export type ShipmentTone = "primary" | "warning" | "success" | "neutral";
export type ActivityType = "inventory" | "procurement" | "shipment" | "order";

export interface Metric {
  id: string;
  title: string;
  value: number;
  status: string;
  change?: string;
  tone: MetricTone;
  icon: string;
  format: "number" | "currency" | "percent";
}

export interface Shipment {
  id: string;
  trackingNumber: string;
  source: string;
  destination: string;
  status: string;
  progress: number;
  eta?: string | null;
  detail: string;
  tone: ShipmentTone;
}

export interface Activity {
  id: string;
  title: string;
  description: string;
  timestamp: string;
  type: ActivityType;
}

export interface Stats {
  id: string;
  label: string;
  value: string;
  description: string;
  icon: string;
}

export interface DashboardData {
  metrics: Metric[];
  shipments: Shipment[];
  activities: Activity[];
  stats: Stats[];
}

export interface OverviewSeriesItem {
  id: string;
  label: string;
  value: number;
  tone: MetricTone | ShipmentTone;
}

export interface TopInventoryItem {
  id: string;
  name: string;
  sku: string;
  category: string;
  value: number;
  stock: number;
  status: string;
}

export interface ExecutiveBrief {
  id: string;
  title: string;
  description: string;
  tone: MetricTone;
}

export interface DashboardOverview {
  inventoryStatus: OverviewSeriesItem[];
  inventoryStages: OverviewSeriesItem[];
  shipmentStatus: OverviewSeriesItem[];
  orderStatus: OverviewSeriesItem[];
  purchaseOrderStatus: OverviewSeriesItem[];
  topInventory: TopInventoryItem[];
  executiveBriefs: ExecutiveBrief[];
}

// anything
