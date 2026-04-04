import { formatLastUpdated } from "../../utils/formatters";

interface HeaderProps {
  title: string;
  lastUpdated: Date | null;
  searchTerm: string;
  onSearchChange: (value: string) => void;
  onRefresh: () => void;
  onMenuClick: () => void;
  searchPlaceholder?: string;
  showRefresh?: boolean;
  showHelp?: boolean;
  subtitle?: string;
  showSearch?: boolean;
}

export function Header({
  title,
  lastUpdated,
  searchTerm,
  onSearchChange,
  onRefresh,
  onMenuClick,
  searchPlaceholder = "Search intel...",
  showRefresh = true,
  showHelp = false,
  subtitle,
  showSearch = true,
}: HeaderProps) {
  return (
    <header className="sticky top-0 z-30 flex h-auto flex-col gap-4 bg-background px-4 py-4 sm:px-6 lg:h-20 lg:flex-row lg:items-center lg:justify-between lg:px-8">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMenuClick}
          className="flex h-10 w-10 items-center justify-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-container-high lg:hidden"
          aria-label="Open navigation"
        >
          <span className="material-symbols-outlined">menu</span>
        </button>
        <div className="flex flex-col gap-1">
          <h2 className="text-[1.85rem] font-bold tracking-tight text-slate-900">{title}</h2>
          {subtitle ? (
            <p className="text-sm text-on-surface-variant">{subtitle}</p>
          ) : null}
          <p className="text-sm font-medium text-on-surface-variant lg:hidden">
            Last updated: {formatLastUpdated(lastUpdated)}
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:gap-8">
        <div className="hidden items-center gap-2 text-sm font-medium text-slate-500 lg:flex">
          <span className="h-2 w-2 animate-pulse rounded-full bg-primary" />
          Last updated: {formatLastUpdated(lastUpdated)}
        </div>

        <div className="flex items-center gap-3">
          {showRefresh ? (
            <button
              type="button"
              onClick={onRefresh}
              className="flex h-10 w-10 items-center justify-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-container-high"
              aria-label="Refresh page data"
            >
              <span className="material-symbols-outlined">refresh</span>
            </button>
          ) : null}

          <button
            type="button"
            className="flex h-10 w-10 items-center justify-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-container-high"
            aria-label="Notifications"
          >
            <span className="material-symbols-outlined">notifications</span>
          </button>

          {showHelp ? (
            <button
              type="button"
              className="flex h-10 w-10 items-center justify-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-container-high"
              aria-label="Help"
            >
              <span className="material-symbols-outlined">help_outline</span>
            </button>
          ) : null}

          {showSearch ? (
            <>
              <div className="hidden h-8 w-px bg-outline-variant/30 sm:block" />
              <label className="flex items-center gap-2 rounded-full bg-surface-container-lowest px-3 py-2 shadow-sm">
                <span className="material-symbols-outlined text-lg text-primary">search</span>
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(event) => onSearchChange(event.target.value)}
                  placeholder={searchPlaceholder}
                  className="w-28 bg-transparent text-sm outline-none placeholder:text-on-surface-variant sm:w-44"
                />
              </label>
            </>
          ) : null}
        </div>
      </div>
    </header>
  );
}
