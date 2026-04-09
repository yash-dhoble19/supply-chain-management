import type { SupplierManagementRecord } from "../../types/procurement.types";
import {
  formatSupplierCurrency,
  getSupplierInitials,
  performanceTierStyles,
  supplierStatusStyles,
} from "../../utils/suppliers";
import { SupplierRowActions } from "./SupplierRowActions";

interface SupplierManagementTableProps {
  rows: SupplierManagementRecord[];
  isLoading?: boolean;
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  onAddSupplier: () => void;
  onViewSupplier: (supplierId: string) => void;
  onEditSupplier: (supplier: SupplierManagementRecord) => void;
  onDeleteSupplier: (supplierId: string) => void;
  deletingId?: string | null;
}

function LoadingRows() {
  return (
    <div className="space-y-3 px-4 py-4">
      {Array.from({ length: 5 }).map((_, index) => (
        <div key={index} className="h-24 animate-pulse rounded-2xl bg-surface-container-low" />
      ))}
    </div>
  );
}

function EmptyState({ onAddSupplier }: { onAddSupplier: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-16 text-center">
      <div className="flex h-20 w-20 items-center justify-center rounded-[1.75rem] bg-primary-fixed text-primary">
        <span className="material-symbols-outlined text-4xl">group_add</span>
      </div>
      <h3 className="mt-5 text-2xl font-bold text-on-surface">No suppliers added yet</h3>
      <p className="mt-2 max-w-xl text-sm leading-6 text-on-surface-variant">
        Build your procurement network with supplier profiles, pricing intelligence, and performance data that can connect directly to backend supplier records.
      </p>
      <button
        type="button"
        onClick={onAddSupplier}
        className="mt-6 inline-flex items-center justify-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-primary/90"
      >
        <span className="material-symbols-outlined text-base">add</span>
        Add Supplier
      </button>
    </div>
  );
}

