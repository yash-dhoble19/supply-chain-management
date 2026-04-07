export interface ManufacturingGoods {
  id: number;
  sku: string;
  product_name: string;
  status: string;
  progress: number;
  start_date: string | null;
  est_completion: string | null;
  unit_price: number;
}

export interface ManufacturingGoodsCreate {
  sku: string;
  product_name: string;
  status?: string;
  progress?: number;
  start_date?: string;
  est_completion?: string;
  unit_price: number;
}

export interface ManufacturingGoodsUpdate {
  status?: string;
  progress?: number;
}