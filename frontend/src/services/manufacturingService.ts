import { apiGet, apiPost, apiPut } from "./api";
import type { ManufacturingGoods, ManufacturingGoodsCreate, ManufacturingGoodsUpdate } from "../types/manufacturing.types";

export const manufacturingService = {
  getAll: (signal?: AbortSignal) => apiGet<ManufacturingGoods[]>("/api/manufacturing/", signal),
  create: (payload: ManufacturingGoodsCreate, signal?: AbortSignal) =>
    apiPost<ManufacturingGoods, ManufacturingGoodsCreate>("/api/manufacturing/", payload, signal),
  update: (id: number, payload: ManufacturingGoodsUpdate, signal?: AbortSignal) =>
    apiPut<ManufacturingGoods, ManufacturingGoodsUpdate>(`/api/manufacturing/${id}`, payload, signal),
  getCompleted: (signal?: AbortSignal) => apiGet<ManufacturingGoods[]>("/api/manufacturing/completed", signal),
};
// anything
