interface DownloadPdfButtonProps {
  onClick: () => void;
  isLoading?: boolean;
}

export function DownloadPdfButton({ onClick, isLoading = false }: DownloadPdfButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={isLoading}
      className="inline-flex items-center justify-center gap-2 rounded-lg bg-kinetic px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-70"
    >
      {isLoading ? <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" /> : null}
      <span className="material-symbols-outlined text-base">download</span>
      {isLoading ? "Preparing PDF..." : "Download Purchase Order"}
    </button>
  );
}

// anything
