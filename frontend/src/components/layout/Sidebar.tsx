import type { AppPage } from "../../types/app.types";

const navItems: Array<{ label: string; icon: string; page?: AppPage }> = [
  { label: "Dashboard", icon: "dashboard", page: "dashboard" },
  { label: "AI TOOLS", icon: "auto_awesome" },
  { label: "Inventory", icon: "inventory_2", page: "inventory" },
  { label: "Demand Forecasting", icon: "query_stats" },
  { label: "Logistics", icon: "local_shipping", page: "logistics" },
  { label: "Procurement Intelligence", icon: "handshake", page: "procurement" },
  { label: "Purchase Orders", icon: "receipt_long", page: "purchaseOrders" },
  { label: "Settings", icon: "settings" },
];

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  activePage: AppPage;
  onNavigate: (page: AppPage) => void;
}

export function Sidebar({ isOpen, onClose, activePage, onNavigate }: SidebarProps) {
  return (
    <>
      <div
        className={`fixed inset-0 z-40 bg-slate-950/50 transition-opacity duration-200 lg:hidden ${
          isOpen ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
        onClick={onClose}
      />

      <aside
        className={`fixed left-0 top-0 z-50 flex h-full w-[240px] -translate-x-full flex-col bg-slate-900 shadow-2xl transition-transform duration-300 lg:translate-x-0 ${
          isOpen ? "translate-x-0" : ""
        }`}
      >
        <div className="p-6">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-kinetic">
              <span className="material-symbols-outlined text-xl text-white">hub</span>
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white">ChainMind</h1>
              <p className="text-[10px] font-medium uppercase tracking-[0.1em] text-slate-400">
                Supply Intelligence
              </p>
            </div>
          </div>
        </div>

        <nav className="mt-4 flex-1 space-y-1 px-3">
          {navItems.map((item) => (
            <button
              key={item.label}
              type="button"
              onClick={() => {
                if (item.page) {
                  onNavigate(item.page);
                  onClose();
                }
              }}
              className={`flex w-full items-center gap-3 px-4 py-3 text-left text-sm font-medium transition-all duration-200 ${
                item.page === activePage
                  ? "border-l-4 border-primary bg-slate-800/50 text-blue-400"
                  : "text-slate-400 hover:bg-slate-800/30 hover:text-slate-200"
              }`}
            >
              <span className="material-symbols-outlined">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="border-t border-slate-800/70 p-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full border-2 border-slate-700 bg-slate-800 text-sm font-semibold text-slate-100">
              MC
            </div>
            <div className="overflow-hidden">
              <p className="truncate text-sm font-semibold text-white">Marcus Chen</p>
              <p className="truncate text-xs text-slate-500">Plant Operations</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
