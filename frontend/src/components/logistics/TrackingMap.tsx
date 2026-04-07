import { useEffect, useRef } from "react";
import L from "leaflet";
import { MapContainer, Marker, Polyline, Popup, TileLayer, useMap } from "react-leaflet";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";
import type { Shipment, TrackingLog } from "../../types/logistics.types";

L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

function haversineDistance(lat1: number, lng1: number, lat2: number, lng2: number) {
  const toRadians = (degrees: number) => (degrees * Math.PI) / 180;
  const earthRadiusKm = 6371;
  const dLat = toRadians(lat2 - lat1);
  const dLon = toRadians(lng2 - lng1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return earthRadiusKm * c;
}

function estimateTollCount(distanceKm: number) {
  if (distanceKm < 40) return 0;
  return Math.max(1, Math.round(distanceKm / 80));
}

function buildRouteProgress(routeCoordinates: [number, number][], currentPosition: [number, number] | null) {
  const totalDistance = routeCoordinates.reduce((sum, coord, index) => {
    if (index === 0) return 0;
    const previous = routeCoordinates[index - 1];
    return sum + haversineDistance(previous[0], previous[1], coord[0], coord[1]);
  }, 0);

  if (!currentPosition || routeCoordinates.length < 2) {
    return {
      coveredDistance: 0,
      remainingDistance: totalDistance,
      progressPercent: 0,
      progressCoordinates: [] as [number, number][],
    };
  }

  let Nearest = {
    index: 0,
    distance: Number.POSITIVE_INFINITY,
  };

  routeCoordinates.forEach((coord, index) => {
    const dist = haversineDistance(coord[0], coord[1], currentPosition[0], currentPosition[1]);
    if (dist < Nearest.distance) {
      Nearest = { index, distance: dist };
    }
  });

  const coveredDistance = routeCoordinates.slice(1, Nearest.index + 1).reduce((sum, coord, index) => {
    const previous = routeCoordinates[index];
    return sum + haversineDistance(previous[0], previous[1], coord[0], coord[1]);
  }, 0);

  const progressCoordinates = routeCoordinates.slice(0, Nearest.index + 1);
  return {
    coveredDistance,
    remainingDistance: Math.max(0, totalDistance - coveredDistance),
    progressPercent: totalDistance > 0 ? Math.min(100, (coveredDistance / totalDistance) * 100) : 0,
    progressCoordinates,
  };
}

const liveMarker = new L.DivIcon({
  className: "",
  html: `
    <div style="display:flex;align-items:center;justify-content:center">
      <div style="width:20px;height:20px;border-radius:999px;background:#0f172a;border:4px solid #38bdf8;box-shadow:0 0 0 12px rgba(56,189,248,0.18)"></div>
    </div>
  `,
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

function FitMapBounds({ shipment, tracking }: { shipment: Shipment; tracking: TrackingLog[] }) {
  const map = useMap();
  const lastViewportKeyRef = useRef<string | null>(null);

  useEffect(() => {
    const viewportKey = `${shipment.id}:${shipment.routeCoordinates.length}:${tracking.length ? "tracked" : "static"}`;
    if (lastViewportKeyRef.current === viewportKey) {
      return;
    }

    const bounds: [number, number][] = [];
    shipment.routeCoordinates.forEach((coordinate) => bounds.push(coordinate));
    if (shipment.originLat !== null && shipment.originLng !== null) {
      bounds.push([shipment.originLat, shipment.originLng]);
    }
    if (shipment.destLat !== null && shipment.destLng !== null) {
      bounds.push([shipment.destLat, shipment.destLng]);
    }
    tracking.forEach((log) => bounds.push([log.latitude, log.longitude]));

    if (!bounds.length) {
      return;
    }

    map.fitBounds(bounds, { padding: [32, 32] });
    lastViewportKeyRef.current = viewportKey;
  }, [map, shipment, tracking]);

  return null;
}

interface TrackingMapProps {
  shipment: Shipment | null;
  tracking: TrackingLog[];
  isLive: boolean;
}

export function TrackingMap({ shipment, tracking, isLive }: TrackingMapProps) {
  if (!shipment || shipment.originLat === null || shipment.originLng === null) {
    return (
      <section className="rounded-[28px] border border-dashed border-slate-300 bg-white/70 p-6 text-sm text-slate-600 shadow-sm">
        Choose an active shipment to open the live map and socket feed.
      </section>
    );
  }

  const currentPosition: [number, number] | null =
    shipment.currentLat !== null && shipment.currentLng !== null
      ? [shipment.currentLat, shipment.currentLng]
      : null;

  const destinationPosition: [number, number] | null =
    shipment.destLat !== null && shipment.destLng !== null ? [shipment.destLat, shipment.destLng] : null;

  const originPosition: [number, number] = [shipment.originLat, shipment.originLng];

  const routeDistanceKm = shipment.distanceKm ?? shipment.routeCoordinates.reduce((sum, coord, index) => {
    if (index === 0) return 0;
    const previous = shipment.routeCoordinates[index - 1];
    return sum + haversineDistance(previous[0], previous[1], coord[0], coord[1]);
  }, 0);

  const tollCount = estimateTollCount(routeDistanceKm);
  const routeProgress = buildRouteProgress(shipment.routeCoordinates, currentPosition);
  const fuelUsedLiters = Number((routeProgress.coveredDistance * shipment.fuelConsumptionRate).toFixed(2));
  const fuelRemainingLiters = Number((routeProgress.remainingDistance * shipment.fuelConsumptionRate).toFixed(2));
  const effectiveProgress = currentPosition ? routeProgress.progressPercent : shipment.progress;

  return (
    <section className="overflow-hidden rounded-[32px] border border-slate-200 bg-white shadow-[0_20px_50px_rgba(15,23,42,0.08)]">
      <div className="flex flex-col gap-3 border-b border-slate-200 bg-slate-950 px-6 py-5 text-white lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.24em] text-sky-300">Live tracking</p>
          <h3 className="mt-2 text-2xl font-bold">
            {shipment.origin} to {shipment.destination}
          </h3>
        </div>
        <div className="flex items-center gap-3 text-sm text-slate-200">
          <span className={`h-2.5 w-2.5 rounded-full ${isLive ? "bg-emerald-400" : "bg-amber-400"}`} />
          {isLive ? "WebSocket connected" : "Waiting for active transit"}
        </div>
      </div>

      <div className="grid gap-5 p-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div className="overflow-hidden rounded-[28px] border border-slate-200">
          <MapContainer center={originPosition} zoom={5} scrollWheelZoom className="h-[460px] w-full">
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            <FitMapBounds shipment={shipment} tracking={tracking} />

            {shipment.routeCoordinates.length > 1 ? (
              <Polyline positions={shipment.routeCoordinates} pathOptions={{ color: "#0f172a", weight: 4, opacity: 0.8 }} />
            ) : null}

            {routeProgress.progressCoordinates.length > 1 ? (
              <Polyline positions={routeProgress.progressCoordinates} pathOptions={{ color: "#38bdf8", weight: 6, opacity: 0.9 }} />
            ) : null}

            <Marker position={originPosition}>
              <Popup>Origin</Popup>
            </Marker>

            {destinationPosition ? (
              <Marker position={destinationPosition}>
                <Popup>Destination</Popup>
              </Marker>
            ) : null}

            {currentPosition ? (
              <Marker position={currentPosition} icon={liveMarker}>
                <Popup>Current position</Popup>
              </Marker>
            ) : null}
          </MapContainer>
        </div>

        <div className="space-y-4">
          <div className="rounded-[28px] bg-slate-100 p-5">
            <p className="text-xs font-bold uppercase tracking-[0.24em] text-slate-500">Shipment status</p>
            <p className="mt-3 text-3xl font-bold text-slate-950">{shipment.status.replace("_", " ")}</p>
            <p className="mt-2 text-sm text-slate-600">Progress {effectiveProgress.toFixed(1)}%</p>
            <div className="mt-4 h-3 rounded-full bg-white">
              <div
                className="h-3 rounded-full bg-gradient-to-r from-sky-500 to-emerald-500"
                style={{ width: `${Math.max(2, effectiveProgress)}%` }}
              />
            </div>
          </div>

          <div className="rounded-[28px] bg-slate-50 p-5">
            <p className="text-xs font-bold uppercase tracking-[0.24em] text-slate-500">Route summary</p>
            <div className="mt-4 grid gap-3">
              <div className="rounded-2xl bg-white p-4 shadow-sm">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Total distance</p>
                <p className="mt-2 text-lg font-semibold text-slate-900">{routeDistanceKm.toFixed(1)} km</p>
              </div>
              <div className="rounded-2xl bg-white p-4 shadow-sm">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Covered</p>
                <p className="mt-2 text-lg font-semibold text-slate-900">{routeProgress.coveredDistance.toFixed(1)} km</p>
              </div>
              <div className="rounded-2xl bg-white p-4 shadow-sm">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Remaining</p>
                <p className="mt-2 text-lg font-semibold text-slate-900">{routeProgress.remainingDistance.toFixed(1)} km</p>
              </div>
              <div className="rounded-2xl bg-white p-4 shadow-sm">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Fuel consumed</p>
                <p className="mt-2 text-lg font-semibold text-slate-900">{fuelUsedLiters.toFixed(1)} L</p>
              </div>
              <div className="rounded-2xl bg-white p-4 shadow-sm">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Fuel remaining</p>
                <p className="mt-2 text-lg font-semibold text-slate-900">{fuelRemainingLiters.toFixed(1)} L</p>
              </div>
              <div className="rounded-2xl bg-white p-4 shadow-sm">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Estimated tolls</p>
                <p className="mt-2 text-lg font-semibold text-slate-900">{tollCount}</p>
              </div>
            </div>
          </div>

          <div className="rounded-[28px] bg-sky-50 p-5">
            <p className="text-xs font-bold uppercase tracking-[0.24em] text-sky-700">Movement log</p>
            <div className="mt-4 max-h-[230px] space-y-3 overflow-y-auto pr-1">
              {tracking.length ? (
                tracking
                  .slice()
                  .reverse()
                  .map((log) => (
                    <div key={log.id} className="rounded-2xl bg-white px-4 py-3 shadow-sm">
                      <p className="text-sm font-semibold text-slate-900">
                        {log.latitude.toFixed(4)}, {log.longitude.toFixed(4)}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">{new Date(log.timestamp).toLocaleString()}</p>
                    </div>
                  ))
              ) : (
                <p className="text-sm text-slate-600">Tracking logs will appear once the shipment starts moving.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
