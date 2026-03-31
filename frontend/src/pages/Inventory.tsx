import React, { useMemo, useState, useRef, useEffect, useCallback } from "react";
import { Header } from "../components/layout/Header";
import { Sidebar } from "../components/layout/Sidebar";
import { useInventoryData } from "../hooks/useInventoryData";
import { useProcurementInventorySync } from "../hooks/useProcurementInventorySync";
import type { AppPage } from "../types/app.types";
import type { InventoryItem } from "../types/inventory.types";
import { inventoryService } from "../services/inventoryService";

interface InventoryProps {
  activePage: AppPage;
  onNavigate: (page: AppPage) => void;
}

const statusTone = (status: string) => {
  if (status.toLowerCase() === "critical") return "text-red-500";
  if (status.toLowerCase() === "low") return "text-orange-500";
  return "text-green-500";
};

const CATEGORIES = ["Electronics", "Mechanical", "Raw Materials", "Packaging"];
const PIE_COLORS = ["#6366F1", "#EC4899", "#10B981", "#F59E0B", "#3B82F6", "#EF4444"];

// Generate SKU from name and category
const generateSKU = (name: string, category: string): string => {
  if (!name || !category) return "";
  const nameCode = name.slice(0, 3).toUpperCase();
  const categoryCode = category.slice(0, 3).toUpperCase();
  const timestamp = Date.now().toString().slice(-4);
  return `${categoryCode}-${nameCode}-${timestamp}`;
};

// Custom hook for debounced search
function useDebounce<T>(value: T, delay: number) {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
}

