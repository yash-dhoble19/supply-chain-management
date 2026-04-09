import { forwardRef } from "react";
import type { PurchaseOrderDocumentData } from "../../types/purchaseOrder.types";
import {
  formatPurchaseOrderCurrency,
  formatPurchaseOrderDate,
  getPurchaseOrderStatusLabel,
} from "../../utils/purchaseOrder";

interface PurchaseOrderDocumentProps {
  order: PurchaseOrderDocumentData;
}

export const PurchaseOrderDocument = forwardRef<HTMLDivElement, PurchaseOrderDocumentProps>(
  function PurchaseOrderDocument({ order }, ref) {
    return (
      <div
        ref={ref}
        data-print-document
        className="mx-auto w-full max-w-4xl rounded-[28px] bg-white p-8 text-slate-900 shadow-2xl sm:p-10"
      >
        <div
          data-print-section
          className="rounded-[24px] bg-[linear-gradient(135deg,#1442b8_0%,#1b5bd4_50%,#7d2d00_100%)] px-6 py-6 text-white sm:px-8"
        >
          <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
            <div className="max-w-xl">
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-white/70">Purchase Order</p>
              <h2 className="mt-3 text-3xl font-bold tracking-tight">{order.companyName}</h2>
              <p className="mt-2 max-w-lg text-sm leading-6 text-white/80">{order.companyAddress}</p>
            </div>
            <div className="grid gap-3 rounded-2xl bg-white/10 p-5 backdrop-blur sm:min-w-[240px]">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/65">PO Number</p>
                <p className="mt-1 text-xl font-bold">{order.poNumber}</p>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/65">Issue Date</p>
                  <p className="mt-1 font-semibold">{formatPurchaseOrderDate(order.issueDate)}</p>
                </div>
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/65">Delivery Date</p>
                  <p className="mt-1 font-semibold">{formatPurchaseOrderDate(order.deliveryDate)}</p>
                </div>
              </div>
              <div className="inline-flex w-fit rounded-full bg-white/15 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.18em]">
                {getPurchaseOrderStatusLabel(order.status)}
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          <section data-print-section className="rounded-2xl border border-slate-200 p-5">
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">Supplier</p>
            <h3 className="mt-3 text-xl font-bold">{order.supplierName}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">{order.supplierAddress}</p>
            <p className="mt-2 text-sm font-medium text-slate-700">{order.supplierEmail}</p>
          </section>

          <section data-print-section className="rounded-2xl border border-slate-200 p-5">
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">Bill To</p>
            <h3 className="mt-3 text-xl font-bold">{order.billToCompany}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">{order.billToAddress}</p>
            <p className="mt-4 text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">Priority</p>
            <p className="mt-2 text-sm font-semibold text-slate-800">{order.priority ?? "Standard"}</p>
          </section>
        </div>

        <section data-print-section className="mt-8 overflow-hidden rounded-2xl border border-slate-200">
          <div data-print-table-wrap className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-5 py-4 text-left text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                    Description
                  </th>
                  <th className="px-5 py-4 text-left text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                    SKU
                  </th>
                  <th className="px-5 py-4 text-right text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                    Quantity
                  </th>
                  <th className="px-5 py-4 text-right text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                    Rate
                  </th>
                  <th className="px-5 py-4 text-right text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                    Amount
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {order.items.map((item, index) => (
                  <tr key={`${item.description}-${index}`}>
                    <td className="px-5 py-4 text-sm font-semibold text-slate-900">{item.description}</td>
                    <td className="px-5 py-4 text-sm text-slate-600">{item.sku ?? "N/A"}</td>
                    <td className="px-5 py-4 text-right text-sm text-slate-700">{item.quantity.toLocaleString()}</td>
                    <td className="px-5 py-4 text-right text-sm text-slate-700">{formatPurchaseOrderCurrency(item.rate)}</td>
                    <td className="px-5 py-4 text-right text-sm font-semibold text-slate-900">
                      {formatPurchaseOrderCurrency(item.amount)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_280px]">
          <section data-print-section className="rounded-2xl border border-slate-200 p-5">
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">Notes</p>
            <p className="mt-3 text-sm leading-7 text-slate-700">
              {order.notes ?? "Please confirm item availability, shipping schedule, and invoice details before dispatch."}
            </p>
          </section>

          <section data-print-section className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
            <div className="space-y-3 text-sm">
              <div className="flex items-center justify-between text-slate-600">
                <span>Subtotal</span>
                <span className="font-semibold text-slate-900">{formatPurchaseOrderCurrency(order.subtotal)}</span>
              </div>
              <div className="flex items-center justify-between text-slate-600">
                <span>Tax ({order.taxRate}%)</span>
                <span className="font-semibold text-slate-900">{formatPurchaseOrderCurrency(order.tax)}</span>
              </div>
              <div className="border-t border-slate-200 pt-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">Total</span>
                  <span className="text-2xl font-bold text-slate-900">{formatPurchaseOrderCurrency(order.total)}</span>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    );
  },
);

// anything
