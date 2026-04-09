export interface InventoryItem {
  id: number;
  sku: string;
  name: string;
  category: string;
  stage: string;
  stock: number;
  safety_stock_level: number;
  optimal_stock_level: number;
  unit_price: number;
  status: string;
  capacity: number;
  pending_po_qty: number;
  in_transit_po_qty: number;
  total_value: number;
}

export interface InventorySummary {
  total_items: number;
  total_value: number;
  critical_items: number;
}

export interface InventoryActivityItem {
  id: number;
  product_id: number;
  product_name: string;
  sku: string;
  change_date: string;
  quantity_change: number;
  reason: string;
  stockout_flag: boolean;
}

export interface InventoryListResponse {
  page: number;
  limit: number;
  total: number;
  items: InventoryItem[];
}

// anything
