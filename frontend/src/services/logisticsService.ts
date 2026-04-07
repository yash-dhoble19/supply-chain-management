import { API_BASE_URL, apiDelete, apiGet, apiPost } from "./api";
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

  deleteShipment(id: number) {
    return apiDelete<{ success: boolean; shipment_id: number }>(`/api/shipments/${id}`);
  },

  getTracking(id: number, signal?: AbortSignal) {
    return apiGet<TrackingResponse>(`/api/tracking/${id}`, signal);
  },

  getShipmentSocketUrl(id: number) {
    const wsBase = API_BASE_URL.replace(/^http/, "ws");
    return `${wsBase}/api/ws/shipments/${id}`;
  },

  updateLogisticsOrderLocation(orderId: number, current_location_lat: number, current_location_lon: number) {
    return apiPost<{ success: boolean; order_id: number }, { current_location_lat: number; current_location_lon: number }>(
      `/logistics/orders/${orderId}/update-location`,
      { current_location_lat, current_location_lon }
    );
  },

  // Fetch logistics orders for dashboard
  listLogisticsOrders(
    filters?: { status?: string; driver_id?: number; unassigned?: boolean },
    signal?: AbortSignal,
  ) {
    const params = new URLSearchParams();
    if (filters?.status) params.set("status", filters.status);
    if (filters?.driver_id !== undefined) params.set("driver_id", String(filters.driver_id));
    if (filters?.unassigned !== undefined) params.set("unassigned", String(filters.unassigned));
    const query = params.toString();
    return apiGet<any[]>(`/logistics/orders/${query ? `?${query}` : ""}`, signal);
  },

  // Accept a job (assign driver)
  acceptJob(orderId: number, driverId: number) {
    return apiPost<{ success: boolean; order_id: number }, { driver_id: number }>(
      `/logistics/orders/${orderId}/accept`,
      { driver_id: driverId }
    );
  },

  // Mark a logistics order as sourced for drivers
  sourceDriver(orderId: number) {
    return apiPost<{ success: boolean; order_id: number }, Record<string, never>>(
      `/logistics/orders/${orderId}/source-driver`,
      {}
    );
  },
};
