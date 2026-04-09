import React, { useState, useEffect } from "react";
import { Sidebar } from "../components/layout/Sidebar";
import type { AppPage } from "../types/app.types";
import { manufacturingService } from "../services/manufacturingService";
import type { ManufacturingGoods, ManufacturingGoodsCreate, ManufacturingGoodsUpdate } from "../types/manufacturing.types";
import {
  getPublishedGoods,
  MARKETPLACE_UPDATED_EVENT,
  upsertPublishedGood,
} from "../services/marketplaceService";
import type { PublishedMarketplaceItem } from "../types/marketplace.types";
import { apiGet } from "../services/api";

interface FinishedStocksProps {
  activePage: AppPage;
  onNavigate: (page: AppPage) => void;
}

const generateManufacturingSKU = (name: string): string => {
  const clean = name
    .trim()
    .replace(/[^A-Za-z0-9]+/g, "")
    .slice(0, 5)
    .toUpperCase();
  const suffix = Date.now().toString().slice(-4);
  return `MFG-${clean || "ITEM"}-${suffix}`;
};

const formatCurrency = (value: number): string =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);

const statusToProgress = (status?: string): number => {
  switch (status) {
    case "Work In Progress":
      return 50;
    case "Quality Check":
      return 90;
    case "Done":
      return 100;
    case "On Hold":
      return 30;
    default:
      return 0;
  }
};

