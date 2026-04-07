import { useState } from "react";
import { Header } from "../components/layout/Header";
import { Sidebar } from "../components/layout/Sidebar";
import { InsightCard } from "../components/procurement/InsightCard";
import { InsightFilterTabs } from "../components/procurement/InsightFilterTabs";
import { ManageSuppliersView } from "../components/procurement/ManageSuppliersView";
import { ProcurementHero } from "../components/procurement/ProcurementHero";
import { PurchaseOrderPreviewModal } from "../components/procurement/PurchaseOrderPreviewModal";
import { PurchaseOrderCard } from "../components/procurement/PurchaseOrderCard";
import { SpendOptimizationCard } from "../components/procurement/SpendOptimizationCard";
import { SupplierStatCard } from "../components/procurement/SupplierStatCard";
import { SupplierTable } from "../components/procurement/SupplierTable";
import { TopPerformerCard } from "../components/procurement/TopPerformerCard";
import { useProcurementData } from "../hooks/useProcurementData";
import { usePurchaseOrder } from "../hooks/usePurchaseOrder";
import type { AppPage } from "../types/app.types";
import { filterInsights, matchesProcurementQuery } from "../utils/procurement";

type InsightFilter = "all" | "urgent" | "high";
type SupplierWorkspaceTab = "analytics" | "manage";

function HeroSkeleton() {
  return <div className="h-[260px] animate-pulse rounded-[1.5rem] bg-surface-container-high" />;
}

function InsightSkeleton() {
  return <div className="h-[420px] animate-pulse rounded-xl bg-surface-container-high" />;
}

function SupplierSkeleton() {
  return <div className="h-[320px] animate-pulse rounded-xl bg-surface-container-high" />;
}

function PurchaseOrderSkeleton() {
  return <div className="h-[160px] animate-pulse rounded-xl bg-surface-container-high" />;
}

interface ProcurementIntelligenceProps {
  activePage: AppPage;
  onNavigate: (page: AppPage) => void;
}

