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
  carrier_id?: number | null;
  driver_id?: number | null;
}

export interface ScheduleRequest {
  id: number;
  origin: string;
  destination: string;
  load_type: string;
  distance_km?: number;
  eta_hours?: number;
  driver_id: number;
  driver_name: string;
  product_name: string;
  quantity: number;
  carrier_type?: string;
  status: "PENDING" | "ACCEPTED" | "REJECTED" | "IN_PROGRESS" | "COMPLETED";
  created_at: string;
  manufacturer_name: string;
  shipment_id?: number;
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

  // Schedules (Manufacturer -> Driver assignment)
  createSchedule(payload: Omit<ScheduleRequest, "id" | "status" | "created_at" | "driver_name" | "manufacturer_name"> & { logistics_order_id?: number, shipment_id?: number }) {
    return apiPost<ScheduleRequest, any>("/api/schedules/", payload);
  },

  listSchedules(driverId?: number, signal?: AbortSignal) {
    const query = driverId ? `?driver_id=${driverId}` : "";
    return apiGet<ScheduleRequest[]>(`/api/schedules/${query}`, signal);
  },

  respondToSchedule(id: number, status: "ACCEPTED" | "REJECTED" | "IN_PROGRESS") {
    return apiPost<any, any>(`/api/schedules/${id}/status`, { status }); // Using apiPut or custom fetch if it's PATCH, but apiGet/apiPost are helpers. Let's use apiPost or fetch.
  },
  
  // Backward compatibility methods for DriverDashboard
  listLogisticsOrders(params: { status?: string; driver_id?: number; unassigned?: boolean } = {}, signal?: AbortSignal) {
    const queryParts = Object.entries(params)
      .map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`)
      .join("&");
    return apiGet<any[]>(`/logistics/orders/${queryParts ? "?" + queryParts : ""}`, signal);
  },

  acceptJob(orderId: number, driverId: number) {
    return apiPost<any, any>(`/logistics/orders/${orderId}/accept`, { driver_id: driverId });
  },

  updateLogisticsOrderLocation(orderId: number, lat: number, lon: number) {
    return apiPost<any, any>(`/logistics/orders/${orderId}/update-location`, {
      current_location_lat: lat,
      current_location_lon: lon,
    });
  }
};
