interface SupplierRowActionsProps {
  onView: () => void;
  onEdit: () => void;
  onDelete: () => void;
  isDeleting?: boolean;
}

export function SupplierRowActions({ onView, onEdit, onDelete, isDeleting }: SupplierRowActionsProps) {
  return (
    <div className="flex items-center justify-end gap-2">
      <button
        type="button"
        onClick={onView}
        className="inline-flex h-9 items-center justify-center rounded-lg border border-outline-variant/20 bg-white px-3 text-xs font-bold uppercase tracking-[0.16em] text-primary transition hover:bg-primary-fixed"
      >
        View
      </button>
      <button
        type="button"
        onClick={onEdit}
        className="inline-flex h-9 items-center justify-center rounded-lg bg-surface-container-high px-3 text-xs font-bold uppercase tracking-[0.16em] text-on-surface transition hover:bg-surface-container"
      >
        Edit
      </button>
      <button
        type="button"
        onClick={onDelete}
        disabled={isDeleting}
        className="inline-flex h-9 items-center justify-center gap-1.5 rounded-lg border border-red-200 bg-white px-3 text-xs font-bold uppercase tracking-[0.16em] text-red-600 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
        aria-label="Delete supplier"
      >
        <span className="material-symbols-outlined text-sm">delete</span>
        {isDeleting ? "…" : "Delete"}
      </button>
    </div>
  );
}

// anything
