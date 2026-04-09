interface QuickPOButtonProps {
  onClick: () => void;
  isLoading?: boolean;
}

export function QuickPOButton({ onClick, isLoading = false }: QuickPOButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={isLoading}
      className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-kinetic py-2.5 text-xs font-bold text-white shadow-sm transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-70"
    >
      {isLoading ? <span className="h-3 w-3 animate-spin rounded-full border-2 border-white/30 border-t-white" /> : null}
      {isLoading ? "Creating PO..." : "Quick PO"}
    </button>
  );
}

// anything
