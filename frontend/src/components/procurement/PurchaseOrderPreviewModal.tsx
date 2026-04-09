import { useRef } from "react";
import type { PurchaseOrderDocumentData } from "../../types/purchaseOrder.types";
import { DownloadPdfButton } from "./DownloadPdfButton";
import { PurchaseOrderDocument } from "./PurchaseOrderDocument";
import { PrintablePurchaseOrder } from "./PrintablePurchaseOrder";

interface PurchaseOrderPreviewModalProps {
  isOpen: boolean;
  order: PurchaseOrderDocumentData | null;
  isLoading?: boolean;
  isDownloading?: boolean;
  isApproving?: boolean;
  onClose: () => void;
  onDownload: () => void;
  onApprove?: () => void;
}

export function PurchaseOrderPreviewModal({
  isOpen,
  order,
  isLoading = false,
  isDownloading = false,
  isApproving = false,
  onClose,
  onDownload,
  onApprove,
}: PurchaseOrderPreviewModalProps) {
  const documentRef = useRef<HTMLDivElement>(null);

  if (!isOpen) {
    return null;
  }

  function handlePrint() {
    if (!order) {
      return;
    }

    const printClass = "printing-purchase-order";
    const handleAfterPrint = () => {
      document.body.classList.remove(printClass);
      window.removeEventListener("afterprint", handleAfterPrint);
    };

    document.body.classList.add(printClass);
    window.addEventListener("afterprint", handleAfterPrint);
    window.print();
  }

  return (
    <>
      {order ? <PrintablePurchaseOrder order={order} /> : null}
      <div
        data-print-root="purchase-order-modal"
        className="fixed inset-0 z-[70] flex items-center justify-center bg-slate-950/55 p-4 backdrop-blur-sm"
      >
      <div
        data-print-shell
        className="flex max-h-[92vh] w-full max-w-6xl flex-col overflow-hidden rounded-[28px] bg-[#eef2fb] shadow-2xl"
      >
        <div
          data-print-toolbar
          className="flex flex-col gap-4 border-b border-slate-200 bg-white px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6"
        >
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">Purchase Order Preview</p>
            <h3 className="mt-1 text-xl font-bold text-slate-900">{order?.poNumber ?? "Preparing document..."}</h3>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={handlePrint}
              disabled={!order}
              className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <span className="material-symbols-outlined text-base">print</span>
              Print
            </button>
            {onApprove ? (
              <button
                type="button"
                onClick={onApprove}
                disabled={!order || isApproving || order?.status !== "draft"}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isApproving ? <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" /> : null}
                Mark as Approved
              </button>
            ) : null}
            <button
              type="button"
              disabled
              className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-200 bg-slate-100 px-4 py-2.5 text-sm font-semibold text-slate-500"
            >
              <span className="material-symbols-outlined text-base">send</span>
              Send to Supplier
            </button>
            <DownloadPdfButton onClick={onDownload} isLoading={isDownloading} />
            <button
              type="button"
              onClick={onClose}
              className="inline-flex h-11 w-11 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 transition hover:bg-slate-50"
              aria-label="Close purchase order preview"
            >
              <span className="material-symbols-outlined">close</span>
            </button>
          </div>
        </div>

        <div data-print-scroll className="overflow-y-auto p-4 sm:p-6">
          {isLoading || !order ? (
            <div className="mx-auto h-[720px] max-w-4xl animate-pulse rounded-[28px] bg-white shadow-2xl" />
          ) : (
            <PurchaseOrderDocument ref={documentRef} order={order} />
          )}
        </div>
      </div>
      </div>
    </>
  );
}

// anything
