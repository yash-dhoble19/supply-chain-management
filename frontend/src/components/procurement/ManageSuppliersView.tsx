import { useEffect, useMemo, useState } from "react";
import { procurementService } from "../../services/procurementService";
import type {
  SupplierManagementDetail,
  SupplierManagementFilters,
  SupplierManagementListResponse,
  SupplierManagementRecord,
  SupplierUpsertPayload,
} from "../../types/procurement.types";
import { formatSupplierCurrency } from "../../utils/suppliers";
import { SupplierDetailsDrawer } from "./SupplierDetailsDrawer";
import { SupplierFilterBar } from "./SupplierFilterBar";
import { SupplierFormModal } from "./SupplierFormModal";
import { SupplierManagementTable } from "./SupplierManagementTable";
import { SupplierSummaryCards } from "./SupplierSummaryCards";

interface ManageSuppliersViewProps {
  searchTerm: string;
  onSearchChange: (value: string) => void;
  onSupplierMutated?: () => void;
}

type SortOption = "highest_score" | "most_orders" | "lowest_price" | "fastest_delivery" | "recently_added";

const defaultFilters = {
  supplierType: "all",
  status: "all",
  productCategory: "all",
  location: "all",
  performanceTier: "all",
  deliveryReliabilityRange: "all",
  sort: "highest_score" as SortOption,
};

function buildCsv(rows: SupplierManagementRecord[]) {
  const headers = [
    "supplier_id",
    "supplier_name",
    "supplier_code",
    "email",
    "phone",
    "product_name",
    "product_category",
    "unit_price",
    "currency",
    "location",
    "delivery_cost",
    "average_delivery_days",
    "supplier_score",
    "reliability_percent",
    "on_time_delivery_percent",
    "total_orders",
    "total_spend",
    "status",
  ];

  const lines = rows.map((row) =>
    headers
      .map((header) => {
        const rawValue = row[header as keyof SupplierManagementRecord];
        const value = Array.isArray(rawValue) ? rawValue.join(" | ") : String(rawValue ?? "");
        return `"${value.replace(/"/g, '""')}"`;
      })
      .join(","),
  );
  return [headers.join(","), ...lines].join("\n");
}

