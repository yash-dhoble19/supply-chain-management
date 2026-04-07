export type LoadType = "STANDARD" | "BULK" | "PERISHABLE" | "FRAGILE" | "EXPRESS";

export interface LogisticsRoutePlan {
  origin: string;
  destination: string;
  load_type: LoadType;
  origin_lat: number;
  origin_lng: number;
  dest_lat: number;
  dest_lng: number;
  route_coordinates: [number, number][];
  distance_km: number;
  eta_hours: number;
  fuel_liters: number;
  average_speed_kmh: number;
  fuel_consumption_rate: number;
}

export interface Shipment {
  id: number;
  trackingId: string;
  trackingNumber: string;
  origin: string;
  destination: string;
  originLat: number | null;
  originLng: number | null;
  destLat: number | null;
  destLng: number | null;
  currentLat: number | null;
  currentLng: number | null;
  status: "CREATED" | "IN_TRANSIT" | "DELIVERED";
  progress: number;
  distanceKm: number;
  eta: string | null;
  startedAt: string | null;
  deliveredAt: string | null;
  loadType: LoadType;
  averageSpeedKmh: number;
  fuelConsumptionRate: number;
  fuelLiters: number;
  routeCoordinates: [number, number][];
  routeDurationSeconds: number;
  carrierId: number | null;
  driverId: number | null;
  createdAt: string | null;
}

export interface LogisticsOrder {
  id: number;
  order_id?: number;
  product_name: string;
  quantity: number;
  unit_price: number;
  status?: string;
  driver_id?: number;
  retailer_name?: string;
  retailer_email?: string;
  retailer_phone?: string;
  retailer_location?: string;
  sku?: string;
  category?: string;
  notes?: string;
  imageUrl?: string;
  supplierName?: string;
  supplierEmail?: string;
  supplierMobile?: string;
  supplierCompany?: string;
  current_location_lat?: number | null;
  current_location_lon?: number | null;
  created_at?: string | null;
}

export interface TrackingLog {
  id: number;
  latitude: number;
  longitude: number;
  timestamp: string;
}

export interface TrackingResponse {
  shipment: Shipment;
  logs: TrackingLog[];
}

export interface LogisticsSocketMessage {
  type: "shipment.snapshot" | "shipment.updated" | "shipment.delivered";
  shipment: Shipment;
  tracking: TrackingLog[];
}

export interface ShipmentPlannerForm {
  origin: string;
  destination: string;
  loadType: LoadType;
  originLat: string;
  originLng: string;
  destLat: string;
  destLng: string;
}

export const LOGISTICS_LOAD_TYPES: LoadType[] = [
  "STANDARD",
  "BULK",
  "PERISHABLE",
  "FRAGILE",
  "EXPRESS",
];