// Table row component (no memo for reliable click behavior)
const TableBodyRow = ({ 
  item, 
  isEditing, 
  editingRowId, 
  productForm, 
  categories,
  onEdit, 
  onSave, 
  onCancel, 
  onDelete,
  onFormChange
}: {
  item: InventoryItem;
  isEditing: boolean;
  editingRowId: number | null;
  productForm: any;
  categories: string[];
  onEdit: (item: InventoryItem) => void;
  onSave: () => void;
  onCancel: () => void;
  onDelete: (id: number) => void;
  onFormChange: (field: string, value: any) => void;
}) => {
  if (editingRowId === item.id && isEditing) {
    return (
      <tr className="border-b bg-yellow-50">
        <td className="px-4 py-3 font-mono text-xs text-slate-600">{item.sku}</td>
        <td className="px-4 py-3">
          <input
            value={productForm.name}
            onChange={(e) => onFormChange('name', e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-2 py-1"
          />
        </td>
        <td className="px-4 py-3">
          <select
            value={productForm.category}
            onChange={(e) => onFormChange('category', e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-2 py-1"
          >
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </td>
        <td className="px-4 py-3">
          <input
            type="number"
            value={productForm.current_stock}
            onChange={(e) => onFormChange('current_stock', Number(e.target.value))}
            className="w-full rounded-lg border border-slate-300 px-2 py-1"
          />
        </td>
        <td className={`px-4 py-3 font-semibold ${statusTone(item.status)}`}>{item.status}</td>
        <td className="px-4 py-3">{item.capacity}%</td>
        <td className="px-4 py-3">
          <input
            type="number"
            value={productForm.unit_price}
            onChange={(e) => onFormChange('unit_price', Number(e.target.value))}
            className="w-full rounded-lg border border-slate-300 px-2 py-1"
          />
        </td>
        <td className="px-4 py-3 font-semibold">
          ${((productForm.current_stock || item.stock) * (productForm.unit_price || item.unit_price)).toFixed(2)}
        </td>
        <td className="px-4 py-3 flex gap-2">
          <button
            onClick={onSave}
            className="rounded-lg bg-green-600 px-2 py-1 text-white hover:bg-green-700"
          >
            Save
          </button>
          <button
            onClick={onCancel}
            className="rounded-lg bg-gray-200 px-2 py-1 text-slate-700 hover:bg-gray-300"
          >
            Cancel
          </button>
        </td>
      </tr>
    );
  }

  return (
    <tr className="border-b hover:bg-slate-50 transition">
      <td className="px-4 py-3 font-mono text-xs text-slate-600">{item.sku}</td>
      <td className="px-4 py-3 font-semibold">{item.name}</td>
      <td className="px-4 py-3 text-slate-600">{item.category}</td>
      <td className="px-4 py-3">{item.stock}</td>
      <td className={`px-4 py-3 font-semibold ${statusTone(item.status)}`}>{item.status}</td>
      <td className="px-4 py-3">{item.capacity}%</td>
      <td className="px-4 py-3">${item.unit_price.toFixed(2)}</td>
      <td className="px-4 py-3 font-semibold">${item.total_value.toFixed(2)}</td>
      <td className="px-4 py-3">
        <div className="flex gap-2">
          <button
            onClick={() => onEdit(item)}
            className="text-blue-600 hover:text-blue-800 font-semibold hover:bg-blue-50 px-2 py-1 rounded"
            title="Edit"
          >
            ✏️
          </button>
          <button
            onClick={() => onDelete(item.id)}
            className="text-red-600 hover:text-red-800 font-semibold hover:bg-red-50 px-2 py-1 rounded"
            title="Delete"
          >
            🗑️
          </button>
        </div>
      </td>
    </tr>
  );
};

export function Inventory({ activePage, onNavigate }: InventoryProps) {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 250); // 250ms debounce
  const [showAddForm, setShowAddForm] = useState(false);
  const [showCrystalBall, setShowCrystalBall] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<InventoryItem | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editingRowId, setEditingRowId] = useState<number | null>(null);
  const [formStatus, setFormStatus] = useState<string | null>(null);
  const [categories, setCategories] = useState(CATEGORIES);
  const [showNewCategoryInput, setShowNewCategoryInput] = useState(false);
  const [newCategory, setNewCategory] = useState("");
  const [isMicListening, setIsMicListening] = useState(false);
  const recognitionRef = useRef<any>(null);

  const { items, summary, activity, isLoading, error, refetch, page, limit, total, setPage, setLimit } =
    useInventoryData();

  // Auto-sync Procurement "Delivered" orders to Inventory
  const { syncDeliveredPOs } = useProcurementInventorySync((message) => {
    setFormStatus(message);
    refetch();
  });

  const [productForm, setProductForm] = useState({
    sku: "",
    name: "",
    category: "",
    current_stock: 0,
    safety_stock_level: 10,
    optimal_stock_level: 50,
    unit_price: 0,
  });

  // Reset message when form opens so old messages don't show prematurely
  useEffect(() => {
    if (showAddForm) {
      setFormStatus(null);
    }
  }, [showAddForm]);

  // Initialize Web Speech API
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = "en-US";

      recognitionRef.current.onstart = () => setIsMicListening(true);
      recognitionRef.current.onend = () => setIsMicListening(false);
      recognitionRef.current.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript.toLowerCase();
        parseSpeechInput(transcript);
      };
    }
  }, []);

  const parseSpeechInput = (transcript: string) => {
    // Parse patterns like "Add 20 steel rods for $10 each"
    const patterns = {
      add: /add\s+(\d+)\s+(.+?)\s+for\s+\$?(\d+(?:\.\d{1,2})?)/i,
      simple: /(\d+)\s+(.+?)\s+\$?(\d+(?:\.\d{1,2})?)/i,
    };

    let match = transcript.match(patterns.add) || transcript.match(patterns.simple);
    if (match) {
      const quantity = parseInt(match[1]);
      const name = match[2].trim();
      const price = parseFloat(match[3]);

      // Guess category from name
      let category = "Others";
      if (name.toLowerCase().includes("steel") || name.toLowerCase().includes("metal")) {
        category = "Raw Materials";
      } else if (name.toLowerCase().includes("circuit") || name.toLowerCase().includes("board")) {
        category = "Electronics";
      }

      setProductForm((prev) => ({
        ...prev,
        name,
        category,
        current_stock: quantity,
        unit_price: price,
      }));
      setFormStatus("Voice input parsed successfully!");
    } else {
      setFormStatus("Could not parse voice input. Try: 'Add 20 steel rods for $10 each'");
    }
  };

  const startMicListener = () => {
    if (recognitionRef.current) {
      recognitionRef.current.start();
    }
  };

  const filtered = useMemo(() => {
    if (!debouncedSearch) return items;
    const q = debouncedSearch.toLowerCase();
    return items.filter((item) =>
      [item.sku, item.name, item.category].some((value) => value?.toString().toLowerCase().includes(q)),
    );
  }, [items, debouncedSearch]);

  const categoryDistribution = useMemo(() => {
    const counts = filtered.reduce<Record<string, number>>((acc, item) => {
      acc[item.category] = (acc[item.category] || 0) + 1;
      return acc;
    }, {});

    const total = Object.values(counts).reduce((sum, v) => sum + v, 0);
    return Object.entries(counts)
      .map(([category, value], index) => ({
        category,
        value,
        percent: total ? (value / total) * 100 : 0,
        color: PIE_COLORS[index % PIE_COLORS.length],
      }))
      .sort((a, b) => b.value - a.value);
  }, [filtered]);

  const categoryPieGradient = useMemo(() => {
    if (!categoryDistribution.length) return "";
    let start = 0;
    const segments = categoryDistribution.map((segment) => {
      const end = start + segment.percent;
      const cssSeg = `${segment.color} ${start.toFixed(1)}% ${end.toFixed(1)}%`;
      start = end;
      return cssSeg;
    });
    return `conic-gradient(${segments.join(", ")})`;
  }, [categoryDistribution]);

  const recentActivity = useMemo(() => {
    const unique = new Map<number, typeof activity[0]>();
    activity.forEach((log) => {
      if (!unique.has(log.id)) unique.set(log.id, log);
    });

    return Array.from(unique.values())
      .sort((a, b) => new Date(b.change_date).getTime() - new Date(a.change_date).getTime())
      .slice(0, 20);
  }, [activity]);

  const handleAddProduct = async () => {
    if (!productForm.name || !productForm.category) {
      setFormStatus("Please fill in Name and Category");
      return;
    }

    const finalForm = {
      ...productForm,
      sku: productForm.sku || generateSKU(productForm.name, productForm.category),
      stage: "WAREHOUSE",
    };

    console.log("Inventory create request:", finalForm);

    try {
      const response = await inventoryService.createProduct(finalForm);
      const created = response.product;

      if (!created || !created.id) {
        throw new Error("API did not return created product");
      }

      console.log("Inventory create response:", created);
      setFormStatus("Product created successfully!");
      setProductForm({
        sku: "",
        name: "",
        category: "",
        current_stock: 0,
        safety_stock_level: 10,
        optimal_stock_level: 50,
        unit_price: 0,
      });
      setShowAddForm(false);
      import("../hooks/useInventoryData").then(m => m.clearInventoryCache());
      refetch();
      window.dispatchEvent(new Event("inventory-updated"));
    } catch (err) {
      setFormStatus(`Error: ${err instanceof Error ? err.message : "Failed to create product"}`);
      console.error("Inventory create error:", err);
    }
  };

  const handleEditProduct = async () => {
    if (!selectedProduct) return;
    console.log("handleEditProduct", selectedProduct.id, productForm);

    try {
      await inventoryService.updateProduct(selectedProduct.id, productForm);
      setFormStatus("Product updated successfully!");
      setIsEditing(false);
      setSelectedProduct(null);
      setEditingRowId(null);
      setShowAddForm(false);
      import("../hooks/useInventoryData").then(m => m.clearInventoryCache());
      refetch();
    } catch (err) {
      setFormStatus(`Error: ${err instanceof Error ? err.message : "Failed to update product"}`);
      console.error("handleEditProduct error", err);
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditingRowId(null);
    setSelectedProduct(null);
    setFormStatus(null);
    setProductForm({
      sku: "",
      name: "",
      category: "",
      current_stock: 0,
      safety_stock_level: 10,
      optimal_stock_level: 50,
      unit_price: 0,
    });
  };

  const handleDeleteProduct = async (productId: number) => {
    if (!confirm("Are you sure you want to delete this product?")) return;

    console.log("handleDeleteProduct", productId);

    try {
      const response = await inventoryService.deleteProduct(productId);
      console.log("handleDeleteProduct response", response);
      if (!response || !response.product) {
        throw new Error("API did not return deleted product");
      }
      console.log("Inventory delete response:", response.product);

      import("../hooks/useInventoryData").then(m => m.clearInventoryCache());
      setFormStatus("Product deleted successfully!");
      refetch();
      window.dispatchEvent(new Event("inventory-updated"));
    } catch (err) {
      setFormStatus(`Error: ${err instanceof Error ? err.message : "Failed to delete product"}`);
      console.error("Inventory delete error:", err);
    }
  };
  const startEditProduct = (item: InventoryItem) => {
    console.log("startEditProduct", item);
    setSelectedProduct(item);
    setProductForm({
      sku: item.sku,
      name: item.name,
      category: item.category,
      current_stock: item.stock,
      safety_stock_level: item.safety_stock_level,
      optimal_stock_level: item.optimal_stock_level,
      unit_price: item.unit_price,
    });
    setIsEditing(true);
    setEditingRowId(item.id);
    setShowAddForm(false); // Inline editing in row
    setFormStatus(null);
  };

  const addNewCategory = () => {
    if (newCategory.trim() && !categories.includes(newCategory)) {
      setCategories([...categories, newCategory]);
      setProductForm((prev) => ({ ...prev, category: newCategory }));
      setNewCategory("");
      setShowNewCategoryInput(false);
    }
  };

  const handleFormChange = useCallback((field: string, value: any) => {
    setProductForm((prev) => ({ ...prev, [field]: value }));
  }, []);

  const handleExport = () => {
    inventoryService.exportCsv(filtered);
  };

  return (
    <div className="min-h-screen bg-background text-on-surface">
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setSidebarOpen(false)}
        activePage={activePage}
        onNavigate={onNavigate}
      />

      <main className="min-h-screen lg:ml-[240px]">
        <Header
          title="Inventory"
          lastUpdated={summary ? new Date() : null}
          searchTerm={search}
          onSearchChange={setSearch}
          onRefresh={refetch}
          onMenuClick={() => setSidebarOpen(true)}
          searchPlaceholder="Search SKU, product, category..."
          showRefresh={false}
          showHelp
        />

        <div className="space-y-6 p-4 sm:p-6 lg:p-8">
          {error ? (
            <section className="rounded-2xl border border-error/20 bg-error-container/60 p-6 shadow-panel">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 className="text-lg font-bold text-error">Inventory data unavailable</h3>
                  <p className="mt-2 text-sm text-on-error-container">{error}. Check server and try again.</p>
                </div>
                <button
                  type="button"
                  onClick={refetch}
                  className="inline-flex items-center justify-center rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
                >
                  Retry
                </button>
              </div>
            </section>
          ) : null}

          {/* Summary Cards */}
          <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="rounded-xl border border-surface-container-high p-5 bg-surface-container-lowest">
              <p className="text-xs uppercase tracking-widest text-on-surface-variant">Total Items</p>
              <p className="mt-2 text-3xl font-bold">{summary ? summary.total_items.toLocaleString() : "--"}</p>
              <p className="text-sm text-slate-500">Active stock count</p>
            </div>
            <div className="rounded-xl border border-surface-container-high p-5 bg-surface-container-lowest">
              <p className="text-xs uppercase tracking-widest text-on-surface-variant">Total Value</p>
              <p className="mt-2 text-3xl font-bold">${summary ? summary.total_value.toLocaleString() : "--"}</p>
              <p className="text-sm text-slate-500">Current valuation</p>
            </div>
            <div className="rounded-xl border border-surface-container-high p-5 bg-surface-container-lowest">
              <p className="text-xs uppercase tracking-widest text-on-surface-variant">Critical Items</p>
              <p className="mt-2 text-3xl font-bold text-red-500">{summary ? summary.critical_items : "--"}</p>
              <p className="text-sm text-slate-500">Below safety threshold</p>
            </div>
          </section>

          {/* Add Product Form Modal */}
          {showAddForm ? (
            <section className="rounded-xl border-2 border-primary/50 bg-gradient-to-br from-primary/5 to-primary/10 p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-2xl font-bold">{isEditing ? "Edit Product" : "Add New Product"}</h3>
                <button
                  onClick={() => {
                    setShowAddForm(false);
                    setIsEditing(false);
                    setSelectedProduct(null);
                    setFormStatus(null);
                  }}
                  className="text-slate-500 hover:text-slate-700 text-2xl"
                >
                  ✕
                </button>
              </div>

              {formStatus ? (
                <div className={`mb-4 p-3 rounded-lg ${formStatus.toLowerCase().includes("error") || formStatus.toLowerCase().includes("failed") ? "bg-red-100 text-red-700" : "bg-green-100 text-green-700"}`}>
                  {formStatus}
                </div>
              ) : null}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-semibold mb-2">Product Name</label>
                  <input
                    type="text"
                    value={productForm.name}
                    onChange={(e) => setProductForm((prev) => ({ ...prev, name: e.target.value }))}
                    placeholder="e.g., Steel Rods"
                    className="w-full rounded-lg border border-slate-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-2">Category</label>
                  <div className="flex gap-2">
                    <select
                      value={productForm.category}
                      onChange={(e) => {
                        if (e.target.value === "custom") {
                          setShowNewCategoryInput(true);
                        } else {
                          setProductForm((prev) => ({ ...prev, category: e.target.value }));
                          setShowNewCategoryInput(false);
                        }
                      }}
                      className="flex-1 rounded-lg border border-slate-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                    >
                      <option value="">Select category</option>
                      {categories.map((cat) => (
                        <option key={cat} value={cat}>
                          {cat}
                        </option>
                      ))}
                      <option value="custom">+ Others (custom)</option>
                    </select>
                    {showNewCategoryInput ? (
                      <button
                        onClick={() => addNewCategory()}
                        className="rounded-lg bg-primary px-3 py-2 text-white hover:bg-primary/90"
                      >
                        Add
                      </button>
                    ) : null}
                  </div>
                  {showNewCategoryInput ? (
                    <input
                      type="text"
                      value={newCategory}
                      onChange={(e) => setNewCategory(e.target.value)}
                      placeholder="New category name"
                      className="w-full mt-2 rounded-lg border border-slate-300 px-4 py-2"
                    />
                  ) : null}
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-2">Total Items</label>
                  <input
                    type="number"
                    value={productForm.current_stock}
                    onChange={(e) => setProductForm((prev) => ({ ...prev, current_stock: Number(e.target.value) }))}
                    placeholder="0"
                    className="w-full rounded-lg border border-slate-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-2">Unit Price ($)</label>
                  <input
                    type="number"
                    value={productForm.unit_price}
                    onChange={(e) => setProductForm((prev) => ({ ...prev, unit_price: Number(e.target.value) }))}
                    placeholder="0.00"
                    step="0.01"
                    className="w-full rounded-lg border border-slate-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-2">SKU (Auto-generated)</label>
                  <input
                    type="text"
                    value={productForm.sku || generateSKU(productForm.name, productForm.category)}
                    readOnly
                    className="w-full rounded-lg border border-slate-300 bg-slate-100 px-4 py-2 text-slate-600"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-2">Safety Stock Level</label>
                  <input
                    type="number"
                    value={productForm.safety_stock_level}
                    onChange={(e) => setProductForm((prev) => ({ ...prev, safety_stock_level: Number(e.target.value) }))}
                    placeholder="10"
                    className="w-full rounded-lg border border-slate-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-2">Optimal Stock Level</label>
                  <input
                    type="number"
                    value={productForm.optimal_stock_level}
                    onChange={(e) => setProductForm((prev) => ({ ...prev, optimal_stock_level: Number(e.target.value) }))}
                    placeholder="50"
                    className="w-full rounded-lg border border-slate-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
              </div>

              <div className="mt-6 flex gap-3">
                <button
                  onClick={isEditing ? handleEditProduct : handleAddProduct}
                  className="flex-1 rounded-lg bg-primary px-4 py-3 text-white font-semibold hover:bg-primary/90 transition"
                >
                  {isEditing ? "Save Changes" : "Create Product"}
                </button>
                <button
                  onClick={() => {
                    startMicListener();
                  }}
                  className={`rounded-lg px-4 py-3 font-semibold transition ${
                    isMicListening
                      ? "bg-red-500 text-white hover:bg-red-600"
                      : "border-2 border-primary text-primary hover:bg-primary/5"
                  }`}
                >
                  🎤 {isMicListening ? "Listening..." : "Voice Input"}
                </button>
              </div>
            </section>
          ) : null}

          {/* Quick Stats and Actions */}
          <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="rounded-xl border border-surface-container-high p-5 bg-surface-container-lowest">
              <h3 className="mb-4 text-lg font-bold">Category Pie Chart</h3>
              {categoryDistribution.length === 0 ? (
                <p className="text-sm text-slate-500">No data available for pie chart.</p>
              ) : (
                <div className="flex flex-col items-center gap-4">
                  <div
                    className="h-40 w-40 rounded-full border border-slate-200"
                    style={{ background: categoryPieGradient }}
                    aria-label="Category distribution pie chart"
                  />
                  <ul className="w-full space-y-2">
                    {categoryDistribution.map((slice) => (
                      <li key={slice.category} className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                          <span className="h-2.5 w-2.5 rounded-full" style={{ background: slice.color }} />
                          <span>{slice.category}</span>
                        </div>
                        <span className="text-slate-500">{slice.value} ({slice.percent.toFixed(1)}%)</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <div className="rounded-xl border border-surface-container-high p-5 bg-surface-container-lowest">
              <h3 className="text-lg font-bold mb-4">Actions</h3>
              <div className="space-y-2">
                <button
                  onClick={() => {
                    setShowAddForm(true);
                    setIsEditing(false);
                    setFormStatus(null);
                    setProductForm({
                      sku: "",
                      name: "",
                      category: "",
                      current_stock: 0,
                      safety_stock_level: 10,
                      optimal_stock_level: 50,
                      unit_price: 0,
                    });
                  }}
                  className="w-full rounded-lg border-2 border-primary bg-primary text-white px-4 py-2 hover:bg-primary/90 transition font-semibold"
                >
                  ➕ Add Product
                </button>
                <button
                  onClick={() => handleExport()}
                  className="w-full rounded-lg border-2 border-slate-300 bg-slate-100 text-slate-800 px-4 py-2 hover:bg-slate-200 transition font-semibold"
                >
                  📥 Export CSV
                </button>
                <button
                  onClick={() => setShowCrystalBall(!showCrystalBall)}
                  className="w-full rounded-lg border-2 border-purple-500 text-purple-700 px-4 py-2 hover:bg-purple-50 transition font-semibold"
                >
                  🔮 Crystal Ball
                </button>
              </div>
            </div>
          </section>

          {/* Crystal Ball - Intelligent Advisory */}
          {showCrystalBall ? (
            <section className="rounded-xl border-2 border-purple-400 bg-gradient-to-br from-purple-50 to-indigo-50 p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-2xl font-bold text-purple-900">🔮 Crystal Ball - Advisory System</h3>
                <button onClick={() => setShowCrystalBall(false)} className="text-purple-500 text-2xl">✕</button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Critical Stock Alert */}
                {summary && summary.critical_items > 0 ? (
                  <div className="rounded-lg border-l-4 border-red-500 bg-red-50 p-4">
                    <h4 className="font-bold text-red-700">⚠️ Critical Stock Alert</h4>
                    <p className="text-sm text-red-600 mt-2">{summary.critical_items} items below safety threshold</p>
                    <button className="mt-2 text-sm underline text-red-700 hover:text-red-900">View & Replenish</button>
                  </div>
                ) : null}

                {/* Fire Emergency */}
                <div className="rounded-lg border-l-4 border-orange-500 bg-orange-50 p-4">
                  <h4 className="font-bold text-orange-700">🔥 Fire Emergency Protocol</h4>
                  <ul className="text-sm text-orange-600 mt-2 space-y-1">
                    <li>✓ Alert Emergency Services (911)</li>
                    <li>✓ Activate Sprinkler System</li>
                    <li>✓ Evacuate Zone A & B</li>
                    <li>✓ Secure Critical Documents</li>
                  </ul>
                </div>

                {/* Stockout Prevention */}
                <div className="rounded-lg border-l-4 border-yellow-500 bg-yellow-50 p-4">
                  <h4 className="font-bold text-yellow-700">📦 Stockout Prevention</h4>
                  <ul className="text-sm text-yellow-600 mt-2 space-y-1">
                    <li>✓ Flag items trending toward stockout</li>
                    <li>✓ Auto-suggest reorder quantities</li>
                    <li>✓ Contact suppliers for expedited shipping</li>
                  </ul>
                </div>

                {/* Inventory Optimization */}
                <div className="rounded-lg border-l-4 border-green-500 bg-green-50 p-4">
                  <h4 className="font-bold text-green-700">💡 Inventory Optimization</h4>
                  <ul className="text-sm text-green-600 mt-2 space-y-1">
                    <li>✓ Identify slow-moving items</li>
                    <li>✓ Recommend markdown strategies</li>
                    <li>✓ Optimize warehouse allocation</li>
                  </ul>
                </div>
              </div>
            </section>
          ) : null}

          {/* Inventory Items Table */}
          <section className="rounded-xl border border-surface-container-high p-5 bg-surface-container-lowest">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-4">
              <h3 className="text-lg font-bold">Inventory Items</h3>
              <div className="flex items-center gap-2">
                <select
                  className="rounded-lg border px-3 py-2"
                  value={limit}
                  onChange={(e) => setLimit(Number(e.target.value))}
                >
                  {[10, 20, 30, 50].map((v) => (
                    <option key={v} value={v}>
                      {v} rows
                    </option>
                  ))}
                </select>
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  className="rounded-lg bg-slate-200 px-3 py-2 hover:bg-slate-300"
                >
                  ← Prev
                </button>
                <span className="text-sm text-slate-600">Page {page}</span>
                <button
                  onClick={() => setPage(page + 1)}
                  className="rounded-lg bg-slate-200 px-3 py-2 hover:bg-slate-300"
                >
                  Next →
                </button>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead>
                  <tr className="bg-slate-50">
                    {["SKU", "Product Name", "Category", "Stock", "Status", "Capacity", "Unit Price", "Total Value", "Actions"].map((h) => (
                      <th key={h} className="border-b px-4 py-3 text-slate-700 font-semibold text-xs uppercase">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {isLoading
                    ? Array.from({ length: 6 }).map((_, i) => (
                        <tr key={i} className="animate-pulse border-b">
                          <td colSpan={9} className="p-4 bg-slate-100" />
                        </tr>
                      ))
                    : filtered.map((item) => (
                        <TableBodyRow
                          key={item.id}
                          item={item}
                          isEditing={isEditing}
                          editingRowId={editingRowId}
                          productForm={productForm}
                          categories={categories}
                          onEdit={startEditProduct}
                          onSave={handleEditProduct}
                          onCancel={handleCancelEdit}
                          onDelete={handleDeleteProduct}
                          onFormChange={handleFormChange}
                        />
                      ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Activity Feed */}
          <section className="rounded-xl border border-surface-container-high p-5 bg-surface-container-lowest">
            <h3 className="text-lg font-bold mb-4">📋 Recent Activity</h3>
            {recentActivity.length === 0 ? (
              <p className="text-sm text-slate-500">No inventory activity yet.</p>
            ) : (
              <ul className="space-y-3">
                {recentActivity.map((act) => (
                  <li key={act.id} className="rounded-lg border border-slate-200 p-3 hover:bg-slate-50 transition">
                    <div className="flex justify-between items-start text-sm">
                      <div>
                        <span className="font-semibold">{act.product_name}</span>
                        <span className="text-slate-500 ml-2">({act.sku})</span>
                      </div>
                      <span className="text-xs text-slate-500">{new Date(act.change_date).toLocaleString()}</span>
                    </div>
                    <div className={`text-xs mt-1 font-semibold ${act.quantity_change > 0 ? "text-green-600" : "text-red-600"}`}>
                      {act.quantity_change > 0 ? "+" : ""}{act.quantity_change} {act.reason}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}
