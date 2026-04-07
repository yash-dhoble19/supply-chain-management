import type { SupplierManagementDetail } from "../../types/procurement.types";
import { formatSupplierCurrency, formatSupplierDate, performanceTierStyles, supplierStatusStyles } from "../../utils/suppliers";

interface SupplierDetailsDrawerProps {
  isOpen: boolean;
  supplier: SupplierManagementDetail | null;
  isLoading?: boolean;
  onClose: () => void;
}

export function SupplierDetailsDrawer({
  isOpen,
  supplier,
  isLoading = false,
  onClose,
}: SupplierDetailsDrawerProps) {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-[75] flex justify-end bg-slate-950/40 backdrop-blur-sm">
      <button type="button" onClick={onClose} className="flex-1 cursor-default" aria-label="Close supplier drawer" />
      <aside className="flex h-full w-full max-w-[540px] flex-col overflow-hidden bg-[#f4f7fd] shadow-2xl">
        <div className="flex items-start justify-between gap-4 border-b border-outline-variant/10 bg-white px-6 py-5">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-on-secondary-container">Supplier Profile</p>
            <h3 className="mt-2 text-2xl font-bold text-on-surface">{supplier?.supplier_name ?? "Loading supplier..."}</h3>
            <p className="mt-1 text-sm text-on-surface-variant">
              {supplier?.company_name ?? "Centralized supplier intelligence and procurement activity"}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex h-11 w-11 items-center justify-center rounded-full border border-outline-variant/20 bg-white text-on-surface-variant transition hover:bg-surface-container-low"
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-5 sm:px-6">
          {isLoading || !supplier ? (
            <div className="space-y-4">
              {Array.from({ length: 5 }).map((_, index) => (
                <div key={index} className="h-28 animate-pulse rounded-[1.5rem] bg-white shadow-sm" />
              ))}
            </div>
          ) : (
            <div className="space-y-5">
              <section className="rounded-[1.5rem] bg-[linear-gradient(135deg,#133b99_0%,#2051c6_55%,#81c4ff_100%)] p-5 text-white shadow-lg">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-white/70">{supplier.supplier_code}</p>
                    <h4 className="mt-2 text-2xl font-bold">{supplier.supplier_name}</h4>
                    <p className="mt-2 text-sm text-white/80">{supplier.location}</p>
                  </div>
                  <div className="space-y-2 text-right">
                    <span
                      className={`inline-flex rounded-full border px-3 py-1 text-[11px] font-bold uppercase tracking-[0.16em] ${
                        supplierStatusStyles[supplier.status] ?? "border-white/20 bg-white/10 text-white"
                      }`}
                    >
                      {supplier.status}
                    </span>
                    <div
                      className={`rounded-full px-3 py-1 text-[11px] font-bold ${
                        performanceTierStyles[supplier.performance_tier] ?? "bg-white/10 text-white"
                      }`}
                    >
                      {supplier.performance_tier}
                    </div>
                  </div>
                </div>

                <div className="mt-5 grid gap-3 sm:grid-cols-3">
                  <div className="rounded-2xl bg-white/10 p-3">
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-white/60">Supplier Score</p>
                    <p className="mt-2 text-2xl font-bold">{supplier.supplier_score}</p>
                  </div>
                  <div className="rounded-2xl bg-white/10 p-3">
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-white/60">Reliability</p>
                    <p className="mt-2 text-2xl font-bold">{supplier.reliability_percent}%</p>
                  </div>
                  <div className="rounded-2xl bg-white/10 p-3">
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-white/60">On-Time</p>
                    <p className="mt-2 text-2xl font-bold">{supplier.on_time_delivery_percent}%</p>
                  </div>
                </div>
              </section>

              <section className="rounded-[1.5rem] bg-white p-5 shadow-sm">
                <h4 className="text-lg font-bold text-on-surface">Profile Info</h4>
                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  <div className="space-y-1 text-sm text-on-surface-variant">
                    <p className="font-semibold text-on-surface">Contact</p>
                    <p>{supplier.contact_person || "Contact unassigned"}</p>
                    <p>{supplier.email}</p>
                    <p>{supplier.phone || "Phone pending"}</p>
                  </div>
                  <div className="space-y-1 text-sm text-on-surface-variant">
                    <p className="font-semibold text-on-surface">Location</p>
                    <p>{supplier.address || supplier.location}</p>
                    <p>{[supplier.city, supplier.state, supplier.country].filter(Boolean).join(", ") || "Location pending"}</p>
                    <p>{supplier.website || "Website not provided"}</p>
                  </div>
                </div>
              </section>

              <section className="rounded-[1.5rem] bg-white p-5 shadow-sm">
                <h4 className="text-lg font-bold text-on-surface">Performance Stats</h4>
                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  {[
                    { label: "Total Orders", value: supplier.total_orders.toLocaleString() },
                    { label: "Total Spend", value: formatSupplierCurrency(supplier.total_spend, supplier.currency) },
                    { label: "Avg Lead Time", value: `${supplier.average_delivery_days} days` },
                    { label: "Delivery Cost", value: formatSupplierCurrency(supplier.delivery_cost, supplier.currency) },
                  ].map((item) => (
                    <div key={item.label} className="rounded-2xl bg-surface-container-low p-4">
                      <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-on-secondary-container">{item.label}</p>
                      <p className="mt-2 text-xl font-bold text-on-surface">{item.value}</p>
                    </div>
                  ))}
                </div>
              </section>

              <section className="rounded-[1.5rem] bg-white p-5 shadow-sm">
                <h4 className="text-lg font-bold text-on-surface">Products Supplied</h4>
                <div className="mt-4 flex flex-wrap gap-2">
                  {supplier.supplied_products.length > 0 ? (
                    supplier.supplied_products.map((product) => (
                      <span
                        key={product}
                        className="rounded-full bg-primary-fixed px-3 py-1.5 text-xs font-semibold text-primary"
                      >
                        {product}
                      </span>
                    ))
                  ) : (
                    <p className="text-sm text-on-surface-variant">No product history yet.</p>
                  )}
                </div>
              </section>

              <section className="rounded-[1.5rem] bg-white p-5 shadow-sm">
                <h4 className="text-lg font-bold text-on-surface">Recent Procurement Activity</h4>
                <div className="mt-4 space-y-3">
                  {supplier.recent_purchase_orders.length > 0 ? (
                    supplier.recent_purchase_orders.map((order) => (
                      <div key={order.id} className="rounded-2xl bg-surface-container-low p-4">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="text-sm font-bold text-on-surface">{order.po_number}</p>
                            <p className="mt-1 text-sm text-on-surface-variant">{order.product_name}</p>
                          </div>
                          <span className="rounded-full bg-white px-3 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-on-surface">
                            {order.status.replace(/_/g, " ")}
                          </span>
                        </div>
                        <div className="mt-3 flex items-center justify-between text-xs text-on-surface-variant">
                          <span>{formatSupplierDate(order.created_at)}</span>
                          <span>{formatSupplierCurrency(order.total_value, supplier.currency)}</span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-on-surface-variant">No recent purchase orders for this supplier yet.</p>
                  )}
                </div>
              </section>

              {supplier.notes ? (
                <section className="rounded-[1.5rem] bg-white p-5 shadow-sm">
                  <h4 className="text-lg font-bold text-on-surface">Notes</h4>
                  <p className="mt-3 text-sm leading-6 text-on-surface-variant">{supplier.notes}</p>
                </section>
              ) : null}
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}
