import type { FormEvent } from "react";
import { useEffect, useMemo, useState } from "react";
import type { SupplierManagementRecord, SupplierUpsertPayload } from "../../types/procurement.types";
import {
  buildDefaultSupplierPayload,
  mapSupplierRecordToPayload,
  normalizePayload,
} from "../../utils/suppliers";

interface SupplierFormModalProps {
  isOpen: boolean;
  mode: "create" | "edit";
  supplier?: SupplierManagementRecord | null;
  isSubmitting?: boolean;
  error?: string | null;
  onClose: () => void;
  onSubmit: (payload: SupplierUpsertPayload) => Promise<void> | void;
}

type ValidationErrors = Partial<Record<keyof SupplierUpsertPayload, string>>;

function Field({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
  error,
}: {
  label: string;
  value: string | number;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: string;
  error?: string;
}) {
  return (
    <label className="space-y-2">
      <span className="text-sm font-semibold text-on-surface">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className={`h-11 w-full rounded-xl border bg-white px-3 text-sm text-on-surface outline-none transition ${
          error
            ? "border-error/50 ring-2 ring-error/10"
            : "border-outline-variant/20 focus:border-primary/40 focus:ring-2 focus:ring-primary/10"
        }`}
      />
      {error ? <p className="text-xs font-medium text-error">{error}</p> : null}
    </label>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  return (
    <label className="space-y-2">
      <span className="text-sm font-semibold text-on-surface">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-11 w-full rounded-xl border border-outline-variant/20 bg-white px-3 text-sm text-on-surface outline-none transition focus:border-primary/40 focus:ring-2 focus:ring-primary/10"
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

function TextareaField({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="space-y-2">
      <span className="text-sm font-semibold text-on-surface">{label}</span>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        rows={4}
        className="w-full rounded-xl border border-outline-variant/20 bg-white px-3 py-3 text-sm text-on-surface outline-none transition focus:border-primary/40 focus:ring-2 focus:ring-primary/10"
      />
    </label>
  );
}

export function SupplierFormModal({
  isOpen,
  mode,
  supplier,
  isSubmitting = false,
  error,
  onClose,
  onSubmit,
}: SupplierFormModalProps) {
  const [form, setForm] = useState<SupplierUpsertPayload>(buildDefaultSupplierPayload());
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    setForm(supplier ? mapSupplierRecordToPayload(supplier) : buildDefaultSupplierPayload());
    setValidationErrors({});
  }, [isOpen, supplier]);

  const title = useMemo(
    () => (mode === "create" ? "Add Supplier" : `Edit ${supplier?.supplier_name ?? "Supplier"}`),
    [mode, supplier],
  );

  if (!isOpen) {
    return null;
  }

  function updateField<K extends keyof SupplierUpsertPayload>(key: K, value: SupplierUpsertPayload[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function validate(payload: SupplierUpsertPayload): ValidationErrors {
    const nextErrors: ValidationErrors = {};
    if (!payload.supplier_name.trim()) nextErrors.supplier_name = "Supplier name is required.";
    if (!payload.email.trim()) nextErrors.email = "Email is required.";
    if (!payload.product_category?.trim()) nextErrors.product_category = "Product category is required.";
    if (payload.unit_price < 0) nextErrors.unit_price = "Unit price cannot be negative.";
    if (payload.delivery_cost < 0) nextErrors.delivery_cost = "Delivery cost cannot be negative.";
    if (payload.average_delivery_days < 0) nextErrors.average_delivery_days = "Delivery days cannot be negative.";
    if (payload.reliability_percent < 0 || payload.reliability_percent > 100) {
      nextErrors.reliability_percent = "Reliability should be between 0 and 100.";
    }
    if (payload.on_time_delivery_percent < 0 || payload.on_time_delivery_percent > 100) {
      nextErrors.on_time_delivery_percent = "On-time delivery should be between 0 and 100.";
    }
    return nextErrors;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalized = normalizePayload(form);
    const nextErrors = validate(normalized);
    setValidationErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      return;
    }
    await onSubmit(normalized);
  }

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-slate-950/55 p-4 backdrop-blur-sm">
      <div className="flex max-h-[92vh] w-full max-w-5xl flex-col overflow-hidden rounded-[28px] bg-[#eff4fe] shadow-2xl">
        <div className="flex items-start justify-between gap-6 border-b border-outline-variant/10 bg-white px-6 py-5">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-on-secondary-container">Supplier Workspace</p>
            <h3 className="mt-2 text-2xl font-bold text-on-surface">{title}</h3>
            <p className="mt-2 text-sm text-on-surface-variant">
              Capture supplier directory, procurement, pricing, and classification details in one workflow.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex h-11 w-11 items-center justify-center rounded-full border border-outline-variant/20 bg-white text-on-surface-variant transition hover:bg-surface-container-low"
            aria-label="Close supplier form"
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        <form id="supplier-form" onSubmit={handleSubmit} className="overflow-y-auto px-5 py-5 sm:px-6">
          <div className="space-y-6">
            {error ? (
              <div className="rounded-2xl border border-error/20 bg-error-container/60 px-4 py-3 text-sm text-on-error-container">
                {error}
              </div>
            ) : null}

            <section className="rounded-[1.5rem] bg-white p-5 shadow-sm">
              <h4 className="text-lg font-bold text-on-surface">Basic Info</h4>
              <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <Field
                  label="Supplier Name"
                  value={form.supplier_name}
                  onChange={(value) => updateField("supplier_name", value)}
                  placeholder="Apex Components"
                  error={validationErrors.supplier_name}
                />
                <Field
                  label="Company Name"
                  value={form.company_name ?? ""}
                  onChange={(value) => updateField("company_name", value)}
                  placeholder="Apex Components Pvt Ltd"
                />
                <Field
                  label="Supplier Code"
                  value={form.supplier_code ?? ""}
                  onChange={(value) => updateField("supplier_code", value)}
                  placeholder="SUP-0042"
                />
                <Field
                  label="Contact Person"
                  value={form.contact_person ?? ""}
                  onChange={(value) => updateField("contact_person", value)}
                  placeholder="Maya Shah"
                />
              </div>
            </section>

            <section className="rounded-[1.5rem] bg-white p-5 shadow-sm">
              <h4 className="text-lg font-bold text-on-surface">Contact Info</h4>
              <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                <Field
                  label="Email"
                  value={form.email}
                  onChange={(value) => updateField("email", value)}
                  placeholder="contact@supplier.com"
                  type="email"
                  error={validationErrors.email}
                />
                <Field
                  label="Phone Number"
                  value={form.phone ?? ""}
                  onChange={(value) => updateField("phone", value)}
                  placeholder="+1 202 555 0168"
                />
                <Field
                  label="Website"
                  value={form.website ?? ""}
                  onChange={(value) => updateField("website", value)}
                  placeholder="https://supplier.com"
                />
              </div>
            </section>

            <section className="rounded-[1.5rem] bg-white p-5 shadow-sm">
              <h4 className="text-lg font-bold text-on-surface">Product and Procurement</h4>
              <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <Field
                  label="Product Name"
                  value={form.product_name ?? ""}
                  onChange={(value) => updateField("product_name", value)}
                  placeholder="Servo Controller"
                />
                <Field
                  label="Product Category"
                  value={form.product_category ?? ""}
                  onChange={(value) => updateField("product_category", value)}
                  placeholder="Electronics"
                  error={validationErrors.product_category}
                />
                <Field
                  label="Unit Price"
                  value={form.unit_price}
                  onChange={(value) => updateField("unit_price", Number(value))}
                  type="number"
                  error={validationErrors.unit_price}
                />
                <Field
                  label="Currency"
                  value={form.currency}
                  onChange={(value) => updateField("currency", value)}
                  placeholder="USD"
                />
                <Field
                  label="Delivery Cost"
                  value={form.delivery_cost}
                  onChange={(value) => updateField("delivery_cost", Number(value))}
                  type="number"
                  error={validationErrors.delivery_cost}
                />
                <Field
                  label="Average Delivery Days"
                  value={form.average_delivery_days}
                  onChange={(value) => updateField("average_delivery_days", Number(value))}
                  type="number"
                  error={validationErrors.average_delivery_days}
                />
                <Field
                  label="Minimum Order Quantity"
                  value={form.minimum_order_quantity ?? ""}
                  onChange={(value) => updateField("minimum_order_quantity", value ? Number(value) : null)}
                  type="number"
                />
                <SelectField
                  label="Supplier Type"
                  value={form.supplier_type}
                  onChange={(value) => updateField("supplier_type", value)}
                  options={["Strategic", "Manufacturer", "Distributor", "Regional", "Specialty"]}
                />
              </div>
            </section>

            <section className="rounded-[1.5rem] bg-white p-5 shadow-sm">
              <h4 className="text-lg font-bold text-on-surface">Location Info</h4>
              <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                <Field
                  label="Address"
                  value={form.address ?? ""}
                  onChange={(value) => updateField("address", value)}
                  placeholder="77 Industrial Park"
                />
                <Field label="City" value={form.city ?? ""} onChange={(value) => updateField("city", value)} placeholder="Chicago" />
                <Field label="State" value={form.state ?? ""} onChange={(value) => updateField("state", value)} placeholder="Illinois" />
                <Field label="Country" value={form.country ?? ""} onChange={(value) => updateField("country", value)} placeholder="USA" />
                <Field
                  label="Postal Code"
                  value={form.postal_code ?? ""}
                  onChange={(value) => updateField("postal_code", value)}
                  placeholder="60601"
                />
                <Field
                  label="Tax ID / GST"
                  value={form.tax_id ?? form.gst_number ?? ""}
                  onChange={(value) => {
                    updateField("tax_id", value);
                    updateField("gst_number", value);
                  }}
                  placeholder="TAX-00991"
                />
              </div>
            </section>

            <section className="rounded-[1.5rem] bg-white p-5 shadow-sm">
              <h4 className="text-lg font-bold text-on-surface">Performance and Classification</h4>
              <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <SelectField
                  label="Status"
                  value={form.status}
                  onChange={(value) => updateField("status", value)}
                  options={["ACTIVE", "INACTIVE", "BLOCKED", "AT_RISK"]}
                />
                <Field
                  label="Reliability %"
                  value={form.reliability_percent}
                  onChange={(value) => updateField("reliability_percent", Number(value))}
                  type="number"
                  error={validationErrors.reliability_percent}
                />
                <Field
                  label="On-Time Delivery %"
                  value={form.on_time_delivery_percent}
                  onChange={(value) => updateField("on_time_delivery_percent", Number(value))}
                  type="number"
                  error={validationErrors.on_time_delivery_percent}
                />
                <Field
                  label="Supplier Score"
                  value={form.supplier_score ?? ""}
                  onChange={(value) => updateField("supplier_score", value ? Number(value) : null)}
                  type="number"
                />
              </div>
              <label className="mt-5 flex items-center justify-between rounded-2xl border border-outline-variant/10 bg-surface-container-low px-4 py-3">
                <div>
                  <p className="text-sm font-semibold text-on-surface">Preferred Supplier</p>
                  <p className="text-xs text-on-surface-variant">Highlight this supplier as a strategic procurement partner.</p>
                </div>
                <button
                  type="button"
                  onClick={() => updateField("preferred_supplier", !form.preferred_supplier)}
                  className={`relative inline-flex h-7 w-12 items-center rounded-full transition ${
                    form.preferred_supplier ? "bg-primary" : "bg-surface-container-high"
                  }`}
                >
                  <span
                    className={`inline-block h-5 w-5 rounded-full bg-white shadow transition ${
                      form.preferred_supplier ? "translate-x-6" : "translate-x-1"
                    }`}
                  />
                </button>
              </label>
              <div className="mt-4">
                <TextareaField
                  label="Notes / Remarks"
                  value={form.notes ?? ""}
                  onChange={(value) => updateField("notes", value)}
                  placeholder="Add relationship context, pricing notes, or contract reminders..."
                />
              </div>
            </section>
          </div>
        </form>

        <div className="flex items-center justify-end gap-3 border-t border-outline-variant/10 bg-white px-6 py-4">
          <button
            type="button"
            onClick={onClose}
            className="inline-flex h-11 items-center justify-center rounded-xl border border-outline-variant/20 bg-white px-4 text-sm font-semibold text-on-surface transition hover:bg-surface-container-low"
          >
            Cancel
          </button>
          <button
            type="submit"
            form="supplier-form"
            disabled={isSubmitting}
            className="inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-primary px-5 text-sm font-semibold text-white shadow-sm transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {isSubmitting ? <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" /> : null}
            {mode === "create" ? "Save Supplier" : "Update Supplier"}
          </button>
        </div>
      </div>
    </div>
  );
}