export function ProcurementIntelligence({
  activePage,
  onNavigate,
}: ProcurementIntelligenceProps) {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [insightFilter, setInsightFilter] = useState<InsightFilter>("all");
  const [supplierWorkspaceTab, setSupplierWorkspaceTab] = useState<SupplierWorkspaceTab>("analytics");
  const {
    summary,
    insights,
    supplierOverview,
    supplierRows,
    topPerformers,
    spendOptimization,
    purchaseOrders,
    isLoading,
    error,
    lastUpdated,
    refetch,
  } = useProcurementData();
  const purchaseOrder = usePurchaseOrder({
    onCreated: refetch,
    onUpdated: refetch,
  });

  const visibleInsights = filterInsights(insights, insightFilter).filter((insight) =>
    matchesProcurementQuery(searchTerm, [
      insight.sku,
      insight.title,
      insight.priority,
      insight.supplierName,
      insight.reasoning,
    ]),
  );

  const visibleSuppliers = supplierRows.filter((supplier) =>
    matchesProcurementQuery(searchTerm, [
      supplier.name,
      supplier.location,
      supplier.verdict,
      supplier.score,
    ]),
  );

  const visiblePerformers = topPerformers.filter((performer) =>
    matchesProcurementQuery(searchTerm, [performer.name, performer.metricLabel, performer.score]),
  );

  const recentPurchaseOrders = purchaseOrders
    .filter((order) =>
      matchesProcurementQuery(searchTerm, [
        order.poNumber,
        order.title,
        order.supplierName,
        order.status,
        order.priority,
      ]),
    )
    .slice(0, 4);

  const draftCount = purchaseOrders.filter((order) => order.lifecycleStage === "draft").length;
  const approvedCount = purchaseOrders.filter((order) => order.lifecycleStage === "approved").length;
  const inTransitCount = purchaseOrders.filter((order) => order.lifecycleStage === "in_transit").length;

  async function goToPurchaseOrdersPage() {
    onNavigate("purchaseOrders");
  }

  const purchaseOrderSummaryCount = recentPurchaseOrders.length;

  return (
    <div className="min-h-screen bg-background text-on-surface">
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setSidebarOpen(false)}
        activePage={activePage}
        onNavigate={onNavigate}
      />

      <main className="min-h-screen lg:ml-[240px]">
        <Header
          title="Procurement Intelligence"
          lastUpdated={lastUpdated}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          onRefresh={refetch}
          onMenuClick={() => setSidebarOpen(true)}
          searchPlaceholder={
            supplierWorkspaceTab === "manage"
              ? "Search suppliers, products, or locations..."
              : "Search POs, SKU, or Suppliers..."
          }
          showRefresh={false}
          showHelp
        />

        <div className="space-y-8 p-4 sm:p-6 lg:p-8">
          {error ? (
            <section className="rounded-2xl border border-error/20 bg-error-container/60 p-6 shadow-panel">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 className="text-lg font-bold text-error">Procurement data unavailable</h3>
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

          {purchaseOrder.error ? (
            <section className="rounded-2xl border border-error/20 bg-error-container/70 p-5 shadow-panel">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 className="text-sm font-bold uppercase tracking-[0.18em] text-error">Purchase Order Workflow</h3>
                  <p className="mt-2 text-sm text-on-error-container">{purchaseOrder.error}</p>
                </div>
              </div>
            </section>
          ) : null}

          {isLoading || !summary ? <HeroSkeleton /> : <ProcurementHero summary={summary} />}

          <section className="rounded-[1.5rem] bg-surface-container-lowest p-2 shadow-sm">
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setSupplierWorkspaceTab("analytics")}
                className={`rounded-[1rem] px-4 py-3 text-sm font-semibold transition ${
                  supplierWorkspaceTab === "analytics"
                    ? "bg-primary text-white shadow-sm"
                    : "text-on-surface-variant hover:bg-surface-container-low"
                }`}
              >
                Performance Analytics
              </button>
              <button
                type="button"
                onClick={() => setSupplierWorkspaceTab("manage")}
                className={`rounded-[1rem] px-4 py-3 text-sm font-semibold transition ${
                  supplierWorkspaceTab === "manage"
                    ? "bg-primary text-white shadow-sm"
                    : "text-on-surface-variant hover:bg-surface-container-low"
                }`}
              >
                Manage Suppliers
              </button>
            </div>
          </section>

          {supplierWorkspaceTab === "manage" ? (
            <ManageSuppliersView
              searchTerm={searchTerm}
              onSearchChange={setSearchTerm}
              onSupplierMutated={refetch}
            />
          ) : (
            <>
              <section className="space-y-6">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                  <div className="space-y-1">
                    <h3 className="text-[1.75rem] font-bold text-on-surface">AI Procurement Insights</h3>
                    <p className="text-lg text-on-surface-variant">
                      Optimized stock replenishment and risk mitigation
                    </p>
                  </div>
                  <InsightFilterTabs activeFilter={insightFilter} onChange={setInsightFilter} />
                </div>

                <div className="grid gap-6 xl:grid-cols-3">
                  {isLoading
                    ? Array.from({ length: 3 }).map((_, index) => <InsightSkeleton key={index} />)
                    : visibleInsights.slice(0, 3).map((insight) => (
                        <InsightCard
                          key={insight.id}
                          insight={insight}
                          onQuickPO={purchaseOrder.createFromInsight}
                          isCreatingPurchaseOrder={purchaseOrder.creatingInsightId === insight.id}
                        />
                      ))}
                </div>

                {!isLoading && visibleInsights.length === 0 ? (
                  <div className="rounded-xl border border-dashed border-outline-variant/40 bg-surface-container-low px-6 py-10 text-center">
                    <p className="text-sm font-semibold text-on-surface">No procurement insights match this view.</p>
                    <p className="mt-1 text-sm text-on-surface-variant">
                      Adjust the filter or search to see more recommendations.
                    </p>
                  </div>
                ) : null}
              </section>

              <section className="grid gap-8 lg:grid-cols-12">
                <div className="space-y-6 lg:col-span-8">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <h3 className="text-[1.75rem] font-bold text-on-surface">Supplier Network</h3>
                      <p className="mt-1 text-base text-on-surface-variant">
                        Performance signals across your most important procurement partners
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setSupplierWorkspaceTab("manage")}
                      className="inline-flex items-center justify-center rounded-full border border-outline-variant/40 bg-surface-container-lowest px-4 py-2 text-xs font-bold uppercase tracking-[0.18em] text-primary transition hover:bg-surface-container-high"
                    >
                      Open Supplier Workspace
                    </button>
                  </div>

                  <div className="grid gap-4 md:grid-cols-4">
                    {isLoading || !supplierOverview ? (
                      Array.from({ length: 4 }).map((_, index) => <SupplierSkeleton key={index} />)
                    ) : (
                      <>
                        <SupplierStatCard label="Avg Reliability" value={`${supplierOverview.avgReliability}%`} />
                        <SupplierStatCard label="On-time Delivery" value={`${supplierOverview.onTimeDelivery}%`} />
                        <SupplierStatCard label="Quality Rate" value={`${supplierOverview.qualityRate}%`} />
                        <SupplierStatCard label="ESG Compliance" value={supplierOverview.esgCompliance} />
                      </>
                    )}
                  </div>

                  {isLoading ? <SupplierSkeleton /> : <SupplierTable rows={visibleSuppliers} />}
                </div>

                <div className="space-y-6 lg:col-span-4">
                  {isLoading ? <SupplierSkeleton /> : <TopPerformerCard performers={visiblePerformers} />}
                  {isLoading || !spendOptimization ? (
                    <SupplierSkeleton />
                  ) : (
                    <SpendOptimizationCard spendOptimization={spendOptimization} />
                  )}
                </div>
              </section>

              <section className="space-y-6">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                  <div className="space-y-1">
                    <h3 className="text-[1.75rem] font-bold text-on-surface">Purchase Orders</h3>
                    <p className="text-lg text-on-surface-variant">Latest purchase orders and lifecycle tracking</p>
                  </div>

                  <div className="flex flex-wrap items-center gap-3">
                    <div className="flex items-center gap-2 rounded-full bg-surface-container-lowest px-3 py-1 shadow-sm">
                      <span className="h-2 w-2 rounded-full bg-primary" />
                      <span className="text-[10px] font-bold uppercase tracking-[0.18em]">{draftCount} Drafts</span>
                    </div>
                    <div className="flex items-center gap-2 rounded-full bg-surface-container-lowest px-3 py-1 shadow-sm">
                      <span className="h-2 w-2 rounded-full bg-orange-400" />
                      <span className="text-[10px] font-bold uppercase tracking-[0.18em]">{approvedCount} Pending</span>
                    </div>
                    <div className="flex items-center gap-2 rounded-full bg-surface-container-lowest px-3 py-1 shadow-sm">
                      <span className="h-2 w-2 rounded-full bg-emerald-500" />
                      <span className="text-[10px] font-bold uppercase tracking-[0.18em]">{inTransitCount} In-Transit</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => void goToPurchaseOrdersPage()}
                      className="inline-flex items-center justify-center rounded-full border border-outline-variant/40 bg-surface-container-lowest px-4 py-2 text-xs font-bold uppercase tracking-[0.18em] text-primary transition hover:bg-surface-container-high"
                    >
                      View All
                    </button>
                  </div>
                </div>

                <div className="space-y-4">
                  {isLoading
                    ? Array.from({ length: 2 }).map((_, index) => <PurchaseOrderSkeleton key={index} />)
                    : recentPurchaseOrders.map((order) => (
                        <PurchaseOrderCard
                          key={order.id}
                          order={order}
                          onViewDetails={(orderId) => void purchaseOrder.openPreview(orderId)}
                        />
                      ))}

                  {!isLoading && recentPurchaseOrders.length > 0 ? (
                    <div className="flex items-center justify-between rounded-xl border border-outline-variant/20 bg-surface-container-low px-4 py-3">
                      <p className="text-sm text-on-surface-variant">
                        Showing the latest {purchaseOrderSummaryCount} purchase orders for quick review.
                      </p>
                      <button
                        type="button"
                        onClick={() => void goToPurchaseOrdersPage()}
                        className="text-sm font-semibold text-primary transition hover:underline"
                      >
                        Show Full List
                      </button>
                    </div>
                  ) : null}

                  {!isLoading && recentPurchaseOrders.length === 0 ? (
                    <div className="rounded-xl border border-dashed border-outline-variant/40 bg-surface-container-low px-6 py-10 text-center">
                      <p className="text-sm font-semibold text-on-surface">No purchase orders match this search.</p>
                      <p className="mt-1 text-sm text-on-surface-variant">
                        Try a different SKU, supplier, or PO number to broaden the results.
                      </p>
                    </div>
                  ) : null}
                </div>
              </section>
            </>
          )}
        </div>
      </main>

      <PurchaseOrderPreviewModal
        isOpen={purchaseOrder.isPreviewOpen}
        order={purchaseOrder.activeOrder}
        isLoading={purchaseOrder.isLoadingOrder}
        isDownloading={purchaseOrder.isDownloadingPdf}
        isApproving={purchaseOrder.isUpdatingStatus}
        onClose={purchaseOrder.closePreview}
        onDownload={() => void purchaseOrder.downloadPdf()}
        onApprove={() => void purchaseOrder.approvePurchaseOrder()}
      />
    </div>
  );
}
