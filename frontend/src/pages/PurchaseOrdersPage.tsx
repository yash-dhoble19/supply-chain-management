import { useEffect, useMemo, useState } from "react";
import { Header } from "../components/layout/Header";
import { Sidebar } from "../components/layout/Sidebar";
import { PurchaseOrderPreviewModal } from "../components/procurement/PurchaseOrderPreviewModal";
import { PurchaseOrderCard } from "../components/procurement/PurchaseOrderCard";
import { usePurchaseOrder } from "../hooks/usePurchaseOrder";
import { procurementService } from "../services/procurementService";
import type { AppPage } from "../types/app.types";
import type { PurchaseOrder, SupplierRow } from "../types/procurement.types";

type DateFilter = "all" | "today" | "7d" | "30d" | "custom";
type SortOrder = "latest" | "oldest";

interface PurchaseOrdersPageProps {
  activePage: AppPage;
  onNavigate: (page: AppPage) => void;
}

function PurchaseOrderPageSkeleton() {
  return <div className="h-[156px] animate-pulse rounded-xl bg-surface-container-high" />;
}

export function PurchaseOrdersPage({ activePage, onNavigate }: PurchaseOrdersPageProps) {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [supplierFilter, setSupplierFilter] = useState("all");
  const [dateFilter, setDateFilter] = useState<DateFilter>("all");
  const [customStartDate, setCustomStartDate] = useState("");
  const [customEndDate, setCustomEndDate] = useState("");
  const [sortOrder, setSortOrder] = useState<SortOrder>("latest");
  const [currentPage, setCurrentPage] = useState(1);
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrder[]>([]);
  const [supplierOptions, setSupplierOptions] = useState<SupplierRow[]>([]);
  const [isLoading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [reloadToken, setReloadToken] = useState(0);
  const purchaseOrder = usePurchaseOrder({
    onUpdated: () => setReloadToken((value) => value + 1),
  });

  const pageSize = 20;

  const hasNextPage = purchaseOrders.length === pageSize;

  const filterSummary = useMemo(() => {
    const parts = [];
    if (statusFilter !== "all") parts.push(`Status: ${statusFilter}`);
    if (priorityFilter !== "all") parts.push(`Priority: ${priorityFilter}`);
    if (supplierFilter !== "all") parts.push(`Supplier: ${supplierFilter}`);
    if (dateFilter !== "all") parts.push(`Date: ${dateFilter}`);
    if (sortOrder !== "latest") parts.push(`Sort: ${sortOrder}`);
    return parts.join(" • ");
  }, [dateFilter, priorityFilter, sortOrder, statusFilter, supplierFilter]);

  useEffect(() => {
    const controller = new AbortController();

    async function loadPurchaseOrders() {
      setLoading(true);
      setError(null);

      try {
        const [orders, supplierOverview] = await Promise.all([
          procurementService.getPurchaseOrders(
            {
              page: currentPage,
              limit: pageSize,
              status: statusFilter !== "all" ? statusFilter : undefined,
              priority: priorityFilter !== "all" ? priorityFilter : undefined,
              supplier: supplierFilter !== "all" ? supplierFilter : undefined,
              search: searchTerm || undefined,
              dateRange: dateFilter !== "all" && dateFilter !== "custom" ? dateFilter : undefined,
              startDate: dateFilter === "custom" && customStartDate ? customStartDate : undefined,
              endDate: dateFilter === "custom" && customEndDate ? customEndDate : undefined,
              sort: sortOrder,
            },
            controller.signal,
          ),
          procurementService.getSuppliersOverview(controller.signal),
        ]);

        setPurchaseOrders(orders);
        setSupplierOptions(supplierOverview.suppliers);
        setLastUpdated(new Date());
      } catch (requestError) {
        if (controller.signal.aborted) {
          return;
        }
        setError(requestError instanceof Error ? requestError.message : "Unable to load purchase orders.");
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void loadPurchaseOrders();
    return () => controller.abort();
  }, [
    currentPage,
    customEndDate,
    customStartDate,
    dateFilter,
    priorityFilter,
    searchTerm,
    sortOrder,
    statusFilter,
    supplierFilter,
    reloadToken,
  ]);

  function resetFilters() {
    setStatusFilter("all");
    setPriorityFilter("all");
    setSupplierFilter("all");
    setDateFilter("all");
    setCustomStartDate("");
    setCustomEndDate("");
    setSortOrder("latest");
    setSearchTerm("");
    setCurrentPage(1);
  }

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
          title="Purchase Orders"
          lastUpdated={lastUpdated}
          searchTerm={searchTerm}
          onSearchChange={(value) => {
            setSearchTerm(value);
            setCurrentPage(1);
          }}
          onRefresh={() => setReloadToken((value) => value + 1)}
          onMenuClick={() => setSidebarOpen(true)}
          searchPlaceholder="Search PO number, item, or supplier..."
          showRefresh={false}
          showHelp
        />

        <div className="space-y-8 p-4 sm:p-6 lg:p-8">
          <section className="rounded-[24px] bg-surface-container-lowest p-6 shadow-panel">
            <div className="flex flex-col gap-6">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-on-surface-variant">
                    Procurement Management
                  </p>
                  <h2 className="mt-2 text-[1.75rem] font-bold text-on-surface">Purchase Orders Management View</h2>
                  <p className="mt-2 text-sm text-on-surface-variant">
                    Search, filter, and review the full purchase order lifecycle without crowding the dashboard.
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  <button
                    type="button"
                    onClick={resetFilters}
                    className="rounded-full border border-outline-variant/40 px-4 py-2 text-xs font-bold uppercase tracking-[0.18em] text-on-surface transition hover:bg-surface-container-high"
                  >
                    Reset Filters
                  </button>
                  <button
                    type="button"
                    onClick={() => onNavigate("procurement")}
                    className="rounded-full bg-kinetic px-4 py-2 text-xs font-bold uppercase tracking-[0.18em] text-white transition hover:opacity-95"
                  >
                    Back to Summary
                  </button>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
                <label className="space-y-2">
                  <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-on-surface-variant">Date</span>
                  <select
                    value={dateFilter}
                    onChange={(event) => {
                      setDateFilter(event.target.value as DateFilter);
                      setCurrentPage(1);
                    }}
                    className="w-full rounded-xl border border-outline-variant/30 bg-white px-4 py-3 text-sm outline-none transition focus:border-primary"
                  >
                    <option value="all">All dates</option>
                    <option value="today">Today</option>
                    <option value="7d">Last 7 days</option>
                    <option value="30d">Last 30 days</option>
                    <option value="custom">Custom range</option>
                  </select>
                </label>

                <label className="space-y-2">
                  <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-on-surface-variant">Status</span>
                  <select
                    value={statusFilter}
                    onChange={(event) => {
                      setStatusFilter(event.target.value);
                      setCurrentPage(1);
                    }}
                    className="w-full rounded-xl border border-outline-variant/30 bg-white px-4 py-3 text-sm outline-none transition focus:border-primary"
                  >
                    <option value="all">All statuses</option>
                    <option value="draft">Draft</option>
                    <option value="approved">Approved</option>
                    <option value="in_transit">In Transit</option>
                    <option value="received">Received</option>
                  </select>
                </label>

                <label className="space-y-2">
                  <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-on-surface-variant">Priority</span>
                  <select
                    value={priorityFilter}
                    onChange={(event) => {
                      setPriorityFilter(event.target.value);
                      setCurrentPage(1);
                    }}
                    className="w-full rounded-xl border border-outline-variant/30 bg-white px-4 py-3 text-sm outline-none transition focus:border-primary"
                  >
                    <option value="all">All priorities</option>
                    <option value="urgent">Urgent</option>
                    <option value="high">High</option>
                    <option value="normal">Normal</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </label>

                <label className="space-y-2">
                  <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-on-surface-variant">Supplier</span>
                  <select
                    value={supplierFilter}
                    onChange={(event) => {
                      setSupplierFilter(event.target.value);
                      setCurrentPage(1);
                    }}
                    className="w-full rounded-xl border border-outline-variant/30 bg-white px-4 py-3 text-sm outline-none transition focus:border-primary"
                  >
                    <option value="all">All suppliers</option>
                    {supplierOptions.map((supplier) => (
                      <option key={supplier.id} value={supplier.name}>
                        {supplier.name}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="space-y-2">
                  <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-on-surface-variant">Sort</span>
                  <select
                    value={sortOrder}
                    onChange={(event) => {
                      setSortOrder(event.target.value as SortOrder);
                      setCurrentPage(1);
                    }}
                    className="w-full rounded-xl border border-outline-variant/30 bg-white px-4 py-3 text-sm outline-none transition focus:border-primary"
                  >
                    <option value="latest">Latest first</option>
                    <option value="oldest">Oldest first</option>
                  </select>
                </label>
              </div>

              {dateFilter === "custom" ? (
                <div className="grid gap-4 md:grid-cols-2">
                  <label className="space-y-2">
                    <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-on-surface-variant">Start date</span>
                    <input
                      type="date"
                      value={customStartDate}
                      onChange={(event) => {
                        setCustomStartDate(event.target.value);
                        setCurrentPage(1);
                      }}
                      className="w-full rounded-xl border border-outline-variant/30 bg-white px-4 py-3 text-sm outline-none transition focus:border-primary"
                    />
                  </label>
                  <label className="space-y-2">
                    <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-on-surface-variant">End date</span>
                    <input
                      type="date"
                      value={customEndDate}
                      onChange={(event) => {
                        setCustomEndDate(event.target.value);
                        setCurrentPage(1);
                      }}
                      className="w-full rounded-xl border border-outline-variant/30 bg-white px-4 py-3 text-sm outline-none transition focus:border-primary"
                    />
                  </label>
                </div>
              ) : null}

              <div className="flex flex-col gap-3 rounded-2xl bg-surface-container-low px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-on-surface-variant">
                  {filterSummary || "Viewing all purchase orders"} • Page {currentPage}
                </p>
                <p className="text-sm font-medium text-on-surface">{purchaseOrders.length} records loaded</p>
              </div>
            </div>
          </section>

          <section className="space-y-4">
            {error ? (
              <div className="rounded-xl border border-error/20 bg-error-container/70 p-5 text-sm text-on-error-container">
                {error}
              </div>
            ) : null}

            {isLoading
              ? Array.from({ length: 4 }).map((_, index) => <PurchaseOrderPageSkeleton key={index} />)
              : purchaseOrders.map((order) => (
                  <PurchaseOrderCard
                    key={order.id}
                    order={order}
                    onViewDetails={(orderId) => void purchaseOrder.openPreview(orderId)}
                  />
                ))}

            {!isLoading && purchaseOrders.length === 0 ? (
              <div className="rounded-xl border border-dashed border-outline-variant/40 bg-surface-container-low px-6 py-10 text-center">
                <p className="text-sm font-semibold text-on-surface">No purchase orders match these filters.</p>
                <p className="mt-1 text-sm text-on-surface-variant">
                  Try broadening the filters or adjusting the search criteria.
                </p>
              </div>
            ) : null}

            <div className="flex items-center justify-between rounded-xl border border-outline-variant/20 bg-surface-container-low px-4 py-3">
              <button
                type="button"
                onClick={() => setCurrentPage((page) => Math.max(page - 1, 1))}
                disabled={currentPage === 1}
                className="rounded-lg border border-outline-variant/30 px-4 py-2 text-sm font-semibold text-on-surface transition hover:bg-surface-container-high disabled:cursor-not-allowed disabled:opacity-50"
              >
                Previous
              </button>
              <span className="text-sm text-on-surface-variant">Page {currentPage}</span>
              <button
                type="button"
                onClick={() => setCurrentPage((page) => page + 1)}
                disabled={!hasNextPage}
                className="rounded-lg border border-outline-variant/30 px-4 py-2 text-sm font-semibold text-on-surface transition hover:bg-surface-container-high disabled:cursor-not-allowed disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </section>
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