export function ManageSuppliersView({
  searchTerm,
  onSearchChange,
  onSupplierMutated,
}: ManageSuppliersViewProps) {
  const [filters, setFilters] = useState(defaultFilters);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [data, setData] = useState<SupplierManagementListResponse | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);
  const [formMode, setFormMode] = useState<"create" | "edit">("create");
  const [isFormOpen, setFormOpen] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState<SupplierManagementRecord | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setSubmitting] = useState(false);
  const [isDetailOpen, setDetailOpen] = useState(false);
  const [activeSupplierId, setActiveSupplierId] = useState<string | null>(null);
  const [activeSupplier, setActiveSupplier] = useState<SupplierManagementDetail | null>(null);
  const [isDetailLoading, setDetailLoading] = useState(false);
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState(searchTerm);

  useEffect(() => {
    const timeout = window.setTimeout(() => setDebouncedSearchTerm(searchTerm), 250);
    return () => window.clearTimeout(timeout);
  }, [searchTerm]);

  useEffect(() => {
    const controller = new AbortController();

    async function loadSuppliers() {
      setLoading(true);
      setError(null);

      try {
        const response = await procurementService.getSuppliers(
          {
            search: debouncedSearchTerm,
            supplierType: filters.supplierType,
            status: filters.status,
            productCategory: filters.productCategory,
            location: filters.location,
            performanceTier: filters.performanceTier,
            deliveryReliabilityRange: filters.deliveryReliabilityRange,
            sort: filters.sort,
            page,
            pageSize,
          },
          controller.signal,
        );
        setData(response);
      } catch (requestError) {
        if (!controller.signal.aborted) {
          setError(requestError instanceof Error ? requestError.message : "Unable to load suppliers.");
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void loadSuppliers();
    return () => controller.abort();
  }, [debouncedSearchTerm, filters, page, pageSize, reloadToken]);

  useEffect(() => {
    if (!activeSupplierId || !isDetailOpen) {
      return;
    }

    const supplierId = activeSupplierId;
    const controller = new AbortController();

    async function loadSupplierDetail() {
      setDetailLoading(true);
      try {
        const response = await procurementService.getSupplierById(supplierId, controller.signal);
        setActiveSupplier(response);
      } catch {
        if (!controller.signal.aborted) {
          setActiveSupplier(null);
        }
      } finally {
        if (!controller.signal.aborted) {
          setDetailLoading(false);
        }
      }
    }

    void loadSupplierDetail();
    return () => controller.abort();
  }, [activeSupplierId, isDetailOpen, reloadToken]);

  const summary = data?.summary;
  const rows = data?.items ?? [];
  const pagination = data?.pagination;
  const filterOptions: SupplierManagementFilters | null = data?.filters ?? null;

  const summaryCaption = useMemo(() => {
    if (!summary) {
      return "Centralized supplier directory, pricing, and procurement relationships";
    }
    return `${summary.total_suppliers} suppliers managing ${summary.total_purchase_orders.toLocaleString()} purchase orders and ${formatSupplierCurrency(summary.total_spend)} of tracked spend.`;
  }, [summary]);

  function openCreateModal() {
    setFormMode("create");
    setEditingSupplier(null);
    setFormError(null);
    setFormOpen(true);
  }

  function openEditModal(supplier: SupplierManagementRecord) {
    setFormMode("edit");
    setEditingSupplier(supplier);
    setFormError(null);
    setFormOpen(true);
  }

  function handleFilterChange(next: Partial<typeof defaultFilters>) {
    setPage(1);
    setFilters((current) => ({ ...current, ...next }));
  }

  function resetFilters() {
    setPage(1);
    setFilters(defaultFilters);
    onSearchChange("");
  }

  async function handleSubmit(payload: SupplierUpsertPayload) {
    setSubmitting(true);
    setFormError(null);
    try {
      if (formMode === "create") {
        await procurementService.createSupplier(payload);
      } else if (editingSupplier) {
        await procurementService.updateSupplier(editingSupplier.supplier_id, payload);
      }
      setFormOpen(false);
      setReloadToken((current) => current + 1);
      onSupplierMutated?.();
    } catch (requestError) {
      setFormError(requestError instanceof Error ? requestError.message : "Unable to save supplier.");
    } finally {
      setSubmitting(false);
    }
  }

  function handleExport() {
    const csv = buildCsv(rows);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "chainmind-suppliers.csv";
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6">
      <section className="rounded-[1.75rem] bg-[radial-gradient(circle_at_top_left,rgba(37,84,199,0.2),transparent_40%),linear-gradient(180deg,#ffffff_0%,#f7faff_100%)] p-6 shadow-panel">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-on-secondary-container">Procurement Intelligence</p>
            <h2 className="mt-3 text-[2rem] font-bold tracking-tight text-on-surface">Manage Suppliers</h2>
            <p className="mt-3 text-base leading-7 text-on-surface-variant">{summaryCaption}</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={handleExport}
              className="inline-flex h-11 items-center justify-center gap-2 rounded-xl border border-outline-variant/20 bg-white px-4 text-sm font-semibold text-on-surface transition hover:bg-surface-container-low"
            >
              <span className="material-symbols-outlined text-base">download</span>
              Export Suppliers
            </button>
            <button
              type="button"
              onClick={openCreateModal}
              className="inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-primary px-5 text-sm font-semibold text-white shadow-sm transition hover:bg-primary/90"
            >
              <span className="material-symbols-outlined text-base">add</span>
              Add Supplier
            </button>
          </div>
        </div>
      </section>

      {summary ? <SupplierSummaryCards summary={summary} /> : null}

      <SupplierFilterBar
        searchTerm={searchTerm}
        onSearchChange={(value) => {
          setPage(1);
          onSearchChange(value);
        }}
        filters={filterOptions}
        values={filters}
        onChange={handleFilterChange}
        onReset={resetFilters}
      />

      {error ? (
        <section className="rounded-2xl border border-error/20 bg-error-container/60 p-5 text-sm text-on-error-container">
          {error}
        </section>
      ) : null}

      <SupplierManagementTable
        rows={rows}
        isLoading={isLoading}
        page={pagination?.page ?? page}
        pageSize={pagination?.page_size ?? pageSize}
        totalItems={pagination?.total_items ?? 0}
        totalPages={pagination?.total_pages ?? 1}
        onPageChange={setPage}
        onPageSizeChange={(nextPageSize) => {
          setPage(1);
          setPageSize(nextPageSize);
        }}
        onAddSupplier={openCreateModal}
        onViewSupplier={(supplierId) => {
          setActiveSupplierId(supplierId);
          setDetailOpen(true);
        }}
        onEditSupplier={openEditModal}
      />

      <SupplierFormModal
        isOpen={isFormOpen}
        mode={formMode}
        supplier={editingSupplier}
        isSubmitting={isSubmitting}
        error={formError}
        onClose={() => setFormOpen(false)}
        onSubmit={handleSubmit}
      />

      <SupplierDetailsDrawer
        isOpen={isDetailOpen}
        supplier={activeSupplier}
        isLoading={isDetailLoading}
        onClose={() => {
          setDetailOpen(false);
          setActiveSupplierId(null);
          setActiveSupplier(null);
        }}
      />
    </div>
  );
}

// anything