export function SupplierManagementTable({
  rows,
  isLoading = false,
  page,
  pageSize,
  totalItems,
  totalPages,
  onPageChange,
  onPageSizeChange,
  onAddSupplier,
  onViewSupplier,
  onEditSupplier,
  onDeleteSupplier,
  deletingId,
}: SupplierManagementTableProps) {
  return (
    <section className="overflow-hidden rounded-[1.5rem] border border-outline-variant/15 bg-surface-container-lowest shadow-sm">
      <div className="flex flex-col gap-3 border-b border-outline-variant/10 px-5 py-5 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-on-secondary-container">Supplier Directory</p>
          <h3 className="mt-2 text-2xl font-bold text-on-surface">Operational supplier relationships</h3>
        </div>
        <div className="flex items-center gap-3 text-sm text-on-surface-variant">
          <span>{totalItems.toLocaleString()} results</span>
          <span className="h-1 w-1 rounded-full bg-outline-variant/40" />
          <span>{pageSize.toLocaleString()} per page</span>
        </div>
      </div>

      {isLoading ? <LoadingRows /> : null}
      {!isLoading && rows.length === 0 ? <EmptyState onAddSupplier={onAddSupplier} /> : null}

      {!isLoading && rows.length > 0 ? (
        <>
          <div className="overflow-x-auto">
            <table className="min-w-[1480px] w-full text-left">
              <thead className="bg-surface-container-low">
                <tr>
                  {[
                    "Supplier",
                    "Contact",
                    "Product",
                    "Unit Price",
                    "Orders",
                    "Spend",
                    "Delivery",
                    "Performance",
                    "Status",
                    "",
                  ].map((heading) => (
                    <th
                      key={heading}
                      className="px-5 py-4 text-[11px] font-bold uppercase tracking-[0.18em] text-on-surface-variant"
                    >
                      {heading}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/10">
                {rows.map((supplier) => (
                  <tr key={supplier.supplier_id} className="align-top transition-colors hover:bg-surface-container-low/60">
                    <td className="px-5 py-5">
                      <div className="flex items-start gap-3">
                        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary-fixed text-sm font-bold text-primary">
                          {getSupplierInitials(supplier.supplier_name)}
                        </div>
                        <div className="space-y-1">
                          <p className="text-sm font-bold text-on-surface">{supplier.supplier_name}</p>
                          <p className="text-xs text-on-surface-variant">{supplier.company_name}</p>
                          <div className="flex flex-wrap items-center gap-2 text-[11px] font-semibold text-on-surface-variant">
                            <span>{supplier.supplier_code}</span>
                            <span className="h-1 w-1 rounded-full bg-outline-variant/40" />
                            <span>{supplier.product_category}</span>
                            <span className="h-1 w-1 rounded-full bg-outline-variant/40" />
                            <span>{supplier.location}</span>
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-5">
                      <div className="space-y-1 text-sm">
                        <p className="font-semibold text-on-surface">{supplier.email}</p>
                        <p className="text-on-surface-variant">{supplier.phone || "Phone pending"}</p>
                        <p className="text-xs text-on-surface-variant">{supplier.contact_person || "Contact unassigned"}</p>
                      </div>
                    </td>
                    <td className="px-5 py-5">
                      <div className="space-y-1">
                        <p className="text-sm font-semibold text-on-surface">{supplier.product_name}</p>
                        <div className="flex flex-wrap gap-2">
                          {supplier.supplied_products.slice(0, 2).map((product) => (
                            <span
                              key={product}
                              className="rounded-full bg-surface-container-high px-2.5 py-1 text-[11px] font-semibold text-on-surface-variant"
                            >
                              {product}
                            </span>
                          ))}
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-5">
                      <div className="space-y-1">
                        <p className="text-sm font-bold text-on-surface">
                          {formatSupplierCurrency(supplier.unit_price, supplier.currency)}
                        </p>
                        <p className="text-xs text-on-surface-variant">
                          Delivery {formatSupplierCurrency(supplier.delivery_cost, supplier.currency)}
                        </p>
                      </div>
                    </td>
                    <td className="px-5 py-5">
                      <div className="space-y-1">
                        <p className="text-lg font-bold text-on-surface">{supplier.total_orders}</p>
                        <p className="text-xs text-on-surface-variant">{supplier.minimum_order_quantity || 0} min order qty</p>
                      </div>
                    </td>
                    <td className="px-5 py-5">
                      <div className="space-y-1">
                        <p className="text-sm font-bold text-on-surface">
                          {formatSupplierCurrency(supplier.total_spend, supplier.currency)}
                        </p>
                        <p className="text-xs text-on-surface-variant">{supplier.supplier_type}</p>
                      </div>
                    </td>
                    <td className="px-5 py-5">
                      <div className="space-y-2 text-sm">
                        <p className="font-semibold text-on-surface">{supplier.average_delivery_days}d avg lead time</p>
                        <p className="text-on-surface-variant">{supplier.reliability_percent}% reliability</p>
                        <p className="text-on-surface-variant">{supplier.on_time_delivery_percent}% on-time</p>
                      </div>
                    </td>
                    <td className="px-5 py-5">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm font-bold text-on-surface">
                          <span>{supplier.supplier_score}</span>
                          <span
                            className={`rounded-full px-2 py-1 text-[11px] font-bold ${performanceTierStyles[supplier.performance_tier] ?? "bg-slate-100 text-slate-700"}`}
                          >
                            {supplier.performance_tier}
                          </span>
                        </div>
                        <div className="h-2 rounded-full bg-surface-container-high">
                          <div
                            className="h-2 rounded-full bg-[linear-gradient(90deg,#1d4ed8_0%,#38bdf8_100%)]"
                            style={{ width: `${Math.min(supplier.supplier_score, 100)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-5">
                      <span
                        className={`inline-flex rounded-full border px-3 py-1 text-[11px] font-bold uppercase tracking-[0.16em] ${
                          supplierStatusStyles[supplier.status] ?? "border-slate-200 bg-slate-100 text-slate-700"
                        }`}
                      >
                        {supplier.status}
                      </span>
                    </td>
                    <td className="px-5 py-5">
                      <SupplierRowActions
                        onView={() => onViewSupplier(supplier.supplier_id)}
                        onEdit={() => onEditSupplier(supplier)}
                        onDelete={() => onDeleteSupplier(supplier.supplier_id)}
                        isDeleting={deletingId === supplier.supplier_id}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex flex-col gap-4 border-t border-outline-variant/10 px-5 py-4 md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-3 text-sm text-on-surface-variant">
              <span>
                Page {page} of {totalPages}
              </span>
              <label className="flex items-center gap-2">
                <span>Rows</span>
                <select
                  value={pageSize}
                  onChange={(event) => onPageSizeChange(Number(event.target.value))}
                  className="h-10 rounded-lg border border-outline-variant/20 bg-white px-3 text-sm text-on-surface outline-none"
                >
                  {[10, 20, 30, 50].map((size) => (
                    <option key={size} value={size}>
                      {size}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => onPageChange(page - 1)}
                disabled={page <= 1}
                className="inline-flex h-10 items-center justify-center rounded-lg border border-outline-variant/20 bg-white px-4 text-sm font-semibold text-on-surface transition hover:bg-surface-container-low disabled:cursor-not-allowed disabled:opacity-50"
              >
                Previous
              </button>
              <button
                type="button"
                onClick={() => onPageChange(page + 1)}
                disabled={page >= totalPages}
                className="inline-flex h-10 items-center justify-center rounded-lg border border-outline-variant/20 bg-white px-4 text-sm font-semibold text-on-surface transition hover:bg-surface-container-low disabled:cursor-not-allowed disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        </>
      ) : null}
    </section>
  );
}

// anything
