
import React, { useState, useEffect } from "react";
import { logisticsService } from "../services/logisticsService";

type Tab = "dashboard" | "available" | "myjobs" | "profile";

const SIDEBAR_ITEMS = [
  { key: "dashboard", label: "Dashboard", icon: "dashboard" },
  { key: "available", label: "Available Jobs", icon: "work" },
  { key: "myjobs", label: "My Jobs", icon: "assignment_turned_in" },
  { key: "profile", label: "Profile", icon: "person" },
];

// Dummy user for demo; replace with real auth
const DEMO_USER = { name: "Driver John", email: "driver@example.com" };

interface DriverDashboardProps {
  user: {
    id: number;
    name: string;
    email: string;
    role: string;
  };
  onLogout: () => void;
}

// Reverse geocoding utility
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
    return `${lat.toFixed(5)}, ${lon.toFixed(5)}`;
  } catch (error) {
    console.warn('Reverse geocoding failed:', error);
    return `${lat.toFixed(5)}, ${lon.toFixed(5)}`;
  }
}

// Hook for location display
function useLocationDisplay(lat?: number | null, lon?: number | null) {
  const [locationLabel, setLocationLabel] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (lat == null || lon == null) {
      setLocationLabel("Not shared");
      return;
    }

    setIsLoading(true);
    reverseGeocode(lat, lon)
      .then(setLocationLabel)
      .catch(() => setLocationLabel(`${lat.toFixed(5)}, ${lon.toFixed(5)}`))
      .finally(() => setIsLoading(false));
  }, [lat, lon]);

  return { locationLabel, isLoading };
}

// Job item component with location display
function JobItem({ job, isGpsEnabled }: { job: any; isGpsEnabled: boolean }) {
  const { locationLabel, isLoading } = useLocationDisplay(job.current_location_lat, job.current_location_lon);

  return (
    <div className="bg-white rounded-xl p-6 shadow flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <div>
        <div className="font-semibold text-lg">{job.product_name}</div>
        <div className="text-slate-500 text-sm">Qty: {job.quantity} | Category: {job.category}</div>
        <div className="text-slate-400 text-xs mt-1">Order ID: {job.id}</div>
        <div className="text-slate-500 text-sm mt-2">
          GPS: {isLoading ? "Loading location..." : locationLabel || (isGpsEnabled ? "Waiting for permission" : "Not shared")}
        </div>
      </div>
      <span className="inline-block px-4 py-2 bg-green-100 text-green-700 rounded-lg">In Progress</span>
    </div>
  );
}

