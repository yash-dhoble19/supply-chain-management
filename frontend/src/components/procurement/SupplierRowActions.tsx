interface SupplierRowActionsProps {
  onView: () => void;
  onEdit: () => void;
}

export function SupplierRowActions({ onView, onEdit }: SupplierRowActionsProps) {
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
        className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-outline-variant/20 bg-white text-on-surface-variant transition hover:bg-surface-container-low"
        aria-label="More supplier actions"
      >
        <span className="material-symbols-outlined text-base">more_horiz</span>
      </button>
    </div>
  );
}
