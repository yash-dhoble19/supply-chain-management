import { useState } from "react";
import { ActivityItem } from "../components/dashboard/ActivityItem";
import { MetricCard } from "../components/dashboard/MetricCard";
import { SectionCard } from "../components/dashboard/SectionCard";
import { ShipmentCard } from "../components/dashboard/ShipmentCard";
import { StatsCard } from "../components/dashboard/StatsCard";
import { TopInventoryTable } from "../components/dashboard/TopInventoryTable";
import { Header } from "../components/layout/Header";
import { Sidebar } from "../components/layout/Sidebar";
import { useDashboardData } from "../hooks/useDashboardData";
import { matchesDashboardQuery } from "../utils/formatters";

function MetricSkeleton() {
  return <div className="h-[156px] animate-pulse rounded-xl bg-surface-container-high" />;
}

function ShipmentSkeleton() {
  return <div className="h-[176px] animate-pulse rounded-xl bg-surface-container-low" />;
}

function ActivitySkeleton() {
  return <div className="h-16 animate-pulse rounded-xl bg-surface-container-low" />;
}

function StatsSkeleton() {
  return <div className="h-24 animate-pulse rounded-xl bg-surface-container-low" />;
}

function OverviewSkeleton() {
  return <div className="h-[280px] animate-pulse rounded-xl bg-surface-container-high" />;
}

function SnapshotGroup({
  title,
  items,
}: {
  title: string;
  items: Array<{ id: string; label: string; value: number; tone: string }>;
}) {
  const toneStyles: Record<string, string> = {
    primary: "bg-primary-fixed text-on-primary-fixed",
    warning: "bg-amber-100 text-amber-800",
    success: "bg-green-100 text-green-800",
    danger: "bg-red-100 text-red-800",
    neutral: "bg-slate-100 text-slate-700",
  };

  return (
    <div className="rounded-xl border border-outline-variant/10 bg-surface-container-low p-5">
      <h4 className="text-sm font-bold uppercase tracking-[0.18em] text-on-surface-variant">{title}</h4>
      <div className="mt-4 flex flex-wrap gap-3">
        {items.length ? (
          items.map((item) => (
            <div key={item.id} className={`min-w-[120px] rounded-2xl px-4 py-3 ${toneStyles[item.tone] || toneStyles.neutral}`}>
              <div className="text-xs font-semibold uppercase tracking-[0.16em] opacity-80">{item.label}</div>
              <div className="mt-1 text-2xl font-bold leading-none">{item.value}</div>
            </div>
          ))
        ) : (
          <div className="rounded-2xl bg-slate-100 px-4 py-3 text-sm font-medium text-slate-600">No live data</div>
        )}
      </div>
    </div>
  );
}

