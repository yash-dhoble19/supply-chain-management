import { createPortal } from "react-dom";
import type { PurchaseOrderDocumentData } from "../../types/purchaseOrder.types";
import {
  formatPurchaseOrderCurrency,
  formatPurchaseOrderDate,
} from "../../utils/purchaseOrder";

interface PrintablePurchaseOrderProps {
  order: PurchaseOrderDocumentData;
}

export function PrintablePurchaseOrder({ order }: PrintablePurchaseOrderProps) {
  return createPortal(
    <div data-print-portal>
      <article data-print-page>
        <header data-print-header>
          <div data-print-brand>
            <h1>{order.companyName}</h1>
            <p>Purchase Order</p>
          </div>
          <div data-print-meta>
            <h2>{order.poNumber}</h2>
            <p>Issue Date: {formatPurchaseOrderDate(order.issueDate)}</p>
            <p>Delivery: {formatPurchaseOrderDate(order.deliveryDate)}</p>
          </div>
        </header>

        <section data-print-section data-print-two-col>
          <div>
            <h3>Supplier</h3>
            <p data-print-strong>{order.supplierName}</p>
            <p>{order.supplierAddress}</p>
            <p>{order.supplierEmail}</p>
          </div>
          <div>
            <h3>Bill To</h3>
            <p data-print-strong>{order.billToCompany}</p>
            <p>{order.billToAddress}</p>
            <p>{order.companyAddress}</p>
          </div>
        </section>

        <section data-print-section>
          <table data-print-table>
            <thead>
              <tr>
                <th>Description</th>
                <th>Qty</th>
                <th>Rate</th>
                <th>Amount</th>
              </tr>
            </thead>
            <tbody>
              {order.items.map((item, index) => (
                <tr key={`${item.description}-${index}`}>
                  <td>{item.description} ({item.sku ?? "N/A"})</td>
                  <td>{item.quantity}</td>
                  <td>{formatPurchaseOrderCurrency(item.rate)}</td>
                  <td>{formatPurchaseOrderCurrency(item.amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section data-print-summary-row>
          <div />
          <div data-print-summary>
            <div>
              <span>Subtotal</span>
              <span>{formatPurchaseOrderCurrency(order.subtotal)}</span>
            </div>
            <div>
              <span>Tax ({order.taxRate}%)</span>
              <span>{formatPurchaseOrderCurrency(order.tax)}</span>
            </div>
          </div>
        </section>

        <section data-print-total-row>
          <div data-print-total-box>
            <span>Total</span>
            <span>{formatPurchaseOrderCurrency(order.total)}</span>
          </div>
        </section>

        <section data-print-notes>
          <h3>Notes</h3>
          <p>
            {order.notes ??
              "Auto-generated purchase order. Please confirm supplier availability before dispatch."}
          </p>
        </section>
      </article>
    </div>,
    document.body,
  );
}
