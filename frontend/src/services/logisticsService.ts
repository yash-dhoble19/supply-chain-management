import { API_BASE_URL, apiGet, apiPost } from "./api";
import type {
  LoadType,
  LogisticsRoutePlan,
  Shipment,
  TrackingResponse,
} from "../types/logistics.types";

interface PlannerPayload {
  origin: string;
  destination: string;
  load_type: LoadType;
  origin_lat?: number;
  origin_lng?: number;
  dest_lat?: number;
  dest_lng?: number;
}

interface CreateShipmentPayload extends PlannerPayload {
  tracking_id?: string;
}

export const logisticsService = {
  planRoute(payload: PlannerPayload) {
    return apiPost<LogisticsRoutePlan, PlannerPayload>("/api/routes/plan", payload);
  },

  createShipment(payload: CreateShipmentPayload) {
    return apiPost<Shipment, CreateShipmentPayload>("/api/shipments/create", payload);
  },

  listShipments(signal?: AbortSignal) {
    return apiGet<Shipment[]>("/api/shipments", signal);
  },

  getShipment(id: number, signal?: AbortSignal) {
    return apiGet<Shipment>(`/api/shipments/${id}`, signal);
  },

  startShipment(id: number, tickSeconds = 5) {
    return apiPost<Shipment, { tick_seconds: number }>(`/api/shipments/${id}/start`, {
      tick_seconds: tickSeconds,
    });
  },

  getTracking(id: number, signal?: AbortSignal) {
    return apiGet<TrackingResponse>(`/api/tracking/${id}`, signal);
  },

  getShipmentSocketUrl(id: number) {
    const wsBase = API_BASE_URL.replace(/^http/, "ws");
    return `${wsBase}/api/ws/shipments/${id}`;
  },
};