export function FinishedStocks({ activePage, onNavigate }: FinishedStocksProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All Categories");
  const [completedManufacturingGoods, setCompletedManufacturingGoods] = useState<ManufacturingGoods[]>([]);
  const [allManufacturingGoods, setAllManufacturingGoods] = useState<ManufacturingGoods[]>([]);
  const [manufacturingLoading, setManufacturingLoading] = useState(false);
  const [totalProducts, setTotalProducts] = useState(0);
  const [activeListings, setActiveListings] = useState(0);
  const [completedCount, setCompletedCount] = useState(0);
  const [lowStockAlerts, setLowStockAlerts] = useState(0);
  const [manufacturingError, setManufacturingError] = useState<string | null>(null);
  const [editingManufacturingId, setEditingManufacturingId] = useState<number | null>(null);
  const [manufacturingForm, setManufacturingForm] = useState<ManufacturingGoodsUpdate>({
    status: "",
    progress: 0,
  });
  const [showAddManufacturingForm, setShowAddManufacturingForm] = useState(false);
  const [newManufacturingForm, setNewManufacturingForm] = useState<ManufacturingGoodsCreate>({
    sku: "",
    product_name: "",
    status: "Pending",
    progress: 0,
    start_date: "",
    est_completion: "",
    unit_price: 0,
  });
  const [publishedGoods, setPublishedGoods] = useState<PublishedMarketplaceItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<ManufacturingGoods | null>(null);
  const [detailMap, setDetailMap] = useState<Record<number, { notes: string; imageUrl: string }>>({});
  const [detailForm, setDetailForm] = useState<{
    product_name: string;
    est_completion: string;
    unit_price: number;
    notes: string;
    imageUrl: string;
  }>({
    product_name: "",
    est_completion: "",
    unit_price: 0,
    notes: "",
    imageUrl: "",
  });

  const [logisticsOrders, setLogisticsOrders] = useState<any[]>([]);

  const reloadManufacturingGoods = async () => {
    setManufacturingLoading(true);
    try {
      const allGoods = await manufacturingService.getAll();
      setAllManufacturingGoods(allGoods);

      const completed = await manufacturingService.getCompleted();
      setCompletedManufacturingGoods(completed);

      const total = allGoods.length;
      const active = allGoods.filter((item) => item.status !== "Done").length;
      const done = allGoods.filter((item) => item.status === "Done").length;
      const lowStock = allGoods.filter((item) => item.progress < 50 || item.status === "Pending").length;

      setTotalProducts(total);
      setActiveListings(active);
      setCompletedCount(done);
      setLowStockAlerts(lowStock);
      setManufacturingError(null);
    } catch (err) {
      setManufacturingError(err instanceof Error ? err.message : "Failed to fetch manufacturing goods");
      console.error("Failed to fetch manufacturing goods:", err);
    } finally {
      setManufacturingLoading(false);
    }
  };

  useEffect(() => {
    const savedPublishedGoods = getPublishedGoods();
    setPublishedGoods(savedPublishedGoods);
    setDetailMap(
      savedPublishedGoods.reduce<Record<number, { notes: string; imageUrl: string }>>((acc, item) => {
        acc[item.id] = {
          notes: item.notes,
          imageUrl: item.imageUrl,
        };
        return acc;
      }, {}),
    );

    reloadManufacturingGoods();
    
    // Fetch logistics orders
    const fetchOrders = async () => {
      try {
        const orders = await apiGet<any[]>("/logistics/orders/");
        setLogisticsOrders(orders);
      } catch (err) {
        console.error("Failed to fetch logistics orders", err);
      }
    };
    fetchOrders();

    const handleLogisticsOrdersUpdated = () => fetchOrders();
    window.addEventListener("logistics-orders-updated", handleLogisticsOrdersUpdated);

    return () => {
      window.removeEventListener("logistics-orders-updated", handleLogisticsOrdersUpdated);
    };
  }, []);

  useEffect(() => {
    const syncPublishedGoods = () => {
      const savedPublishedGoods = getPublishedGoods();
      setPublishedGoods(savedPublishedGoods);
      setDetailMap((prev) => ({
        ...prev,
        ...savedPublishedGoods.reduce<Record<number, { notes: string; imageUrl: string }>>((acc, item) => {
          acc[item.id] = {
            notes: item.notes,
            imageUrl: item.imageUrl,
          };
          return acc;
        }, {}),
      }));
    };

    window.addEventListener(MARKETPLACE_UPDATED_EVENT, syncPublishedGoods);
    return () => window.removeEventListener(MARKETPLACE_UPDATED_EVENT, syncPublishedGoods);
  }, []);

  const openDetails = (item: ManufacturingGoods) => {
    const saved = detailMap[item.id] ?? { notes: "", imageUrl: "" };
    setSelectedItem(item);
    setDetailForm({
      product_name: item.product_name,
      est_completion: item.est_completion ?? "",
      unit_price: item.unit_price,
      notes: saved.notes,
      imageUrl: saved.imageUrl,
    });
  };

  const closeDetails = () => {
    setSelectedItem(null);
  };

  const persistDetails = (updatedItem: ManufacturingGoods, publish = false) => {
    setCompletedManufacturingGoods((prev) =>
      prev.map((item) => (item.id === updatedItem.id ? updatedItem : item))
    );
    setDetailMap((prev) => ({
      ...prev,
      [updatedItem.id]: {
        notes: detailForm.notes,
        imageUrl: detailForm.imageUrl,
      },
    }));
    const alreadyPublished = publishedGoods.some((item) => item.id === updatedItem.id);
    if (publish || alreadyPublished) {
      upsertPublishedGood(updatedItem, {
        notes: detailForm.notes,
        imageUrl: detailForm.imageUrl,
      });
      setPublishedGoods(getPublishedGoods());
    }
    setSelectedItem(updatedItem);
  };

  const saveDetails = () => {
    if (!selectedItem) return;

    const updatedItem: ManufacturingGoods = {
      ...selectedItem,
      product_name: detailForm.product_name,
      est_completion: detailForm.est_completion || null,
      unit_price: detailForm.unit_price,
    };

    persistDetails(updatedItem, false);
  };

  const publishDetails = () => {
    if (!selectedItem) return;

    const updatedItem: ManufacturingGoods = {
      ...selectedItem,
      product_name: detailForm.product_name,
      est_completion: detailForm.est_completion || null,
      unit_price: detailForm.unit_price,
    };

    persistDetails(updatedItem, true);
    closeDetails();
  };

  const handleDetailChange = (field: keyof typeof detailForm, value: string | number) => {
    setDetailForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result;
      if (typeof result === "string") {
        setDetailForm((prev) => ({ ...prev, imageUrl: result }));
      }
    };
    reader.readAsDataURL(file);
  };

  const selectedPublishedItem = selectedItem
    ? publishedGoods.find((item) => item.id === selectedItem.id)
    : null;
  const publishedDateValue = selectedPublishedItem
    ? new Date(selectedPublishedItem.publishedAt).toLocaleDateString()
    : "Will be set when published";

  const startEditManufacturing = (item: ManufacturingGoods) => {
    setEditingManufacturingId(item.id);
    setManufacturingForm({
      status: item.status,
      progress: item.progress,
    });
  };

  const handleSaveManufacturing = async () => {
    if (!editingManufacturingId) return;

    try {
      const payload = {
        ...manufacturingForm,
        status: manufacturingForm.status,
        progress: manufacturingForm.status ? statusToProgress(manufacturingForm.status) : manufacturingForm.progress,
      };

      await manufacturingService.update(editingManufacturingId, payload);
      setEditingManufacturingId(null);
      setManufacturingForm({ status: "", progress: 0 });
      await reloadManufacturingGoods();
    } catch (err) {
      console.error("Failed to update manufacturing goods:", err);
    }
  };

  const handleCancelManufacturingEdit = () => {
    setEditingManufacturingId(null);
    setManufacturingForm({ status: "", progress: 0 });
  };

  const handleManufacturingFormChange = (field: string, value: any) => {
    setManufacturingForm((prev) => {
      if (field === "status") {
        return { ...prev, status: value, progress: statusToProgress(value) };
      }

      return { ...prev, [field]: value };
    });
  };

  const handleAddManufacturingGoods = async () => {
    if (!newManufacturingForm.sku || !newManufacturingForm.product_name || !newManufacturingForm.unit_price) {
      setManufacturingError("SKU, Name and Unit Price are required.");
      return;
    }

    try {
      setManufacturingLoading(true);
      await manufacturingService.create({
        ...newManufacturingForm,
        progress: statusToProgress(newManufacturingForm.status),
      });
      setShowAddManufacturingForm(false);
      setNewManufacturingForm({
        sku: "",
        product_name: "",
        status: "Pending",
        progress: 0,
        start_date: "",
        est_completion: "",
        unit_price: 0,
      });
      await reloadManufacturingGoods();
    } catch (err) {
      setManufacturingError(err instanceof Error ? err.message : "Failed to add manufacturing goods.");
    } finally {
      setManufacturingLoading(false);
    }
  };

  const handleNewManufacturingChange = (field: keyof ManufacturingGoodsCreate, value: any) => {
    setNewManufacturingForm((prev) => {
      if (field === "product_name") {
        return {
          ...prev,
          product_name: value,
          sku: generateManufacturingSKU(value),
        };
      }

      if (field === "status") {
        return {
          ...prev,
          status: value,
          progress: statusToProgress(value),
        };
      }

      return { ...prev, [field]: value };
    });
  };

  return (
    <div className="min-h-screen bg-background text-on-surface font-body">
      <Sidebar isOpen={false} onClose={() => {}} activePage={activePage} onNavigate={onNavigate} />

      {/* Main Canvas */}
      <main className="min-h-screen lg:ml-[240px] p-6 md:p-8 space-y-8 pb-24 md:pb-8">
        {/* Smart Summary Header */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Metric Card 1 */}
          <div className="glass-card p-6 rounded-xl border border-outline-variant/20 shadow-sm flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="material-symbols-outlined text-primary bg-primary-container/10 p-2 rounded-lg">inventory</span>
              <span className="text-[10px] font-bold text-green-600 bg-green-100 px-2 py-0.5 rounded-full">+4%</span>
            </div>
            <h3 className="text-secondary font-medium text-sm">Total Products</h3>
            <p className="text-3xl font-headline font-extrabold text-on-surface">{totalProducts}</p>
          </div>
          {/* Metric Card 2 */}
          <div className="glass-card p-6 rounded-xl border border-outline-variant/20 shadow-sm flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="material-symbols-outlined text-primary bg-primary-container/10 p-2 rounded-lg">box</span>
              <span className="text-[10px] font-bold text-on-surface bg-surface-container-high px-2 py-0.5 rounded-full">Stable</span>
            </div>
            <h3 className="text-secondary font-medium text-sm">Completed Items</h3>
            <p className="text-3xl font-headline font-extrabold text-on-surface">{completedCount}</p>
          </div>
          {/* Metric Card 3 */}
          <div className="glass-card p-6 rounded-xl border border-outline-variant/20 shadow-sm flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="material-symbols-outlined text-primary bg-primary-container/10 p-2 rounded-lg">list_alt</span>
              <span className="text-[10px] font-bold text-green-600 bg-green-100 px-2 py-0.5 rounded-full">Active</span>
            </div>
            <h3 className="text-secondary font-medium text-sm">Active Listings</h3>
            <p className="text-3xl font-headline font-extrabold text-on-surface">{activeListings}</p>
          </div>
          {/* Metric Card 4 */}
          <div className="glass-card p-6 rounded-xl border border-outline-variant/20 shadow-sm flex flex-col gap-2 ring-2 ring-error/10 bg-error/5">
            <div className="flex items-center justify-between">
              <span className="material-symbols-outlined text-error bg-error-container/20 p-2 rounded-lg">warning</span>
              <span className="text-[10px] font-bold text-error bg-error-container px-2 py-0.5 rounded-full">Critical</span>
            </div>
            <h3 className="text-error font-medium text-sm">Low Stock Alerts</h3>
            <p className="text-3xl font-headline font-extrabold text-error">{lowStockAlerts}</p>
          </div>
        </section>

        {/* Search & Filter Area */}
        <section className="flex flex-col md:flex-row items-center gap-4 w-full bg-surface-container-low p-4 rounded-2xl">
          <div className="relative w-full md:w-96 group">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-secondary group-focus-within:text-primary transition-colors">search</span>
            <input
              className="w-full bg-surface-container-high border-transparent focus:border-primary focus:bg-surface-container-lowest focus:ring-0 rounded-xl pl-10 pr-4 py-2 text-sm transition-all"
              placeholder="Search product name or SKU..."
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="flex overflow-x-auto gap-2 no-scrollbar w-full py-1">
            <button
              className={`whitespace-nowrap px-4 py-2 rounded-full text-xs font-bold transition-transform active:scale-95 ${
                selectedCategory === "All Categories"
                  ? "bg-primary text-white"
                  : "bg-surface-container-high text-secondary hover:bg-surface-container-highest"
              }`}
              onClick={() => setSelectedCategory("All Categories")}
            >
              All Categories
            </button>
            <button
              className={`whitespace-nowrap px-4 py-2 rounded-full text-xs font-semibold transition-all ${
                selectedCategory === "Electronics"
                  ? "bg-primary text-white"
                  : "bg-surface-container-high text-secondary hover:bg-surface-container-highest"
              }`}
              onClick={() => setSelectedCategory("Electronics")}
            >
              Electronics
            </button>
            <button
              className={`whitespace-nowrap px-4 py-2 rounded-full text-xs font-semibold transition-all ${
                selectedCategory === "Home Decor"
                  ? "bg-primary text-white"
                  : "bg-surface-container-high text-secondary hover:bg-surface-container-highest"
              }`}
              onClick={() => setSelectedCategory("Home Decor")}
            >
              Home Decor
            </button>
            <button
              className={`whitespace-nowrap px-4 py-2 rounded-full text-xs font-semibold transition-all ${
                selectedCategory === "Apparel"
                  ? "bg-primary text-white"
                  : "bg-surface-container-high text-secondary hover:bg-surface-container-highest"
              }`}
              onClick={() => setSelectedCategory("Apparel")}
            >
              Apparel
            </button>
            <div className="h-6 w-[1px] bg-outline-variant/30 mx-2 self-center"></div>
            <button className="whitespace-nowrap px-4 py-2 rounded-full bg-surface-container-high text-secondary hover:bg-surface-container-highest text-xs font-semibold transition-all flex items-center gap-2">
              Stock Status <span className="material-symbols-outlined text-xs">expand_more</span>
            </button>
            <button className="whitespace-nowrap px-4 py-2 rounded-full bg-surface-container-high text-secondary hover:bg-surface-container-highest text-xs font-semibold transition-all flex items-center gap-2">
              Listing Type <span className="material-symbols-outlined text-xs">expand_more</span>
            </button>
          </div>
        </section>

        <section className="rounded-xl border border-surface-container-high bg-surface-container-lowest overflow-hidden">
          <div className="p-5 border-b border-surface-container-high flex justify-between items-center">
            <h3 className="text-lg font-bold">Manufacturing Goods</h3>
            <span className="text-sm text-slate-500 bg-slate-100 px-3 py-1 rounded-full">{allManufacturingGoods.length} items</span>
          </div>

          <div className="p-5 flex flex-col md:flex-row md:items-center md:justify-between gap-3 bg-surface-container-lowest border-b border-surface-container-high">
            <button
              onClick={() => setShowAddManufacturingForm((prev) => !prev)}
              className="rounded-lg bg-primary px-4 py-2 text-white hover:bg-primary/90"
            >
              {showAddManufacturingForm ? "Hide Add Task" : "Add Manufacturing Task"}
            </button>
            <span className="text-sm text-slate-500">{allManufacturingGoods.length} tasks currently</span>
          </div>

          {manufacturingError && (
            <div className="p-4 bg-red-50 border-l-4 border-red-500">
              <p className="text-red-700">{manufacturingError}</p>
            </div>
          )}

          {showAddManufacturingForm && (
            <div className="p-5 border-b border-surface-container-high bg-surface-container-lowest">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="flex flex-col">
                  <input
                    className="rounded-lg border px-3 py-2 bg-slate-50"
                    value={newManufacturingForm.sku}
                    readOnly
                    placeholder="Auto-generated SKU"
                    title="SKU is auto-generated from the product name"
                  />
                  <p className="text-xs text-slate-500 mt-1">SKU is auto-generated and unique; you can change product name if needed.</p>
                </div>
                <div className="flex flex-col">
                  <input
                    className="rounded-lg border px-3 py-2"
                    placeholder="Product Name"
                    value={newManufacturingForm.product_name}
                    onChange={(e) => handleNewManufacturingChange("product_name", e.target.value)}
                  />
                  <p className="text-xs text-slate-500 mt-1">Enter the manufacturing product name.</p>
                </div>
                <select
                  className="rounded-lg border px-3 py-2"
                  value={newManufacturingForm.status}
                  onChange={(e) => handleNewManufacturingChange("status", e.target.value)}
                >
                  <option value="Pending">Pending</option>
                  <option value="Work In Progress">Work In Progress</option>
                  <option value="Quality Check">Quality Check</option>
                  <option value="Done">Done</option>
                  <option value="On Hold">On Hold</option>
                </select>
                <div className="flex flex-col">
                  <input
                    type="text"
                    className="rounded-lg border px-3 py-2 bg-slate-50"
                    value={`${statusToProgress(newManufacturingForm.status)}%`}
                    readOnly
                    placeholder="Progress based on status"
                  />
                  <p className="text-xs text-slate-500 mt-1">Progress is auto-derived from status and cannot be set manually.</p>
                </div>

                <div className="flex flex-col">
                  <input
                    type="date"
                    className="rounded-lg border px-3 py-2"
                    value={newManufacturingForm.start_date || ""}
                    onChange={(e) => handleNewManufacturingChange("start_date", e.target.value)}
                  />
                  <p className="text-xs text-slate-500 mt-1">Start date of manufacturing run.</p>
                </div>
                <div className="flex flex-col">
                  <input
                    type="date"
                    className="rounded-lg border px-3 py-2"
                    value={newManufacturingForm.est_completion || ""}
                    onChange={(e) => handleNewManufacturingChange("est_completion", e.target.value)}
                  />
                  <p className="text-xs text-slate-500 mt-1">Estimated completion date.</p>
                </div>
                <div className="flex flex-col">
                  <input
                    type="number"
                    min={0}
                    step="0.01"
                    className="rounded-lg border px-3 py-2"
                    placeholder="Unit Price (INR)"
                    value={newManufacturingForm.unit_price}
                    onChange={(e) => handleNewManufacturingChange("unit_price", Number(e.target.value))}
                  />
                  <p className="text-xs text-slate-500 mt-1">Cost per unit in INR. 0 means price not set yet.</p>
                </div>
                <div className="md:col-span-2 flex gap-2">
                  <button
                    onClick={handleAddManufacturingGoods}
                    className="rounded-lg bg-green-600 px-4 py-2 text-white hover:bg-green-700"
                  >
                    Save Task
                  </button>
                  <button
                    onClick={() => setShowAddManufacturingForm(false)}
                    className="rounded-lg bg-slate-200 px-4 py-2 text-slate-800 hover:bg-slate-300"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-surface-container-high">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-slate-700">SKU</th>
                  <th className="px-4 py-3 text-left font-semibold text-slate-700">PRODUCT NAME</th>
                  <th className="px-4 py-3 text-left font-semibold text-slate-700">STATUS</th>
                  <th className="px-4 py-3 text-center font-semibold text-slate-700">PROGRESS</th>
                  <th className="px-4 py-3 text-left font-semibold text-slate-700">START DATE</th>
                  <th className="px-4 py-3 text-left font-semibold text-slate-700">EST. COMPLETION</th>
                  <th className="px-4 py-3 text-center font-semibold text-slate-700">ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {manufacturingLoading ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <tr key={i} className="animate-pulse border-b">
                      <td colSpan={7} className="p-4 bg-slate-100" />
                    </tr>
                  ))
                ) : (
                  allManufacturingGoods.map((item) => (
                    <tr key={item.id} className="border-b hover:bg-slate-50 transition">
                      <td className="px-4 py-3 font-mono text-xs text-slate-600">{item.sku}</td>
                      <td className="px-4 py-3 font-semibold">{item.product_name}</td>
                      <td className="px-4 py-3">
                        {editingManufacturingId === item.id ? (
                          <select
                            value={manufacturingForm.status || item.status}
                            onChange={(e) => handleManufacturingFormChange("status", e.target.value)}
                            className="w-full rounded-lg border border-slate-300 px-2 py-1"
                          >
                            <option value="Pending">Pending</option>
                            <option value="Work In Progress">Work In Progress</option>
                            <option value="Quality Check">Quality Check</option>
                            <option value="Done">Done</option>
                            <option value="On Hold">On Hold</option>
                          </select>
                        ) : (
                          <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold ${
                            item.status === "Done" ? "bg-green-100 text-green-700" :
                            item.status === "Work In Progress" ? "bg-blue-100 text-blue-700" :
                            item.status === "Quality Check" ? "bg-yellow-100 text-yellow-700" :
                            item.status === "On Hold" ? "bg-red-100 text-red-700" :
                            "bg-purple-100 text-purple-700"
                          }`}>
                            {item.status === "Done" ? "Done" :
                             item.status === "Work In Progress" ? "Work In Progress" :
                             item.status === "Quality Check" ? "Quality Check" :
                             item.status === "On Hold" ? "On Hold" :
                             "Pending"}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-20 h-2 bg-slate-200 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                (editingManufacturingId === item.id ? manufacturingForm.status : item.status) === "Done" ? "bg-green-500" :
                                (editingManufacturingId === item.id ? manufacturingForm.status : item.status) === "Work In Progress" ? "bg-blue-500" :
                                (editingManufacturingId === item.id ? manufacturingForm.status : item.status) === "Quality Check" ? "bg-yellow-500" :
                                (editingManufacturingId === item.id ? manufacturingForm.status : item.status) === "On Hold" ? "bg-red-500" :
                                "bg-purple-500"
                              }`}
                              style={{ width: `${editingManufacturingId === item.id ? manufacturingForm.progress : item.progress}%` }}
                            />
                          </div>
                          <span className="text-xs font-semibold text-slate-600">
                            {editingManufacturingId === item.id ? manufacturingForm.progress : item.progress}%
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-slate-600">
                        {item.start_date ? new Date(item.start_date).toLocaleDateString() : "N/A"}
                      </td>
                      <td className="px-4 py-3 text-slate-600">
                        {item.status === "Done" ? (
                          <span className="text-green-600 font-semibold">Completed</span>
                        ) : item.est_completion ? (
                          new Date(item.est_completion).toLocaleDateString()
                        ) : (
                          "TBD"
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        {editingManufacturingId === item.id ? (
                          <div className="flex gap-2 justify-center">
                            <button
                              onClick={handleSaveManufacturing}
                              className="rounded-lg bg-green-600 px-2 py-1 text-white hover:bg-green-700 text-xs"
                            >
                              Save
                            </button>
                            <button
                              onClick={handleCancelManufacturingEdit}
                              className="rounded-lg bg-gray-200 px-2 py-1 text-slate-700 hover:bg-gray-300 text-xs"
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => startEditManufacturing(item)}
                            className="text-blue-600 hover:text-blue-800 font-semibold hover:bg-blue-50 px-2 py-1 rounded"
                            title="Edit"
                          >
                            Edit
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* Completed Manufacturing Goods Section */}
        <section className="mt-8">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-2xl font-bold text-on-surface">Finished                                                                                                                                                                          Goods</h3>
            <span className="text-sm text-slate-500 bg-slate-100 px-3 py-1 rounded-full">
              {completedManufacturingGoods.length} completed items
            </span>
          </div>

          {manufacturingLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
              <p className="text-sm text-secondary mt-2">Loading completed goods...</p>
            </div>
          ) : completedManufacturingGoods.length === 0 ? (
            <div className="text-center py-12 bg-surface-container-low rounded-2xl">
              <span className="material-symbols-outlined text-secondary/30 text-4xl block mb-2">factory</span>
              <p className="text-sm font-medium text-secondary">No completed manufacturing goods yet.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {completedManufacturingGoods.map((item) => (
                <div key={item.id} className="bg-surface-container-lowest rounded-2xl overflow-hidden border border-outline-variant/10 shadow-sm hover:shadow-md transition-shadow">
                  <div className="p-6">
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
                      <div className="min-w-0">
                        <span className="text-[10px] font-bold text-primary tracking-widest uppercase mb-1 block truncate">
                          Manufacturing • SKU: {item.sku}
                        </span>
                        <h4 className="text-lg font-headline font-extrabold text-on-surface leading-tight truncate">
                          {item.product_name}
                        </h4>
                      </div>
                      <span className="whitespace-nowrap px-3 py-1 rounded-full bg-green-100 text-green-700 text-[10px] font-bold uppercase tracking-tight">
                        ✓ Completed
                      </span>
                    </div>

                    <div className="space-y-3">
                      <div className="flex justify-between text-xs font-medium">
                        <span className="text-secondary">Progress</span>
                        <span className="text-on-surface">{item.progress}%</span>
                      </div>
                      <div className="h-2 w-full bg-surface-container rounded-full overflow-hidden">
                        <div className="h-full bg-green-500 rounded-full" style={{ width: `${item.progress}%` }}></div>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-6 pt-6 border-t border-outline-variant/10">
                      <div>
                        <p className="text-[10px] text-secondary font-bold uppercase">Unit Price</p>
                        <p className="text-lg font-extrabold text-on-surface">{formatCurrency(item.unit_price)}</p>
                      </div>
                      <div className="flex flex-col items-start sm:items-end gap-2">
                        <span className="text-[10px] font-bold text-secondary uppercase">Completion Date</span>
                        <span className="text-sm font-bold text-on-surface">
                          {item.est_completion ? new Date(item.est_completion).toLocaleDateString() : 'N/A'}
                        </span>
                      </div>
                    </div>

                    <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mt-6">
                      <button
                        type="button"
                        onClick={() => openDetails(item)}
                        className="border border-outline-variant text-secondary px-4 py-2 rounded-lg text-sm font-semibold hover:bg-surface-container-low transition-all active:scale-95 whitespace-nowrap"
                      >
                        View Details
                      </button>
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full bg-green-500" />
                        <span className="text-xs font-bold text-secondary uppercase tracking-wide">
                          Ready for Sale
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="mt-10">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-2xl font-bold text-on-surface">Published Goods</h3>
            <span className="text-sm text-slate-500 bg-slate-100 px-3 py-1 rounded-full">
              {publishedGoods.length} published items
            </span>
          </div>

          {publishedGoods.length === 0 ? (
            <div className="rounded-2xl bg-surface-container-low p-8 text-center text-sm text-secondary">
              No published goods yet.
            </div>
          ) : (
            <div className="overflow-x-auto rounded-3xl border border-outline-variant/10 bg-surface-container-lowest">
              <table className="min-w-full divide-y divide-outline-variant/10 text-sm">
                <thead className="bg-surface-container-high">
                  <tr>
                    <th className="px-4 py-3 text-left font-semibold text-secondary">SKU</th>
                    <th className="px-4 py-3 text-left font-semibold text-secondary">Product</th>
                    <th className="px-4 py-3 text-left font-semibold text-secondary">Status</th>
                    <th className="px-4 py-3 text-left font-semibold text-secondary">Progress</th>
                    <th className="px-4 py-3 text-left font-semibold text-secondary">Unit Price</th>
                    <th className="px-4 py-3 text-left font-semibold text-secondary">Completion Date</th>
                    <th className="px-4 py-3 text-right font-semibold text-secondary">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-outline-variant/10 bg-surface-container-lowest">
                  {publishedGoods.map((item) => (
                    <tr key={item.id} className="hover:bg-surface-container-high transition-colors">
                      <td className="px-4 py-3 font-mono text-xs text-slate-500">{item.sku}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          {detailMap[item.id]?.imageUrl ? (
                            <img
                              src={detailMap[item.id].imageUrl}
                              alt={item.product_name}
                              className="h-12 w-12 rounded-2xl object-cover"
                            />
                          ) : (
                            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-surface-container-high text-[10px] text-secondary">
                              No image
                            </div>
                          )}
                          <span className="font-semibold text-on-surface">{item.product_name}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-secondary">{item.status}</td>
                      <td className="px-4 py-3 text-sm text-on-surface">{item.progress}%</td>
                      <td className="px-4 py-3 text-sm text-on-surface">{formatCurrency(item.unit_price)}</td>
                      <td className="px-4 py-3 text-sm text-secondary">
                        {item.est_completion ? new Date(item.est_completion).toLocaleDateString() : "N/A"}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          type="button"
                          onClick={() => openDetails(item)}
                          className="rounded-full bg-surface-container-high px-3 py-1 text-xs font-semibold text-secondary hover:bg-surface-container-lowest"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* Incoming Logistics Orders */}
        <section className="mt-10">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-2xl font-bold text-on-surface">Incoming Retailer Orders</h3>
            <span className="text-sm text-slate-500 bg-slate-100 px-3 py-1 rounded-full">
              {logisticsOrders.length} orders
            </span>
          </div>

          {logisticsOrders.length === 0 ? (
            <div className="rounded-2xl bg-surface-container-low p-8 text-center text-sm text-secondary">
              No orders received from retailers yet.
            </div>
          ) : (
            <div className="overflow-x-auto rounded-3xl border border-outline-variant/10 bg-surface-container-lowest">
              <table className="min-w-full divide-y divide-outline-variant/10 text-sm">
                <thead className="bg-surface-container-high">
                  <tr>
                    <th className="px-4 py-3 text-left font-semibold text-secondary">Retailer</th>
                    <th className="px-4 py-3 text-left font-semibold text-secondary">Product</th>
                    <th className="px-4 py-3 text-left font-semibold text-secondary">Quantity</th>
                    <th className="px-4 py-3 text-left font-semibold text-secondary">Status</th>
                    <th className="px-4 py-3 text-left font-semibold text-secondary">Driver</th>
                    <th className="px-4 py-3 text-right font-semibold text-secondary">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-outline-variant/10 bg-surface-container-lowest">
                  {logisticsOrders.map((order) => (
                    <tr key={order.id} className="hover:bg-surface-container-high transition-colors">
                      <td className="px-4 py-3 text-on-surface font-semibold">{order.retailer_name || "Unknown Retailer"}</td>
                      <td className="px-4 py-3 text-secondary">{order.product_name}</td>
                      <td className="px-4 py-3 text-on-surface font-bold">{order.quantity} units</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded-full text-[10px] font-bold uppercase ${
                          order.status === "Pending" ? "bg-amber-100 text-amber-700" :
                          order.status === "In Progress" || order.status === "Sourced" ? "bg-blue-100 text-blue-700" :
                          "bg-green-100 text-green-700"
                        }`}>
                          {order.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-secondary">{order.driver_id ? `Assigned (ID: ${order.driver_id})` : "Awaiting Assignment"}</td>
                      <td className="px-4 py-3 text-right">
                        {!order.driver_id && (
                          <button
                            type="button"
                            onClick={() => {
                              sessionStorage.setItem("pendingLogisticsOrder", JSON.stringify({
                                destination: order.retailer_location || "Central Retail Hub",
                                productName: order.product_name,
                                quantity: order.quantity
                              }));
                              onNavigate("logistics");
                            }}
                            className="rounded-full bg-primary/10 px-4 py-1.5 text-xs font-bold text-primary hover:bg-primary/20 transition-colors"
                          >
                            Schedule
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {selectedItem ? (
          <div className="fixed inset-0 z-50 overflow-y-auto p-4 bg-slate-950/70">
            <div className="mx-auto flex h-full w-full max-w-3xl flex-col overflow-hidden rounded-3xl bg-surface text-on-surface shadow-2xl max-h-[calc(100vh-4rem)]">
              <div className="flex items-center justify-between gap-4 border-b border-outline-variant/20 px-6 py-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-secondary">Product Details</p>
                  <h2 className="text-2xl font-bold">{selectedItem.product_name}</h2>
                  <p className="text-sm text-secondary">SKU: {selectedItem.sku}</p>
                </div>
                <button
                  type="button"
                  onClick={closeDetails}
                  className="rounded-full p-2 text-secondary transition hover:bg-surface-container-highest"
                >
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>

              <div className="grid flex-1 gap-6 overflow-y-auto px-6 py-6 sm:grid-cols-[1.2fr_0.8fr]">
                <div className="space-y-5">
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-secondary">Product Name</label>
                    <input
                      value={detailForm.product_name}
                      onChange={(e) => handleDetailChange("product_name", e.target.value)}
                      className="w-full rounded-2xl border border-outline-variant/60 bg-surface-container-lowest px-4 py-3 text-sm text-on-surface focus:border-primary focus:ring-0"
                    />
                  </div>

                    <div className="space-y-2">
                      <label className="text-sm font-semibold text-secondary">Unit Price</label>
                      <input
                        type="number"
                        value={detailForm.unit_price}
                        onChange={(e) => handleDetailChange("unit_price", Number(e.target.value))}
                        className="w-full rounded-2xl border border-outline-variant/60 bg-surface-container-lowest px-4 py-3 text-sm text-on-surface focus:border-primary focus:ring-0"
                      />
                    </div>

                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-secondary">Published Date</label>
                    <input
                      value={publishedDateValue}
                      readOnly
                      className="w-full rounded-2xl border border-outline-variant/60 bg-surface-container-lowest px-4 py-3 text-sm text-on-surface"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-secondary">Additional Product Notes</label>
                    <textarea
                      value={detailForm.notes}
                      onChange={(e) => handleDetailChange("notes", e.target.value)}
                      rows={4}
                      placeholder="Add product features, storage instructions, or any helpful details."
                      className="w-full rounded-2xl border border-outline-variant/60 bg-surface-container-lowest px-4 py-3 text-sm text-on-surface focus:border-primary focus:ring-0"
                    />
                  </div>
                </div>

                <div className="space-y-5">
                  <div className="rounded-3xl border border-outline-variant/10 bg-surface-container-lowest p-4">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-semibold text-secondary">Product Image</p>
                      <span className="text-xs text-secondary">optional</span>
                    </div>
                    <label className="mt-4 flex cursor-pointer items-center justify-center rounded-2xl border border-dashed border-outline-variant/60 bg-surface-container-high px-4 py-5 text-center text-sm text-secondary transition hover:border-primary hover:text-primary">
                      <input type="file" accept="image/*" hidden onChange={handleImageUpload} />
                      Choose an image file
                    </label>
                    {detailForm.imageUrl ? (
                      <img src={detailForm.imageUrl} alt="Product preview" className="mt-4 h-44 w-full rounded-3xl object-cover shadow-sm" />
                    ) : (
                      <div className="mt-4 flex h-44 items-center justify-center rounded-3xl border border-dashed border-outline-variant/50 bg-surface-container-low text-sm text-secondary">
                        No image added yet
                      </div>
                    )}
                  </div>

                  <div className="rounded-3xl border border-outline-variant/10 bg-surface-container-lowest p-4">
                    <p className="text-sm font-semibold text-secondary mb-3">Quick info</p>
                    <div className="space-y-3 text-sm text-secondary">
                      <div className="flex justify-between">
                        <span>SKU</span>
                        <span className="font-semibold text-on-surface">{selectedItem.sku}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex flex-col gap-3 border-t border-outline-variant/20 px-6 py-4 sm:flex-row sm:items-center sm:justify-end">
                <button
                  type="button"
                  onClick={closeDetails}
                  className="w-full rounded-2xl border border-outline-variant px-4 py-3 text-sm font-semibold text-secondary hover:bg-surface-container-high sm:w-auto"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={saveDetails}
                  className="w-full rounded-2xl border border-outline-variant px-4 py-3 text-sm font-semibold text-secondary hover:bg-surface-container-high sm:w-auto"
                >
                  Save
                </button>
                <button
                  type="button"
                  onClick={publishDetails}
                  className="w-full rounded-2xl bg-primary px-4 py-3 text-sm font-semibold text-white hover:bg-primary/90 sm:w-auto"
                >
                  Publish
                </button>
              </div>
            </div>
          </div>
        ) : null}
      </main>

      {/* BottomNavBar (Mobile Only) */}
      <nav className="md:hidden fixed bottom-0 left-0 w-full flex justify-around items-center px-4 py-2 bg-white/60 dark:bg-slate-900/60 backdrop-blur-xl border-t border-[#c4c5d5]/20 z-50 rounded-t-2xl shadow-[0_-8px_32px_rgba(19,27,46,0.06)]">
        <a className="flex flex-col items-center justify-center bg-[#00288e] text-white rounded-xl py-2 px-4 transition-transform active:scale-110 duration-300" href="#" onClick={(e) => { e.preventDefault(); onNavigate("dashboard"); }}>
          <span className="material-symbols-outlined">home</span>
          <span className="font-['Inter'] text-[10px] font-semibold uppercase tracking-wider">Home</span>
        </a>
        <a className="flex flex-col items-center justify-center text-[#515f74] dark:text-slate-400 py-2 px-4 hover:text-[#00288e] transition-transform active:scale-110 duration-300" href="#" onClick={(e) => e.preventDefault()}>
          <span className="material-symbols-outlined">search</span>
          <span className="font-['Inter'] text-[10px] font-semibold uppercase tracking-wider">Search</span>
        </a>
        <a className="flex flex-col items-center justify-center text-[#515f74] dark:text-slate-400 py-2 px-4 hover:text-[#00288e] transition-transform active:scale-110 duration-300" href="#" onClick={(e) => e.preventDefault()}>
          <span className="material-symbols-outlined">notifications_active</span>
          <span className="font-['Inter'] text-[10px] font-semibold uppercase tracking-wider">Alerts</span>
        </a>
        <a className="flex flex-col items-center justify-center text-[#515f74] dark:text-slate-400 py-2 px-4 hover:text-[#00288e] transition-transform active:scale-110 duration-300" href="#" onClick={(e) => e.preventDefault()}>
          <span className="material-symbols-outlined">settings</span>
          <span className="font-['Inter'] text-[10px] font-semibold uppercase tracking-wider">Settings</span>
        </a>
      </nav>

    </div>
  );
}
