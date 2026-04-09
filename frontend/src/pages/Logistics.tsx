import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Header } from "../components/layout/Header";
import { Sidebar } from "../components/layout/Sidebar";
import { RouteForm } from "../components/logistics/RouteForm";
import { RouteInsights } from "../components/logistics/RouteInsights";
import { ShipmentCard } from "../components/logistics/ShipmentCard";
import { TrackingMap } from "../components/logistics/TrackingMap";
import { logisticsService } from "../services/logisticsService";
import type {
  LogisticsRoutePlan,
  LogisticsSocketMessage,
  Shipment,
  ShipmentPlannerForm,
  TrackingLog,
} from "../types/logistics.types";
import type { AppPage } from "../types/app.types";

interface LogisticsProps {
  activePage: AppPage;
  onNavigate: (page: AppPage) => void;
}

const defaultForm: ShipmentPlannerForm = {
  origin: "",
  destination: "",
  loadType: "STANDARD",
  originLat: "",
  originLng: "",
  destLat: "",
  destLng: "",
  driverId: "",
  productName: "",
  quantity: "",
};

function toOptionalNumber(value: string) {
  const trimmed = value.trim();
  if (!trimmed) return undefined;
  const parsed = Number(trimmed);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function matchesShipmentSearch(shipment: Shipment, query: string) {
  if (!query) return true;
  const normalized = query.toLowerCase();
  return [
    shipment.trackingId,
    shipment.trackingNumber,
    shipment.origin,
    shipment.destination,
    shipment.status,
    shipment.loadType,
  ].some((value) => value.toLowerCase().includes(normalized));
}

function mergeShipmentPreservingRoute(previous: Shipment | undefined, incoming: Shipment) {
  if (incoming.routeCoordinates.length || !previous?.routeCoordinates.length) {
    return incoming;
  }

  return {
    ...incoming,
    routeCoordinates: previous.routeCoordinates,
  };
}

export function Logistics({ activePage, onNavigate }: LogisticsProps) {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [plannerForm, setPlannerForm] = useState<ShipmentPlannerForm>(defaultForm);
  const [routePlan, setRoutePlan] = useState<LogisticsRoutePlan | null>(null);
  const [planError, setPlanError] = useState<string | null>(null);
  const [pageError, setPageError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [trackingLogs, setTrackingLogs] = useState<TrackingLog[]>([]);
  const [selectedShipmentId, setSelectedShipmentId] = useState<number | null>(null);
  const [isPlanning, setIsPlanning] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [startingShipmentId, setStartingShipmentId] = useState<number | null>(null);
  const [isLoadingShipments, setIsLoadingShipments] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isSocketLive, setIsSocketLive] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const routeOutputRef = useRef<HTMLDivElement | null>(null);
  const selectedShipmentIdRef = useRef<number | null>(null);

  const [drivers, setDrivers] = useState<{ id: number; name: string }[]>([]);
  const [logisticsOrderId, setLogisticsOrderId] = useState<number | undefined>();

  const selectedShipment = shipments.find((shipment) => shipment.id === selectedShipmentId) ?? null;

  useEffect(() => {
    selectedShipmentIdRef.current = selectedShipmentId;
  }, [selectedShipmentId]);

  useEffect(() => {
    const pendingOrderStr = sessionStorage.getItem("pendingLogisticsOrder");
    if (pendingOrderStr) {
      try {
        const payload = JSON.parse(pendingOrderStr);
        setPlannerForm((prev) => ({
          ...prev,
          origin: "MIDC Amravati",
          destination: payload.destination || "",
          productName: payload.productName || "",
          quantity: payload.quantity ? payload.quantity.toString() : "",
          loadType: "STANDARD",
        }));
        if (payload.logisticsOrderId) {
            setLogisticsOrderId(payload.logisticsOrderId);
        }
        sessionStorage.removeItem("pendingLogisticsOrder");
      } catch (e) {
        console.error("Failed to parse pending logistics order", e);
      }
    }

    // Fetch drivers for dropdown
    fetch("http://127.0.0.1:8000/api/drivers")
      .then(res => res.json())
      .then(data => setDrivers(data))
      .catch(console.error);

  }, []);

  const fetchShipments = useCallback(async (signal?: AbortSignal) => {
    try {
      const response = await logisticsService.listShipments(signal);
      setShipments((current) => {
        const currentById = new Map(current.map((shipment) => [shipment.id, shipment]));
        return response.map((shipment) => mergeShipmentPreservingRoute(currentById.get(shipment.id), shipment));
      });
      setLastUpdated(new Date());
      setPageError(null);
      const activeShipmentId = selectedShipmentIdRef.current;
      if (activeShipmentId !== null && !response.some((shipment) => shipment.id === activeShipmentId)) {
        setSelectedShipmentId(null);
        setTrackingLogs([]);
      }
    } catch (error) {
      if (signal?.aborted) return;
      const message = error instanceof Error ? error.message : "Failed to load shipments";
      setPageError(message);
    } finally {
      setIsLoadingShipments(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void fetchShipments(controller.signal);

    const interval = window.setInterval(() => {
      void fetchShipments();
    }, 20000);

    return () => {
      controller.abort();
      window.clearInterval(interval);
    };
  }, [fetchShipments]);

  useEffect(() => {
    if (!selectedShipmentId) {
      setTrackingLogs([]);
      setIsSocketLive(false);
      socketRef.current?.close();
      socketRef.current = null;
      return;
    }

    const controller = new AbortController();
    void logisticsService
      .getTracking(selectedShipmentId, controller.signal)
      .then((response) => {
        setTrackingLogs(response.logs);
        setShipments((current) =>
          current.map((shipment) =>
            shipment.id === response.shipment.id
              ? mergeShipmentPreservingRoute(shipment, response.shipment)
              : shipment,
          ),
        );
      })
      .catch((error) => {
        if (controller.signal.aborted) return;
        setPageError(error instanceof Error ? error.message : "Failed to load tracking history");
      });

    return () => controller.abort();
  }, [selectedShipmentId]);

  useEffect(() => {
    socketRef.current?.close();
    socketRef.current = null;
    setIsSocketLive(false);

    if (!selectedShipmentId || selectedShipment?.status !== "IN_TRANSIT") {
      return;
    }

    const socket = new WebSocket(logisticsService.getShipmentSocketUrl(selectedShipmentId));
    socketRef.current = socket;

    socket.onopen = () => setIsSocketLive(true);
    socket.onclose = () => setIsSocketLive(false);
    socket.onerror = () => setIsSocketLive(false);
    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as LogisticsSocketMessage;
        setShipments((current) =>
          current.map((shipment) =>
            shipment.id === message.shipment.id
              ? mergeShipmentPreservingRoute(shipment, message.shipment)
              : shipment,
          ),
        );
        setTrackingLogs(message.tracking);
        setLastUpdated(new Date());
        if (message.type === "shipment.delivered") {
          setStatusMessage(`Shipment ${message.shipment.trackingId} has been delivered.`);
        }
      } catch {
        setPageError("Received an invalid shipment update from the live socket.");
      }
    };

    return () => {
      socket.close();
    };
  }, [selectedShipmentId, selectedShipment?.status]);

  const filteredShipments = useMemo(
    () => shipments.filter((shipment) => matchesShipmentSearch(shipment, searchTerm)),
    [searchTerm, shipments],
  );

  const activeShipments = filteredShipments.filter((shipment) => shipment.status !== "DELIVERED");

  const scrollToRouteOutput = () => {
    window.requestAnimationFrame(() => {
      routeOutputRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      routeOutputRef.current?.focus({ preventScroll: true });
    });
  };

  const handleFormChange = (field: keyof ShipmentPlannerForm, value: string) => {
    setPlannerForm((current) => ({ ...current, [field]: value }));
    setRoutePlan(null);
    setPlanError(null);
    setStatusMessage(null);
  };

  const handlePlanRoute = async () => {
    if (!plannerForm.origin.trim() || !plannerForm.destination.trim()) {
      setPlanError("Origin and destination are required before calculating a route.");
      return;
    }

    setIsPlanning(true);
    setPlanError(null);
    setStatusMessage(null);

    try {
      const response = await logisticsService.planRoute({
        origin: plannerForm.origin.trim(),
        destination: plannerForm.destination.trim(),
        load_type: plannerForm.loadType,
        origin_lat: toOptionalNumber(plannerForm.originLat),
        origin_lng: toOptionalNumber(plannerForm.originLng),
        dest_lat: toOptionalNumber(plannerForm.destLat),
        dest_lng: toOptionalNumber(plannerForm.destLng),
      });
      setRoutePlan(response);
      setStatusMessage("Route planned successfully. You can create the shipment now.");
      scrollToRouteOutput();
    } catch (error) {
      setRoutePlan(null);
      setPlanError(error instanceof Error ? error.message : "Route planning failed");
      scrollToRouteOutput();
    } finally {
      setIsPlanning(false);
    }
  };

  const handleCreateShipment = async () => {
    if (!plannerForm.origin.trim() || !plannerForm.destination.trim()) {
      setPlanError("Origin and destination are required before creating a shipment.");
      return;
    }
    if (!plannerForm.driverId) {
      setPlanError("Please select a driver to assign this schedule to.");
      return;
    }
    if (!plannerForm.productName || !plannerForm.quantity) {
        setPlanError("Please provide product name and quantity for the schedule request.");
        return;
    }

    setIsCreating(true);
    setPlanError(null);
    setPageError(null);
    setStatusMessage(null);

    try {
      const shipment = await logisticsService.createShipment({
        origin: plannerForm.origin.trim(),
        destination: plannerForm.destination.trim(),
        load_type: plannerForm.loadType,
        origin_lat: toOptionalNumber(plannerForm.originLat),
        origin_lng: toOptionalNumber(plannerForm.originLng),
        dest_lat: toOptionalNumber(plannerForm.destLat),
        dest_lng: toOptionalNumber(plannerForm.destLng),
        driver_id: parseInt(plannerForm.driverId)
      });

      // Create Driver Schedule Request
      const driver = drivers.find(d => d.id.toString() === plannerForm.driverId);
      if (driver) {
          await logisticsService.createSchedule({
              origin: plannerForm.origin.trim(),
              destination: plannerForm.destination.trim(),
              load_type: plannerForm.loadType,
              distance_km: routePlan?.distance_km,
              eta_hours: routePlan?.eta_hours,
              driver_id: driver.id,
              product_name: plannerForm.productName,
              quantity: parseInt(plannerForm.quantity),
              carrier_type: plannerForm.loadType,
              logistics_order_id: logisticsOrderId,
              shipment_id: shipment.id
          });
      }

      setShipments((current) => [shipment, ...current]);
      setSelectedShipmentId(shipment.id);
      setStatusMessage(`Shipment created and Schedule sent to Driver ${driver?.name || ""}.`);
      setLastUpdated(new Date());
    } catch (error) {
      setPageError(error instanceof Error ? error.message : "Shipment creation failed");
    } finally {
      setIsCreating(false);
    }
  };

  const handleStartShipment = async (shipment: Shipment) => {
    setStartingShipmentId(shipment.id);
    setPageError(null);
    setStatusMessage(null);

    try {
      const updatedShipment = await logisticsService.startShipment(shipment.id);
      setShipments((current) =>
        current.map((item) => (item.id === updatedShipment.id ? updatedShipment : item)),
      );
      setSelectedShipmentId(updatedShipment.id);
      setStatusMessage(`Shipment ${updatedShipment.trackingId} is now in transit with live tracking enabled.`);
      setLastUpdated(new Date());
    } catch (error) {
      setPageError(error instanceof Error ? error.message : "Shipment start failed");
    } finally {
      setStartingShipmentId(null);
    }
  };

  const handleTrackShipment = (shipment: Shipment) => {
    setSelectedShipmentId(shipment.id);
    setStatusMessage(`Subscribed to live tracking for ${shipment.trackingId}.`);
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(14,165,233,0.12),_transparent_34%),linear-gradient(180deg,#f8fbff_0%,#eef4fb_100%)] text-on-surface">
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setSidebarOpen(false)}
        activePage={activePage}
        onNavigate={onNavigate}
      />

      <main className="min-h-screen lg:ml-[240px]">
        <Header
          title="Logistics Command Center"
          lastUpdated={lastUpdated}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          onRefresh={() => void fetchShipments()}
          onMenuClick={() => setSidebarOpen(true)}
          searchPlaceholder="Search shipments..."
          showRefresh={false}
          showHelp
        />

        <div className="space-y-8 p-4 sm:p-6 lg:p-8">
          {statusMessage ? (
            <section className="rounded-3xl border border-emerald-200 bg-emerald-50 px-5 py-4 text-sm text-emerald-800 shadow-sm">
              {statusMessage}
            </section>
          ) : null}

          {pageError ? (
            <section className="rounded-3xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-800 shadow-sm">
              {pageError}
            </section>
          ) : null}

          <section className="grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_420px]">
            <RouteForm
              form={plannerForm}
              onChange={handleFormChange}
              onPlan={handlePlanRoute}
              onCreate={handleCreateShipment}
              isPlanning={isPlanning}
              isCreating={isCreating}
              canCreate={!!routePlan}
              drivers={drivers}
            />
            <div ref={routeOutputRef} tabIndex={-1} className="outline-none">
              <RouteInsights plan={routePlan} error={planError} />
            </div>
          </section>

          <section className="space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-l font-bold uppercase tracking-[0.24em] text-sky-600">Active shipment cards</p>
                <h2 className="mt-2 text-2xl font-bold text-slate-950"></h2>
              </div>
            </div>

            {isLoadingShipments ? (
              <div className="grid gap-4 xl:grid-cols-2">
                {Array.from({ length: 2 }).map((_, index) => (
                  <div key={index} className="h-[320px] animate-pulse rounded-[28px] bg-white/70 shadow-sm" />
                ))}
              </div>
            ) : activeShipments.length ? (
              <div className="grid gap-4 xl:grid-cols-2">
                {activeShipments.map((shipment) => (
                  <ShipmentCard
                    key={shipment.id}
                    shipment={shipment}
                    onTrack={handleTrackShipment}
                    onStart={handleStartShipment}
                    isStarting={startingShipmentId === shipment.id}
                    isActive={selectedShipmentId === shipment.id}
                  />
                ))}
              </div>
            ) : (
              <div className="rounded-[28px] border border-dashed border-slate-300 bg-white/70 px-6 py-10 text-center shadow-sm">
                <p className="text-sm font-semibold text-slate-900">No active shipments match this view.</p>
                <p className="mt-2 text-sm text-slate-600">
                  Create a route above to save a shipment, or adjust the search field to see more records.
                </p>
              </div>
            )}
          </section>

          <TrackingMap shipment={selectedShipment} tracking={trackingLogs} isLive={isSocketLive} />
        </div>
      </main>
    </div>
  );
}

// anything
