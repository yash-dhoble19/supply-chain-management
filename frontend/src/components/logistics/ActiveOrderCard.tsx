import { useEffect, useState } from "react";
import type { LogisticsOrder } from "../../types/logistics.types";

interface ActiveOrderCardProps {
  order: LogisticsOrder;
}

function formatCoordinates(lat?: number | null, lon?: number | null) {
  if (lat == null || lon == null) return "Location not shared yet";
  return `${lat.toFixed(5)}, ${lon.toFixed(5)}`;
}

async function reverseGeocode(lat: number, lon: number): Promise<string> {
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=16&addressdetails=1`,
      {
        headers: {
          'User-Agent': 'SupplyChainDashboard/1.0'
        }
      }
    );
    const data = await response.json();
    if (data && data.display_name) {
      // Extract city/area from the full address
      const address = data.address || {};
      const city = address.city || address.town || address.village || address.suburb;
      const state = address.state;
      const country = address.country;
      
      if (city && state) {
        return `${city}, ${state}`;
      } else if (city) {
        return city;
      } else if (state) {
        return state;
      } else {
        // Fallback to a shortened version of display_name
        return data.display_name.split(',').slice(0, 2).join(', ');
      }
    }
    return formatCoordinates(lat, lon);
  } catch (error) {
    console.warn('Reverse geocoding failed:', error);
    return formatCoordinates(lat, lon);
  }
}

export function ActiveOrderCard({ order }: ActiveOrderCardProps) {
  const [locationLabel, setLocationLabel] = useState<string>("Loading location...");
  const [isLoadingLocation, setIsLoadingLocation] = useState(false);

  const hasLocation = order.current_location_lat != null && order.current_location_lon != null;

  useEffect(() => {
    if (!hasLocation) {
      setLocationLabel("Driver GPS not enabled yet");
      return;
    }

    setIsLoadingLocation(true);
    reverseGeocode(order.current_location_lat!, order.current_location_lon!)
      .then(setLocationLabel)
      .catch(() => setLocationLabel(formatCoordinates(order.current_location_lat, order.current_location_lon)))
      .finally(() => setIsLoadingLocation(false));
  }, [hasLocation, order.current_location_lat, order.current_location_lon]);

  const mapQuery = hasLocation
    ? `${order.current_location_lat},${order.current_location_lon}`
    : order.retailer_location
    ? encodeURIComponent(order.retailer_location)
    : undefined;

  return (
    <article className="rounded-[28px] border border-slate-200 bg-white/95 p-5 shadow-sm">
      <div className="flex flex-col gap-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.24em] text-slate-500">In Progress</p>
            <h3 className="mt-2 text-lg font-bold text-slate-950">{order.product_name}</h3>
            <p className="mt-1 text-sm text-slate-600">Qty: {order.quantity}</p>
          </div>
          <span className="inline-flex rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
            {order.status || "IN_PROGRESS"}
          </span>
        </div>

        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-2xl bg-slate-100 px-4 py-3">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">Order ID</p>
            <p className="mt-2 text-xl font-bold text-slate-900">{order.order_id ?? order.id}</p>
          </div>
          <div className="rounded-2xl bg-slate-100 px-4 py-3">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">Current Location</p>
            <p className="mt-2 text-sm font-semibold text-slate-900">
              {isLoadingLocation ? (
                <span className="inline-flex items-center gap-2">
                  <span className="h-3 w-3 animate-spin rounded-full border border-slate-400 border-t-transparent"></span>
                  Loading location...
                </span>
              ) : (
                locationLabel
              )}
            </p>
          </div>
          <div className="rounded-2xl bg-slate-100 px-4 py-3">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">Retailer</p>
            <p className="mt-2 text-sm font-semibold text-slate-900">{order.retailer_name || "Unknown"}</p>
          </div>
        </div>

        <div className="flex flex-col gap-3 text-sm text-slate-600">
          <div>
            <span className="font-semibold text-slate-800">Supplier:</span> {order.supplierName || "Unknown"}
          </div>
          <div>
            <span className="font-semibold text-slate-800">Destination:</span> {order.retailer_location || "Not set"}
          </div>
        </div>

        {mapQuery ? (
          <a
            href={`https://www.google.com/maps/search/?api=1&query=${mapQuery}`}
            target="_blank"
            rel="noreferrer"
            className="inline-flex w-fit rounded-full border border-slate-300 bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
          >
            View location in map
          </a>
        ) : null}
      </div>
    </article>
  );
}
