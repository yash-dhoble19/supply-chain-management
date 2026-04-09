import type { SupplierManagementRecord, SupplierUpsertPayload } from "../types/procurement.types";

export const supplierStatusStyles: Record<string, string> = {
  Preferred: "border-emerald-200 bg-emerald-50 text-emerald-700",
  Active: "border-sky-200 bg-sky-50 text-sky-700",
  Inactive: "border-slate-200 bg-slate-100 text-slate-600",
  Blocked: "border-rose-200 bg-rose-50 text-rose-700",
  "At Risk": "border-amber-200 bg-amber-50 text-amber-700",
};

export const performanceTierStyles: Record<string, string> = {
  Elite: "bg-emerald-50 text-emerald-700",
  Strong: "bg-sky-50 text-sky-700",
  Stable: "bg-indigo-50 text-indigo-700",
  Watch: "bg-amber-50 text-amber-700",
};

export function formatSupplierCurrency(value: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: value >= 1000 ? 0 : 2,
  }).format(value);
}

export function formatSupplierDate(value: string | null | undefined): string {
  if (!value) {
    return "Pending";
  }
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

export function getSupplierInitials(name: string): string {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

export function buildDefaultSupplierPayload(): SupplierUpsertPayload {
  return {
    supplier_name: "",
    email: "",
    company_name: "",
    supplier_code: "",
    contact_person: "",
    phone: "",
    website: "",
    product_name: "",
    product_category: "",
    unit_price: 0,
    currency: "USD",
    delivery_cost: 0,
    average_delivery_days: 5,
    minimum_order_quantity: null,
    address: "",
    city: "",
    state: "",
    country: "",
    postal_code: "",
    supplier_type: "Strategic",
    status: "ACTIVE",
    preferred_supplier: false,
    supplier_score: null,
    reliability_percent: 95,
    on_time_delivery_percent: 93,
    gst_number: "",
    tax_id: "",
    notes: "",
  };
}

export function mapSupplierRecordToPayload(record: SupplierManagementRecord): SupplierUpsertPayload {
  return {
    supplier_name: record.supplier_name,
    email: record.email,
    company_name: record.company_name,
    supplier_code: record.supplier_code,
    contact_person: record.contact_person ?? "",
    phone: record.phone ?? "",
    website: record.website ?? "",
    product_name: record.product_name,
    product_category: record.product_category,
    unit_price: record.unit_price,
    currency: record.currency,
    delivery_cost: record.delivery_cost,
    average_delivery_days: record.average_delivery_days,
    minimum_order_quantity: record.minimum_order_quantity,
    address: record.address ?? "",
    city: record.city ?? "",
    state: record.state ?? "",
    country: record.country ?? "",
    postal_code: record.postal_code ?? "",
    supplier_type: record.supplier_type,
    status: record.raw_status,
    preferred_supplier: record.preferred_supplier,
    supplier_score: record.supplier_score,
    reliability_percent: record.reliability_percent,
    on_time_delivery_percent: record.on_time_delivery_percent,
    gst_number: record.gst_number ?? "",
    tax_id: record.tax_id ?? "",
    notes: record.notes ?? "",
  };
}

export function normalizePayload(payload: SupplierUpsertPayload): SupplierUpsertPayload {
  return {
    ...payload,
    supplier_name: payload.supplier_name.trim(),
    email: payload.email.trim(),
    company_name: payload.company_name?.trim() || payload.supplier_name.trim(),
    supplier_code: payload.supplier_code?.trim() || null,
    contact_person: payload.contact_person?.trim() || null,
    phone: payload.phone?.trim() || null,
    website: payload.website?.trim() || null,
    product_name: payload.product_name?.trim() || null,
    product_category: payload.product_category?.trim() || null,
    address: payload.address?.trim() || null,
    city: payload.city?.trim() || null,
    state: payload.state?.trim() || null,
    country: payload.country?.trim() || null,
    postal_code: payload.postal_code?.trim() || null,
    gst_number: payload.gst_number?.trim() || null,
    tax_id: payload.tax_id?.trim() || null,
    notes: payload.notes?.trim() || null,
  };
}

// anything