export function DriverDashboard({ user, onLogout }: DriverDashboardProps) {
    const [viewJob, setViewJob] = useState<any | null>(null);
  const [tab, setTab] = useState<Tab>("dashboard");
  const [availableJobs, setAvailableJobs] = useState<any[]>([]);
  const [myJobs, setMyJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isGpsEnabled, setIsGpsEnabled] = useState(false);
  const [gpsError, setGpsError] = useState<string | null>(null);


  // Demo driver id (replace with real auth)
  const DRIVER_ID = 1;

  // Fetch all jobs and split into available/my jobs
  const fetchJobs = React.useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setError(null);

    try {
      const [available, mine] = await Promise.all([
        logisticsService.listLogisticsOrders({ status: "Sourced", unassigned: true }, signal),
        logisticsService.listLogisticsOrders({ driver_id: DRIVER_ID }, signal),
      ]);

      setAvailableJobs(available);
      setMyJobs(mine);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load jobs");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchJobs(controller.signal);

    const handler = () => fetchJobs();
    window.addEventListener("logistics-orders-updated", handler);
    return () => {
      controller.abort();
      window.removeEventListener("logistics-orders-updated", handler);
    };
    // eslint-disable-next-line
  }, [tab]);

  useEffect(() => {
    if (!isGpsEnabled || !navigator.geolocation || myJobs.length === 0) {
      return;
    }

    setGpsError(null);
    const watchId = navigator.geolocation.watchPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        myJobs.forEach((job) => {
          logisticsService.updateLogisticsOrderLocation(job.id, latitude, longitude).catch(() => {
            // Ignore individual update failures; we keep trying.
          });
        });
        fetchJobs();
      },
      (positionError) => {
        setGpsError(positionError.message || "Unable to retrieve driver location");
      },
      {
        enableHighAccuracy: true,
        maximumAge: 5000,
        timeout: 10000,
      },
    );

    return () => {
      navigator.geolocation.clearWatch(watchId);
    };
  }, [isGpsEnabled, myJobs, fetchJobs]);

  // Accept job handler
  const acceptJob = async (jobId: number) => {
    // Optimistically move job to myJobs
    setAvailableJobs((prev) => prev.filter((j) => j.id !== jobId));
    setMyJobs((prev) => [
      ...prev,
      availableJobs.find((j) => j.id === jobId)
    ].filter(Boolean));
    setLoading(true);
    try {
      await logisticsService.acceptJob(jobId, DRIVER_ID);
      fetchJobs();
    } catch (e) {
      setError("Failed to accept job");
      setLoading(false);
    }
  };

  const handleToggleGps = () => {
    if (!navigator.geolocation) {
      setGpsError("Geolocation is not supported by this browser.");
      return;
    }
    setGpsError(null);
    setIsGpsEnabled((current) => !current);
  };

  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Sidebar */}
      <aside className="w-60 bg-white border-r border-slate-200 flex flex-col py-6">
        <div className="px-6 pb-8">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-3xl text-blue-700">local_shipping</span>
            <span className="font-bold text-lg">Drivers Dashboard</span>
          </div>
        </div>
        <nav className="flex-1">
          {SIDEBAR_ITEMS.map((item) => (
            <button
              key={item.key}
              className={`flex items-center w-full px-6 py-3 text-left gap-3 hover:bg-blue-50 ${tab === item.key ? "bg-blue-100 text-blue-700 font-semibold" : "text-slate-700"}`}
              onClick={() => setTab(item.key as Tab)}
            >
              <span className="material-symbols-outlined text-xl">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>
        <div className="mt-auto px-6 pt-8">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span className="material-symbols-outlined text-base">account_circle</span>
            Manufacturer Admin
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-10">
        {tab === "dashboard" && (
          <div>
            <h1 className="text-2xl font-bold mb-6">Welcome back, {DEMO_USER.name}</h1>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
              <div className="rounded-2xl bg-white p-6 shadow">
                <div className="text-sm text-slate-500 font-semibold">Jobs in your area</div>
                <div className="text-3xl font-bold mt-2">{availableJobs.length + myJobs.length}</div>
              </div>
              <div className="rounded-2xl bg-white p-6 shadow">
                <div className="text-sm text-slate-500 font-semibold">In progress</div>
                <div className="text-3xl font-bold mt-2">{myJobs.length}</div>
              </div>
              <div className="rounded-2xl bg-white p-6 shadow">
                <div className="text-sm text-slate-500 font-semibold">Completed</div>
                <div className="text-3xl font-bold mt-2">42</div>
              </div>
            </div>
            <div className="bg-white rounded-2xl p-6 shadow mb-6">
              <div className="font-semibold mb-2">Active Shipments</div>
              {myJobs.length === 0 ? (
                <div className="text-slate-500">No active shipments.</div>
              ) : (
                <div className="space-y-4">
                  {myJobs.map((job) => (
                    <div key={job.id} className="rounded-xl border p-4 flex flex-col md:flex-row md:items-center md:justify-between">
                      <div>
                        <div className="font-semibold">{job.product_name}</div>
                        <div className="text-slate-500 text-sm">Qty: {job.quantity}</div>
                        <div className="text-slate-400 text-xs">Order ID: {job.id}</div>
                      </div>
                      <span className="inline-block px-4 py-2 bg-green-100 text-green-700 rounded-lg mt-2 md:mt-0">In Progress</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="bg-white rounded-2xl p-6 shadow">
              <div className="font-semibold mb-2">Quick Actions</div>
              <div className="flex gap-4">
                <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  <span className="material-symbols-outlined">search</span> Find Jobs
                </button>
                <button className="flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200">
                  <span className="material-symbols-outlined">assignment_turned_in</span> My Jobs
                </button>
              </div>
            </div>            <div className="bg-white rounded-2xl p-6 shadow mb-6">
              <div className="font-semibold mb-3">GPS Sharing</div>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-slate-600">
                  Enable GPS sharing so your accepted orders report live location back to the manufacturer.
                </p>
                <button
                  className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${isGpsEnabled ? "bg-emerald-600 text-white hover:bg-emerald-700" : "bg-slate-100 text-slate-700 hover:bg-slate-200"}`}
                  onClick={handleToggleGps}
                >
                  {isGpsEnabled ? "Disable GPS sharing" : "Allow GPS sharing"}
                </button>
              </div>
              {gpsError ? <p className="mt-3 text-sm text-red-500">{gpsError}</p> : null}
            </div>          </div>
        )}

        {tab === "available" && (
          <div>
            <h2 className="text-xl font-bold mb-4">Available Jobs</h2>
            {loading ? (
              <div>Loading...</div>
            ) : error ? (
              <div className="text-red-500">{error}</div>
            ) : availableJobs.length === 0 ? (
              <div>No available jobs at the moment.</div>
            ) : (
              <div className="grid gap-4">
                {availableJobs.map((job) => (
                  <div key={job.id} className="bg-white rounded-xl p-6 shadow flex flex-col md:flex-row md:items-center md:justify-between">
                    <div>
                      <div className="font-semibold text-lg">{job.product_name}</div>
                      <div className="text-slate-500 text-sm">Qty: {job.quantity} | Category: {job.category}</div>
                      <div className="text-slate-400 text-xs mt-1">Order ID: {job.id}</div>
                    </div>
                    <div className="flex gap-2 mt-4 md:mt-0">
                      <button
                        className="px-4 py-2 bg-gray-100 text-blue-700 rounded-lg border border-blue-200 hover:bg-blue-50"
                        onClick={() => setViewJob(job)}
                      >
                        View
                      </button>
                      <button
                        className="px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                        onClick={() => acceptJob(job.id)}
                      >
                        Accept Job
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Job Details Modal */}
            {viewJob && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
                <div className="bg-white rounded-2xl shadow-xl max-w-lg w-full p-8 relative max-h-[90vh] overflow-auto">
                  <button
                    className="absolute top-3 right-3 text-slate-400 hover:text-slate-700"
                    onClick={() => setViewJob(null)}
                  >
                    <span className="material-symbols-outlined">close</span>
                  </button>
                  <h3 className="text-xl font-bold mb-2">Job Details</h3>
                  <div className="mb-2"><span className="font-semibold">Product:</span> {viewJob.product_name}</div>
                  <div className="mb-2"><span className="font-semibold">Quantity:</span> {viewJob.quantity}</div>
                  <div className="mb-2"><span className="font-semibold">Order ID:</span> {viewJob.id}</div>
                  <div className="mb-2"><span className="font-semibold">Supplier Name:</span> {viewJob.supplierName || "-"}</div>
                  <div className="mb-2"><span className="font-semibold">Supplier Email:</span> {viewJob.supplierEmail || "-"}</div>
                  <div className="mb-2"><span className="font-semibold">Supplier Mobile:</span> {viewJob.supplierMobile || "-"}</div>
                  <div className="mb-2"><span className="font-semibold">Supplier Company:</span> {viewJob.supplierCompany || "-"}</div>
                  <div className="mb-2"><span className="font-semibold">Retailer Name:</span> {viewJob.retailer_name}</div>
                  <div className="mb-2"><span className="font-semibold">Retailer Email:</span> {viewJob.retailer_email}</div>
                  <div className="mb-2"><span className="font-semibold">Retailer Phone:</span> {viewJob.retailer_phone}</div>
                  <div className="mb-2"><span className="font-semibold">Retailer Location:</span> {viewJob.retailer_location}</div>
                  {/* Location details for delivery */}
                  {viewJob.retailer_location && (
                    <div className="mt-4">
                      <span className="font-semibold">Delivery Location:</span>
                      <div className="text-blue-700 underline">
                        <a
                          href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(viewJob.retailer_location)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          View on Map
                        </a>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {tab === "myjobs" && (
          <div>
            <h2 className="text-xl font-bold mb-4">My Jobs</h2>
            {loading ? (
              <div>Loading...</div>
            ) : error ? (
              <div className="text-red-500">{error}</div>
            ) : myJobs.length === 0 ? (
              <div>You have not accepted any jobs yet.</div>
            ) : (
              <div className="grid gap-4">
                {myJobs.map((job) => (
                  <JobItem key={job.id} job={job} isGpsEnabled={isGpsEnabled} />
                ))}
              </div>
            )}
          </div>
        )}

        {tab === "profile" && (
          <div>
            <h2 className="text-xl font-bold mb-4">Profile</h2>
            <div className="bg-white rounded-xl p-6 shadow">
              <div className="font-semibold">{DEMO_USER.name}</div>
              <div className="text-slate-500">{DEMO_USER.email}</div>
              <div className="mt-4 text-xs text-slate-400">Role: Driver</div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