export function Dashboard() {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [visibleShipments, setVisibleShipments] = useState(4);
  const { metrics, shipments, activities, stats, overview, isLoading, error, lastUpdated, refetch } =
    useDashboardData();

  const filteredShipments = shipments.filter((shipment) =>
    matchesDashboardQuery(searchTerm, [
      shipment.trackingNumber,
      shipment.source,
      shipment.destination,
      shipment.status,
      shipment.detail,
    ]),
  );

  const filteredActivities = activities.filter((activity) =>
    matchesDashboardQuery(searchTerm, [activity.title, activity.description, activity.type]),
  );
  const visibleActivities = filteredActivities.slice(0, 6);

  const visibleShipmentItems = filteredShipments.slice(0, visibleShipments);
  const canLoadMoreShipments = visibleShipments < filteredShipments.length;
  const nextLoadCount = Math.min(4, filteredShipments.length - visibleShipments);

  return (
    <div className="min-h-screen bg-background text-on-surface">
      <Sidebar isOpen={isSidebarOpen} onClose={() => setSidebarOpen(false)} />

      <main className="min-h-screen lg:ml-[240px]">
        <Header
          lastUpdated={lastUpdated}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          onRefresh={refetch}
          onMenuClick={() => setSidebarOpen(true)}
        />

        <div className="space-y-8 p-4 sm:p-6 lg:p-8">
          {error ? (
            <section className="rounded-2xl border border-error/20 bg-error-container/60 p-6 shadow-panel">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 className="text-lg font-bold text-error">Dashboard data unavailable</h3>
                  <p className="mt-2 text-sm text-on-error-container">
                    {error}. Check the FastAPI server and database connection, then retry.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={refetch}
                  className="inline-flex items-center justify-center rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
                >
                  Retry
                </button>
              </div>
            </section>
          ) : null}

          <section className="grid gap-6 sm:grid-cols-2 xl:grid-cols-5">
            {isLoading
              ? Array.from({ length: 5 }).map((_, index) => <MetricSkeleton key={index} />)
              : metrics.map((metric) => <MetricCard key={metric.id} metric={metric} />)}
          </section>

          <section className="grid items-start gap-8 xl:grid-cols-[minmax(0,1.18fr)_minmax(360px,0.82fr)]">
            <SectionCard
              title="Real-time Shipment Tracking"
              description="Monitoring global logistics flow and transit milestones"
              className="self-start"
              action={
                <div className="flex flex-wrap items-center gap-4">
                  <div className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded bg-primary" />
                    <span className="text-[10px] font-bold uppercase text-on-surface-variant">On Track</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded bg-tertiary" />
                    <span className="text-[10px] font-bold uppercase text-on-surface-variant">Risk of Delay</span>
                  </div>
                </div>
              }
            >
              <div className="grid gap-4 2xl:grid-cols-2">
                {isLoading
                  ? Array.from({ length: 4 }).map((_, index) => <ShipmentSkeleton key={index} />)
                  : visibleShipmentItems.map((shipment) => (
                      <ShipmentCard key={shipment.id} shipment={shipment} />
                    ))}
              </div>

              {!isLoading && filteredShipments.length === 0 ? (
                <div className="rounded-xl border border-dashed border-outline-variant/40 bg-surface-container-low px-6 py-10 text-center">
                  <p className="text-sm font-semibold text-on-surface">No shipments match this view.</p>
                  <p className="mt-1 text-sm text-on-surface-variant">
                    Try a different search or add shipment data in the backend.
                  </p>
                </div>
              ) : null}

              {canLoadMoreShipments ? (
                <div className="mt-8 flex justify-center">
                  <button
                    type="button"
                    onClick={() => setVisibleShipments((current) => current + 4)}
                    className="rounded-lg border border-outline-variant px-6 py-2 text-sm font-bold text-on-surface-variant transition-all hover:bg-surface-container-high"
                  >
                    Load {nextLoadCount} More Shipments
                  </button>
                </div>
              ) : null}
            </SectionCard>

            <div className="flex max-h-[640px] flex-col self-start rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-sm">
              <h3 className="mb-6 text-lg font-bold text-on-surface">Recent Activity</h3>
              <div className="scrollbar-subtle flex-1 space-y-6 overflow-y-auto pr-1">
                {isLoading
                  ? Array.from({ length: 5 }).map((_, index) => <ActivitySkeleton key={index} />)
                  : visibleActivities.map((activity) => (
                      <ActivityItem key={activity.id} activity={activity} />
                    ))}
              </div>

              {!isLoading && visibleActivities.length === 0 ? (
                <div className="rounded-xl border border-dashed border-outline-variant/40 bg-surface-container-low px-4 py-6 text-center">
                  <p className="text-sm font-semibold text-on-surface">No recent activity found.</p>
                  <p className="mt-1 text-sm text-on-surface-variant">
                    Activity updates will appear here as orders, shipments, and inventory logs change.
                  </p>
                </div>
              ) : null}

              <button
                type="button"
                onClick={refetch}
                className="mt-6 flex items-center gap-1 text-sm font-bold text-primary transition hover:underline"
              >
                Refresh activity <span className="material-symbols-outlined text-xs">arrow_forward</span>
              </button>
            </div>
          </section>

          <section className="grid items-start gap-8 xl:grid-cols-[minmax(0,1.45fr)_minmax(340px,1fr)]">
            {isLoading || !overview ? (
              <>
                <OverviewSkeleton />
                <OverviewSkeleton />
              </>
            ) : (
              <>
                <SectionCard
                  title="Inventory Exposure"
                  description="Highest-value stock positions and where working capital is concentrated."
                >
                  <TopInventoryTable items={overview.topInventory} />
                </SectionCard>

                <div className="space-y-8">
                  <SectionCard
                    title="Operations Snapshot"
                    description="Compact live summary of health, flow, and procurement pressure."
                  >
                    <div className="space-y-4">
                      <SnapshotGroup title="Inventory Health" items={overview.inventoryStatus} />
                      <SnapshotGroup title="Shipment Status" items={overview.shipmentStatus} />
                      <SnapshotGroup title="Purchase Orders" items={overview.purchaseOrderStatus} />
                    </div>
                  </SectionCard>
                </div>
              </>
            )}
          </section>

          <section className="grid gap-8 lg:grid-cols-3">
            {isLoading
              ? Array.from({ length: 3 }).map((_, index) => <StatsSkeleton key={index} />)
              : stats.map((stat) => <StatsCard key={stat.id} stat={stat} />)}
          </section>
        </div>
      </main>
    </div>
  );
}
