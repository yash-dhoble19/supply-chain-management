import React, { useEffect, useMemo, useState, useRef } from "react";
import { QRCodeSVG } from "qrcode.react";
import type { AuthRole } from "../services/authService";
import {
  addToCart,
  CART_UPDATED_EVENT,
  clearCart,
  getCartItems,
  removeFromCart,
  replaceCartWithSingleItem,
  setCartItemQuantity,
} from "../services/cartService";
import {
  getPublishedGoods,
  MARKETPLACE_UPDATED_EVENT,
} from "../services/marketplaceService";
import type { CartItem } from "../types/cart.types";
import type { PublishedMarketplaceItem } from "../types/marketplace.types";
import { apiPost } from "../services/api";

interface RetailerDashboardProps {
  user: { name: string; email: string; role: AuthRole };
  onLogout: () => void;
}

type RetailerView = "browse" | "details" | "cart";

function formatDate(value: string | null) {
  if (!value) return "Recently published";
  return new Date(value).toLocaleDateString();
}

function formatPrice(value: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
  }).format(value);
}

function buildPlaceholderImage(item: PublishedMarketplaceItem) {
  const palettes: Record<string, string> = {
    Electronics: "from-cyan-500 via-sky-700 to-slate-950",
    "Safety Gear": "from-amber-300 via-orange-500 to-yellow-700",
    "Raw Materials": "from-slate-400 via-slate-600 to-slate-900",
    "Bulk Supplies": "from-indigo-500 via-blue-700 to-slate-950",
    "Published Goods": "from-rose-300 via-fuchsia-500 to-violet-700",
  };
  return palettes[item.category] ?? palettes["Published Goods"];
}

function getRating(item: PublishedMarketplaceItem) {
  const base = 4.2 + ((item.id % 7) * 0.1);
  return Math.min(4.9, Number(base.toFixed(1)));
}

function getReviewCount(item: PublishedMarketplaceItem) {
  return 24 + item.id * 7;
}

function getPricingTiers(item: PublishedMarketplaceItem) {
  return [
    { label: "1 - 49 Units", minimum: 1, price: item.unit_price, featured: false },
    {
      label: "50 - 199 Units (MOQ)",
      minimum: 50,
      price: Number((item.unit_price * 0.92).toFixed(2)),
      featured: true,
    },
    { label: "200+ Units", minimum: 200, price: Number((item.unit_price * 0.84).toFixed(2)), featured: false },
  ];
}

function getPriceForQuantity(item: PublishedMarketplaceItem, quantity: number) {
  const tiers = getPricingTiers(item);
  if (quantity >= tiers[2].minimum) return tiers[2].price;
  if (quantity >= tiers[1].minimum) return tiers[1].price;
  return tiers[0].price;
}

function getAppliedPricingTier(item: PublishedMarketplaceItem, quantity: number) {
  const tiers = getPricingTiers(item);
  if (quantity >= tiers[2].minimum) return tiers[2];
  if (quantity >= tiers[1].minimum) return tiers[1];
  return tiers[0];
}

function getTierStartingQuantity(minimum: number) {
  if (minimum >= 200) return 200;
  if (minimum >= 50) return 50;
  return 25;
}

function getProductHighlights(item: PublishedMarketplaceItem) {
  const highlights: Record<string, string[]> = {
    Electronics: [
      "Industrial-grade component quality",
      "Ready for bulk retailer procurement",
      "Protected packaging for transit safety",
      "Stable supply from finished stocks",
    ],
    "Safety Gear": [
      "Compliance-friendly protection stock",
      "Suitable for bulk procurement cycles",
      "Reliable fit and finish for retail sale",
      "Finished-stock availability for faster dispatch",
    ],
    "Raw Materials": [
      "Consistent production-ready material quality",
      "Bulk volume pricing for retailers",
      "Warehouse-backed finished inventory",
      "Suitable for repeat reorder programs",
    ],
    "Bulk Supplies": [
      "Designed for high-volume retail operations",
      "Bulk-buy savings across larger quantities",
      "Reliable manufacturer-published stock",
      "Fast quote-to-order workflow",
    ],
    "Published Goods": [
      "Published directly from manufacturer inventory",
      "Ready to request quotes and place orders",
      "Bulk-friendly pricing structure",
      "Retailer-focused restock workflow",
    ],
  };
  return highlights[item.category] ?? highlights["Published Goods"];
}

function getDescription(item: PublishedMarketplaceItem) {
  if (item.notes.trim()) return item.notes;
  return `${item.product_name} is a manufacturer-published listing prepared for retailer ordering. The item is available through the SupplyCentral marketplace with bulk-friendly pricing and a streamlined quote-to-cart workflow.`;
}

function getCartTotal(items: CartItem[]) {
  return items.reduce((sum, item) => sum + getPriceForQuantity(item, item.quantity) * item.quantity, 0);
}

function ProductVisual({
  item,
  className,
  imageClassName,
}: {
  item: PublishedMarketplaceItem;
  className: string;
  imageClassName?: string;
}) {
  if (item.imageUrl) {
    return (
      <div className={`flex items-center justify-center bg-[#f8f9ff] ${className}`}>
        <img
          src={item.imageUrl}
          alt={item.product_name}
          className={imageClassName ?? "h-full w-full object-contain p-4"}
        />
      </div>
    );
  }

  return (
    <div className={`flex items-end bg-gradient-to-br ${buildPlaceholderImage(item)} ${className}`}>
      <div className="m-5 rounded-2xl bg-white/15 px-4 py-3 backdrop-blur">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/75">{item.category}</p>
        <p className="mt-1 text-xl font-semibold text-white">{item.product_name}</p>
      </div>
    </div>
  );
}

export function RetailerDashboard({ user, onLogout }: RetailerDashboardProps) {
  const [publishedGoods, setPublishedGoods] = useState<PublishedMarketplaceItem[]>(() => getPublishedGoods());
  const [cartItems, setCartItems] = useState<CartItem[]>(() => getCartItems());
  const [activeView, setActiveView] = useState<RetailerView>("browse");
  const [selectedProduct, setSelectedProduct] = useState<PublishedMarketplaceItem | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All Categories");
  const [selectedMaxPrice, setSelectedMaxPrice] = useState(250);
  const [detailQuantity, setDetailQuantity] = useState(50);
  const [orderMessage, setOrderMessage] = useState("");
  const [retailerPhone, setRetailerPhone] = useState("");
  const [retailerLocation, setRetailerLocation] = useState("");
  const [formError, setFormError] = useState("");

  // --- Payment flow state ---
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState<"upi" | "cash" | null>(null);
  const [upiTransactionId, setUpiTransactionId] = useState("");
  const [paymentProcessing, setPaymentProcessing] = useState(false);
  const [invoice, setInvoice] = useState<any>(null);
  const [showInvoice, setShowInvoice] = useState(false);
  const invoiceRef = useRef<HTMLDivElement>(null);

  const UPI_ID = import.meta.env.VITE_UPI_ID || "9028336352@ybl";

  useEffect(() => {
    const syncPublishedGoods = () => setPublishedGoods(getPublishedGoods());
    const syncCart = () => setCartItems(getCartItems());

    window.addEventListener(MARKETPLACE_UPDATED_EVENT, syncPublishedGoods);
    window.addEventListener(CART_UPDATED_EVENT, syncCart);
    window.addEventListener("storage", syncPublishedGoods);
    window.addEventListener("storage", syncCart);

    return () => {
      window.removeEventListener(MARKETPLACE_UPDATED_EVENT, syncPublishedGoods);
      window.removeEventListener(CART_UPDATED_EVENT, syncCart);
      window.removeEventListener("storage", syncPublishedGoods);
      window.removeEventListener("storage", syncCart);
    };
  }, []);

  const categoryOptions = useMemo(
    () => ["All Categories", ...new Set(publishedGoods.map((item) => item.category))],
    [publishedGoods],
  );

  const priceCeiling = useMemo(() => {
    const maxPrice = Math.max(...publishedGoods.map((item) => item.unit_price), 0);
    if (maxPrice <= 250) return 250;
    return Math.ceil(maxPrice / 250) * 250;
  }, [publishedGoods]);

  useEffect(() => {
    setSelectedMaxPrice(priceCeiling);
  }, [priceCeiling]);

  const filteredGoods = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();

    return publishedGoods.filter((item) => {
      const matchesSearch =
        !query ||
        [item.product_name, item.sku, item.notes, item.category].some((value) =>
          value.toLowerCase().includes(query),
        );
      const matchesCategory =
        selectedCategory === "All Categories" || item.category === selectedCategory;
      const matchesPrice = item.unit_price <= selectedMaxPrice;

      return matchesSearch && matchesCategory && matchesPrice;
    });
  }, [publishedGoods, searchTerm, selectedCategory, selectedMaxPrice]);

  const relatedProducts = useMemo(() => {
    if (!selectedProduct) return [];
    return publishedGoods.filter((item) => item.id !== selectedProduct.id).slice(0, 4);
  }, [publishedGoods, selectedProduct]);

  const detailPricingTiers = selectedProduct ? getPricingTiers(selectedProduct) : [];
  const detailUnitPrice = selectedProduct ? getPriceForQuantity(selectedProduct, detailQuantity) : 0;
  const activeDetailTier = selectedProduct ? getAppliedPricingTier(selectedProduct, detailQuantity) : null;
  const detailSubtotal = detailUnitPrice * detailQuantity;
  const cartCount = cartItems.reduce((sum, item) => sum + item.quantity, 0);
  const cartTotal = getCartTotal(cartItems);

  const openDetails = (item: PublishedMarketplaceItem) => {
    setSelectedProduct(item);
    setDetailQuantity(50);
    setOrderMessage("");
    setActiveView("details");
  };

  const handleAddToCart = () => {
    if (!selectedProduct) return;
    setCartItems(addToCart(selectedProduct, detailQuantity));
    setOrderMessage("");
    setActiveView("cart");
  };

  const handleBuyNow = () => {
    if (!selectedProduct) return;
    replaceCartWithSingleItem(selectedProduct, detailQuantity);
    setCartItems(getCartItems());
    setOrderMessage("Ready for checkout. Review the cart and place the order.");
    setActiveView("cart");
  };

  // Helper to send logistics order to backend
  async function createLogisticsOrder(item: CartItem, pStatus?: string, upiTxnId?: string) {
    const payload = {
      product_name: item.product_name,
      sku: item.sku,
      quantity: item.quantity,
      unit_price: getPriceForQuantity(item, item.quantity),
      category: item.category,
      notes: item.notes,
      imageUrl: item.imageUrl,
      supplierName: item.category || "Marketplace",
      publishedAt: item.publishedAt,
      retailer_name: user.name,
      retailer_email: user.email,
      retailer_phone: retailerPhone,
      retailer_location: retailerLocation,
      payment_status: pStatus || "pending",
      upi_transaction_id: upiTxnId || null,
    };
    try {
      await apiPost("/logistics/orders/create", payload);
      // Dispatch event to update logistics orders everywhere
      window.dispatchEvent(new Event("logistics-orders-updated"));
    } catch (e) {
      console.error("Failed to create logistics order", e);
    }
  }

  // Opens the payment method selection modal
  const handlePlaceOrder = async () => {
    if (!cartItems.length) return;
    setShowPaymentModal(true);
    setPaymentMethod(null);
    setUpiTransactionId("");
    setPaymentProcessing(false);
  };

  // Generate UPI payment deep link
  const getUpiPaymentString = () => {
    const amount = (cartTotal * 1.04).toFixed(2);
    const name = "SupplyCentral";
    return `upi://pay?pa=${UPI_ID}&pn=${encodeURIComponent(name)}&am=${amount}&cu=INR&tn=${encodeURIComponent("Order Payment")}`;
  };

  // Confirm payment and create invoice
  const confirmPayment = async () => {
    if (paymentMethod === "upi" && !upiTransactionId.trim()) {
      setFormError("Please enter the UPI Transaction ID to confirm.");
      return;
    }
    setPaymentProcessing(true);
    setFormError("");

    try {
      const paymentPayload = {
        payment_method: paymentMethod,
        upi_transaction_id: paymentMethod === "upi" ? upiTransactionId.trim() : null,
        retailer_name: user.name,
        retailer_email: user.email,
        retailer_phone: retailerPhone,
        retailer_location: retailerLocation,
        items: cartItems.map((item) => ({
          product_name: item.product_name,
          sku: item.sku,
          quantity: item.quantity,
          unit_price: getPriceForQuantity(item, item.quantity),
          category: item.category,
        })),
        subtotal: cartTotal,
        freight: cartTotal * 0.04,
        grand_total: cartTotal * 1.04,
      };

      const invoiceData = await apiPost<any, any>("/payments/create-order", paymentPayload);
      setInvoice(invoiceData);

      // Create logistics orders (fire and forget)
      const pStatus = paymentMethod === "upi" ? "paid" : "pending_cash";
      const txnId = paymentMethod === "upi" ? upiTransactionId.trim() : undefined;
      Promise.all(cartItems.map((item) => createLogisticsOrder(item, pStatus, txnId))).catch(() => {});

      clearCart();
      setCartItems([]);
      setSelectedProduct(null);
      setShowPaymentModal(false);
      setShowInvoice(true);
      setOrderMessage("");
    } catch (err) {
      console.error("Payment failed:", err);
      setFormError("Payment processing failed. Please try again.");
    } finally {
      setPaymentProcessing(false);
    }
  };

  const closeInvoice = () => {
    setShowInvoice(false);
    setInvoice(null);
    setActiveView("browse");
    setOrderMessage("Order placed successfully! Invoice has been generated.");
  };

  const printInvoice = () => {
    const content = invoiceRef.current;
    if (!content) return;
    const printWindow = window.open("", "_blank");
    if (!printWindow) return;
    printWindow.document.write(`
      <html>
        <head>
          <title>Invoice</title>
          <style>
            body { font-family: 'Inter', 'Segoe UI', sans-serif; padding: 40px; color: #1e293b; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { padding: 12px 16px; text-align: left; border-bottom: 1px solid #e2e8f0; }
            th { background: #f1f5f9; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: #475569; }
            .header { text-align: center; margin-bottom: 30px; }
            .header h1 { font-size: 28px; color: #1c39bb; margin: 0; }
            .header p { color: #64748b; margin: 4px 0; }
            .total-row td { font-weight: 700; font-size: 16px; border-top: 2px solid #1c39bb; }
            .badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
            .badge-upi { background: #dcfce7; color: #16a34a; }
            .badge-cash { background: #fef3c7; color: #d97706; }
            .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }
            .info-block p { margin: 2px 0; }
            .info-block .label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; color: #94a3b8; }
            .info-block .value { font-size: 14px; font-weight: 600; color: #1e293b; }
            .divider { border: none; border-top: 1px solid #e2e8f0; margin: 20px 0; }
            @media print { body { padding: 20px; } }
          </style>
        </head>
        <body>${content.innerHTML}</body>
      </html>
    `);
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
  };

  const browseView = (
    <main className="mx-auto grid max-w-7xl gap-8 px-4 py-6 sm:px-6 lg:grid-cols-[320px_minmax(0,1fr)] lg:px-8">
      <aside className="rounded-[2rem] border border-white/70 bg-white/80 p-5 shadow-[0_24px_60px_rgba(38,45,88,0.08)] backdrop-blur">
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Marketplace</p>
          <h2 className="text-3xl font-semibold leading-none text-slate-950">Published Goods</h2>
          <p className="text-sm leading-6 text-slate-500">
            Retailers can browse only the items the manufacturer has published from finished stocks.
          </p>
        </div>

        <div className="mt-6 space-y-5">
          <div>
            <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Search
            </label>
            <input
              type="text"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search published items"
              className="w-full rounded-2xl border border-[#d6dbf7] bg-[#f8f9ff] px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-[#1c39bb] focus:ring-2 focus:ring-[#1c39bb]/15"
            />
          </div>

          <div>
            <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Category
            </label>
            <select
              value={selectedCategory}
              onChange={(event) => setSelectedCategory(event.target.value)}
              className="w-full rounded-2xl border border-[#d6dbf7] bg-[#eef2ff] px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-[#1c39bb] focus:ring-2 focus:ring-[#1c39bb]/15"
            >
              {categoryOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Price Range
              </label>
              <span className="text-xs font-semibold text-[#1c39bb]">
                {formatPrice(0)} - {formatPrice(selectedMaxPrice)}
              </span>
            </div>
            <input
              type="range"
              min={0}
              max={priceCeiling}
              step={10}
              value={selectedMaxPrice}
              onChange={(event) => setSelectedMaxPrice(Number(event.target.value))}
              className="h-2 w-full cursor-pointer accent-[#1c39bb]"
            />
          </div>

          <div className="rounded-3xl bg-[#1c39bb] px-4 py-4 text-white shadow-[0_18px_40px_rgba(28,57,187,0.22)]">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/75">Market Snapshot</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
              <div>
                <p className="text-2xl font-semibold">{publishedGoods.length}</p>
                <p className="text-sm text-white/75">Published listings</p>
              </div>
              <div>
                <p className="text-2xl font-semibold">{cartCount}</p>
                <p className="text-sm text-white/75">Items in cart</p>
              </div>
              <div>
                <p className="text-2xl font-semibold">{formatPrice(cartTotal || 0)}</p>
                <p className="text-sm text-white/75">Cart total</p>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <section className="space-y-6">
        {filteredGoods.length === 0 ? (
          <div className="rounded-[2rem] border border-dashed border-slate-300 bg-white/70 px-6 py-16 text-center shadow-[0_20px_50px_rgba(38,45,88,0.06)]">
            <p className="text-lg font-semibold text-slate-900">No published products match these filters.</p>
            <p className="mt-2 text-sm text-slate-500">
              Publish items from the manufacturer&apos;s Finished Stocks page to make them appear here.
            </p>
          </div>
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
            {filteredGoods.map((item) => (
              <article
                key={item.id}
                className="overflow-hidden rounded-[1.75rem] border border-white/80 bg-white shadow-[0_16px_34px_rgba(38,45,88,0.08)] transition-transform duration-300 hover:-translate-y-1"
              >
                <ProductVisual
                  item={item}
                  className="h-44 w-full border-b border-[#edf1ff]"
                  imageClassName="h-full w-full object-contain p-3"
                />

                <div className="space-y-3.5 p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full bg-[#eef2ff] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-[#1c39bb]">
                      {item.category}
                    </span>
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-600">
                      SKU {item.sku}
                    </span>
                  </div>

                  <div className="space-y-1.5">
                    <h3 className="text-lg font-semibold leading-snug text-slate-950">{item.product_name}</h3>
                    <div className="flex items-center justify-between gap-3 text-sm text-slate-500">
                      <p>Published {formatDate(item.publishedAt)}</p>
                      <p>{getRating(item)} rating</p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-[1.85rem] font-semibold leading-none text-slate-950">
                        {formatPrice(item.unit_price)}
                      </p>
                      <p className="mt-1 text-sm text-slate-500">per unit</p>
                    </div>
                    <span className="inline-flex shrink-0 items-center whitespace-nowrap rounded-full bg-[#f8f9ff] px-2.5 py-1 text-[11px] font-medium text-slate-600">
                      Ready to quote
                    </span>
                  </div>

                  <p
                    className="text-sm leading-6 text-slate-600"
                    style={{
                      display: "-webkit-box",
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: "vertical",
                      overflow: "hidden",
                    }}
                  >
                    {item.notes || "Published from finished stocks and ready for retailer review."}
                  </p>

                  <button
                    type="button"
                    onClick={() => openDetails(item)}
                    className="w-full rounded-2xl bg-[#eef2ff] px-4 py-3 text-sm font-semibold text-[#1c39bb] transition hover:bg-[#dfe6ff]"
                  >
                    Request Quote
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );

  const detailsView = selectedProduct ? (
    <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.15fr)_380px]">
        <section className="rounded-[2rem] bg-white p-5 shadow-[0_22px_50px_rgba(38,45,88,0.08)]">
          <div className="mb-5 flex items-center justify-between">
            <button
              type="button"
              onClick={() => setActiveView("browse")}
              className="inline-flex items-center gap-2 rounded-2xl px-3 py-2 text-sm font-semibold text-slate-600 transition hover:bg-slate-100"
            >
              <span className="material-symbols-outlined text-base">arrow_back</span>
              Back to marketplace
            </button>
            <button
              type="button"
              onClick={() => setActiveView("cart")}
              className="rounded-2xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700"
            >
              Cart {cartCount ? `(${cartCount})` : ""}
            </button>
          </div>

          <div className="overflow-hidden rounded-[2rem]">
            <ProductVisual item={selectedProduct} className="h-[320px] w-full object-cover" />
          </div>

          <div className="mt-6">
            <div className="flex flex-wrap items-center gap-3">
              <span className="rounded-full bg-[#1c39bb] px-3 py-1 text-[11px] font-bold uppercase tracking-[0.14em] text-white">
                {selectedProduct.category}
              </span>
              <span className="text-sm text-slate-500">SKU: {selectedProduct.sku}</span>
            </div>

            <h2 className="mt-4 text-3xl font-semibold leading-tight text-slate-950">{selectedProduct.product_name}</h2>

            <div className="mt-4 flex flex-wrap items-center gap-4 text-sm text-slate-500">
              <div className="flex items-center gap-1 text-amber-500">
                {Array.from({ length: 5 }).map((_, index) => (
                  <span key={index} className="material-symbols-outlined text-base">
                    {index < Math.round(getRating(selectedProduct)) ? "star" : "star_half"}
                  </span>
                ))}
              </div>
              <span className="font-semibold text-slate-900">{getRating(selectedProduct)}</span>
              <span>({getReviewCount(selectedProduct)} reviews)</span>
              <span>Published {formatDate(selectedProduct.publishedAt)}</span>
            </div>

            <div className="mt-8">
              <h3 className="text-xl font-semibold text-slate-950">Detailed Product Description</h3>
              <p className="mt-3 text-base leading-8 text-slate-600">{getDescription(selectedProduct)}</p>
            </div>

            <ul className="mt-6 space-y-3 text-sm text-slate-600">
              {getProductHighlights(selectedProduct).map((highlight) => (
                <li key={highlight} className="flex items-start gap-3">
                  <span className="material-symbols-outlined text-lg text-[#1c39bb]">check_circle</span>
                  <span>{highlight}</span>
                </li>
              ))}
            </ul>

            <div className="mt-10 rounded-[2rem] bg-[#f5f7ff] p-5">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold uppercase tracking-[0.22em] text-slate-500">Related Products</h3>
                <button
                  type="button"
                  onClick={() => setActiveView("browse")}
                  className="text-sm font-semibold text-[#1c39bb]"
                >
                  Browse more
                </button>
              </div>
              <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {relatedProducts.length ? (
                  relatedProducts.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => openDetails(item)}
                      className="overflow-hidden rounded-[1.5rem] bg-white text-left shadow-sm transition hover:-translate-y-1"
                    >
                      <ProductVisual item={item} className="h-36 w-full object-cover" />
                      <div className="p-4">
                        <p className="text-base font-semibold text-slate-950">{item.product_name}</p>
                        <p className="mt-1 text-sm text-slate-500">{formatPrice(item.unit_price)}</p>
                      </div>
                    </button>
                  ))
                ) : (
                  <div className="rounded-[1.5rem] bg-white px-4 py-8 text-sm text-slate-500">
                    More published products will appear here.
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        <aside className="space-y-5">
          <div className="rounded-[2rem] bg-white p-5 shadow-[0_22px_50px_rgba(38,45,88,0.08)]">
            <h3 className="text-sm font-bold uppercase tracking-[0.22em] text-slate-500">Bulk Pricing Structure</h3>
            <div className="mt-4 space-y-3">
              {detailPricingTiers.map((tier) => {
                const isActiveTier = activeDetailTier?.label === tier.label;

                return (
                <button
                  key={tier.label}
                  type="button"
                  onClick={() => setDetailQuantity(getTierStartingQuantity(tier.minimum))}
                  className={`w-full rounded-2xl border px-4 py-4 text-left transition ${
                    isActiveTier
                      ? "border-[#1c39bb] bg-[#eef2ff] shadow-[0_10px_24px_rgba(28,57,187,0.12)]"
                      : tier.featured
                        ? "border-[#8da3ff] bg-[#eef2ff]"
                        : "border-slate-200 bg-white hover:border-[#b7c4ff] hover:bg-[#f8faff]"
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-slate-900">{tier.label}</p>
                      {isActiveTier ? (
                        <p className="mt-1 text-xs font-semibold uppercase tracking-[0.18em] text-[#1c39bb]">
                          Applied to current quantity
                        </p>
                      ) : tier.featured ? (
                        <p className="mt-1 text-xs font-semibold uppercase tracking-[0.18em] text-[#1c39bb]">
                          Best Value
                        </p>
                      ) : null}
                    </div>
                    <div className="text-right">
                      <p className="text-xl font-semibold text-slate-950">{formatPrice(tier.price)}</p>
                      <p className="text-xs text-slate-500">/ unit</p>
                    </div>
                  </div>
                </button>
              )})}
            </div>

            <div className="mt-5 rounded-2xl bg-[#f6f3fb] px-4 py-4">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#dde5ff] text-[#1c39bb]">
                  <span className="material-symbols-outlined">local_shipping</span>
                </div>
                <div>
                  <p className="font-semibold text-slate-900">Standard Bulk Freight</p>
                  <p className="text-sm text-slate-500">Delivery within 3-5 business days.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-[2rem] bg-white p-5 shadow-[0_22px_50px_rgba(38,45,88,0.08)]">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold text-slate-900">Specify Order Quantity</p>
              <div className="text-right">
                <p className="text-xs text-slate-500">Est. Subtotal</p>
                <p className="text-3xl font-semibold text-[#1c39bb]">{formatPrice(detailSubtotal)}</p>
              </div>
            </div>

            <div className="mt-5 flex items-center justify-between rounded-2xl bg-[#eef2ff] p-3">
              <button
                type="button"
                onClick={() => setDetailQuantity((current) => Math.max(1, current - 10))}
                className="flex h-12 w-12 items-center justify-center rounded-xl bg-white text-[#1c39bb] shadow-sm"
              >
                <span className="material-symbols-outlined">remove</span>
              </button>
              <div className="text-center">
                <p className="text-2xl font-semibold text-slate-950">{detailQuantity}</p>
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Units</p>
              </div>
              <button
                type="button"
                onClick={() => setDetailQuantity((current) => current + 10)}
                className="flex h-12 w-12 items-center justify-center rounded-xl bg-white text-[#1c39bb] shadow-sm"
              >
                <span className="material-symbols-outlined">add</span>
              </button>
            </div>

            {activeDetailTier ? (
              <div className="mt-3 rounded-2xl border border-[#dbe4ff] bg-[#f8faff] px-4 py-3 text-sm text-slate-600">
                <span className="font-semibold text-slate-900">{activeDetailTier.label}</span> is active for the
                current quantity at <span className="font-semibold text-[#1c39bb]">{formatPrice(detailUnitPrice)}</span>{" "}
                per unit.
              </div>
            ) : null}

            <div className="mt-5 rounded-2xl bg-[#f6f3fb] px-4 py-4">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#dde5ff] text-[#1c39bb]">
                  <span className="material-symbols-outlined">local_shipping</span>
                </div>
                <div>
                  <p className="font-semibold text-slate-900">Standard Bulk Freight</p>
                  <p className="text-sm text-slate-500">Delivery within 3-5 business days.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="sticky bottom-4 rounded-[2rem] bg-white p-4 shadow-[0_22px_50px_rgba(38,45,88,0.12)]">
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={handleAddToCart}
                className="rounded-2xl border-2 border-[#1c39bb] bg-white px-4 py-4 text-base font-semibold text-[#1c39bb]"
              >
                Add to Cart
              </button>
              <button
                type="button"
                onClick={handleBuyNow}
                className="rounded-2xl bg-[#1c39bb] px-4 py-4 text-base font-semibold text-white"
              >
                Buy
              </button>
            </div>
          </div>
        </aside>
      </div>
    </main>
  ) : null;

  const cartView = (
    <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="mb-6 flex flex-col gap-3 rounded-[2rem] bg-white p-5 shadow-[0_22px_50px_rgba(38,45,88,0.08)] sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Cart Page</p>
          <h2 className="text-2xl font-semibold text-slate-950">Retailer Cart</h2>
          <p className="mt-2 text-sm text-slate-500">Order multiple published products together from one place.</p>
        </div>
        <button
          type="button"
          onClick={() => setActiveView("browse")}
          className="rounded-2xl border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-700"
        >
          Continue browsing
        </button>
      </div>

      {cartItems.length === 0 ? (
        <div className="rounded-[2rem] border border-dashed border-slate-300 bg-white px-6 py-16 text-center">
          <p className="text-xl font-semibold text-slate-900">Your cart is empty.</p>
          <p className="mt-2 text-sm text-slate-500">Use Request Quote and Add to Cart to collect products here.</p>
        </div>
      ) : (
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
          <section className="space-y-4">
            {cartItems.map((item) => {
              const unitPrice = getPriceForQuantity(item, item.quantity);
              const subtotal = unitPrice * item.quantity;

              return (
                <article
                  key={item.id}
                  className="grid gap-4 rounded-[2rem] bg-white p-5 shadow-[0_22px_50px_rgba(38,45,88,0.08)] md:grid-cols-[160px_minmax(0,1fr)_140px]"
                >
                  <div className="overflow-hidden rounded-[1.5rem]">
                    <ProductVisual item={item} className="h-full min-h-[160px] w-full object-cover" />
                  </div>

                  <div className="space-y-3">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded-full bg-[#eef2ff] px-3 py-1 text-[11px] font-bold uppercase tracking-[0.14em] text-[#1c39bb]">
                          {item.category}
                        </span>
                        <span className="text-xs text-slate-500">SKU {item.sku}</span>
                      </div>
                      <h3 className="mt-2 text-xl font-semibold text-slate-950">{item.product_name}</h3>
                      <p className="mt-2 text-sm leading-6 text-slate-500">
                        {item.notes || "Published retailer listing ready for multi-product ordering."}
                      </p>
                    </div>

                    <div className="flex flex-wrap items-center gap-3">
                      <button
                        type="button"
                        onClick={() => setCartItems(setCartItemQuantity(item.id, Math.max(1, item.quantity - 10)))}
                        className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#eef2ff] text-[#1c39bb]"
                      >
                        <span className="material-symbols-outlined">remove</span>
                      </button>
                      <div className="rounded-xl bg-[#f6f3fb] px-4 py-2 text-center">
                        <p className="text-lg font-semibold text-slate-950">{item.quantity}</p>
                        <p className="text-[11px] uppercase tracking-[0.14em] text-slate-500">Units</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => setCartItems(setCartItemQuantity(item.id, item.quantity + 10))}
                        className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#eef2ff] text-[#1c39bb]"
                      >
                        <span className="material-symbols-outlined">add</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => setCartItems(removeFromCart(item.id))}
                        className="ml-auto rounded-xl px-3 py-2 text-sm font-semibold text-rose-500 hover:bg-rose-50"
                      >
                        Remove
                      </button>
                    </div>
                  </div>

                  <div className="flex flex-col justify-between rounded-[1.5rem] bg-[#f6f3fb] p-4">
                    <div>
                      <p className="text-xs uppercase tracking-[0.14em] text-slate-500">Unit Price</p>
                      <p className="mt-1 text-xl font-semibold text-slate-950">{formatPrice(unitPrice)}</p>
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-[0.14em] text-slate-500">Subtotal</p>
                      <p className="mt-1 text-2xl font-semibold text-[#1c39bb]">{formatPrice(subtotal)}</p>
                    </div>
                  </div>
                </article>
              );
            })}
          </section>

          <aside className="rounded-[2rem] bg-white p-5 shadow-[0_22px_50px_rgba(38,45,88,0.08)]">
            <h3 className="text-xl font-semibold text-slate-950">Order Summary</h3>
            <div className="mt-5 space-y-4 text-sm">
              <div className="flex items-center justify-between text-slate-600">
                <span>Unique products</span>
                <span className="font-semibold text-slate-950">{cartItems.length}</span>
              </div>
              <div className="flex items-center justify-between text-slate-600">
                <span>Total units</span>
                <span className="font-semibold text-slate-950">
                  {cartItems.reduce((sum, item) => sum + item.quantity, 0)}
                </span>
              </div>
              <div className="flex items-center justify-between text-slate-600">
                <span>Estimated freight</span>
                <span className="font-semibold text-slate-950">{formatPrice(cartTotal * 0.04)}</span>
              </div>
              <div className="border-t border-slate-200 pt-4">
                <div className="flex items-center justify-between">
                  <span className="text-base font-semibold text-slate-950">Grand Total</span>
                  <span className="text-xl font-semibold text-[#1c39bb]">{formatPrice(cartTotal * 1.04)}</span>
                </div>
              </div>
            </div>

            <form
              onSubmit={async (e) => {
                e.preventDefault();
                setFormError("");
                if (!retailerPhone.trim() || !retailerLocation.trim()) {
                  setFormError("Phone number and location are required.");
                  return;
                }
                await handlePlaceOrder();
              }}
              className="space-y-3 mt-4"
            >
              <div>
                <label className="block text-xs font-semibold mb-1">Retailer Phone <span className="text-red-500">*</span></label>
                <input
                  type="tel"
                  value={retailerPhone}
                  onChange={e => setRetailerPhone(e.target.value)}
                  required
                  className="w-full rounded-xl border px-3 py-2 text-sm"
                  placeholder="Enter your phone number"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold mb-1">Retailer Location <span className="text-red-500">*</span></label>
                <input
                  type="text"
                  value={retailerLocation}
                  onChange={e => setRetailerLocation(e.target.value)}
                  required
                  className="w-full rounded-xl border px-3 py-2 text-sm"
                  placeholder="Enter your location"
                />
              </div>
              {formError && <div className="text-red-500 text-xs font-semibold">{formError}</div>}
              <button
                type="submit"
                className="mt-2 w-full rounded-2xl bg-[#1c39bb] px-4 py-4 text-base font-semibold text-white"
              >
                Place Order
              </button>
            </form>
          </aside>
        </div>
      )}
    </main>
  );

  return (
    <div className="min-h-screen bg-[#f6f3fb] pb-24 text-slate-950 font-body md:pb-8">
      <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[#4b5fd1]">Marketplace</p>
            <h1 className="text-2xl font-semibold leading-none text-slate-950">SupplyCentral</h1>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setActiveView("browse")}
              className={`hidden rounded-2xl px-4 py-2 text-sm font-semibold transition sm:block ${
                activeView === "browse" ? "bg-[#eef2ff] text-[#1c39bb]" : "text-slate-500 hover:bg-slate-100"
              }`}
            >
              Browse
            </button>
            <button
              type="button"
              onClick={() => setActiveView("cart")}
              className="relative rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-[#1c39bb] hover:text-[#1c39bb]"
            >
              Cart
              {cartCount ? (
                <span className="ml-2 rounded-full bg-[#1c39bb] px-2 py-0.5 text-xs text-white">{cartCount}</span>
              ) : null}
            </button>
            <div className="hidden text-right sm:block">
              <p className="text-sm font-semibold text-slate-900">{user.name}</p>
              <p className="text-xs text-slate-500">{user.email}</p>
            </div>
            <button
              type="button"
              onClick={onLogout}
              className="rounded-2xl bg-[#1c39bb] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#17319d]"
            >
              Log out
            </button>
          </div>
        </div>
      </header>

      {orderMessage ? (
        <div className="mx-auto mt-4 max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700">
            {orderMessage}
          </div>
        </div>
      ) : null}

      {activeView === "browse" ? browseView : null}
      {activeView === "details" ? detailsView : null}
      {activeView === "cart" ? cartView : null}

      <nav className="fixed bottom-0 left-0 right-0 z-20 border-t border-slate-200 bg-white/95 px-4 py-2 backdrop-blur md:hidden">
        <div className="mx-auto flex max-w-xl items-center justify-around">
          <button
            type="button"
            onClick={() => setActiveView("browse")}
            className={`flex flex-col items-center gap-1 ${activeView === "browse" ? "text-[#1c39bb]" : "text-slate-400"}`}
          >
            <span className="material-symbols-outlined">storefront</span>
            <span className="text-[11px] font-semibold">Browse</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveView("cart")}
            className={`flex flex-col items-center gap-1 ${activeView === "cart" ? "text-[#1c39bb]" : "text-slate-400"}`}
          >
            <span className="material-symbols-outlined">shopping_cart</span>
            <span className="text-[11px] font-semibold">Cart</span>
          </button>
          <button
            type="button"
            onClick={() => selectedProduct && setActiveView("details")}
            className={`flex flex-col items-center gap-1 ${activeView === "details" ? "text-[#1c39bb]" : "text-slate-400"}`}
          >
            <span className="material-symbols-outlined">receipt_long</span>
            <span className="text-[11px] font-semibold">Quote</span>
          </button>
          <button type="button" onClick={onLogout} className="flex flex-col items-center gap-1 text-slate-400">
            <span className="material-symbols-outlined">account_circle</span>
            <span className="text-[11px] font-semibold">Profile</span>
          </button>
        </div>
      </nav>

      {/* ===== Payment Method Modal ===== */}
      {showPaymentModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-[2rem] bg-white p-6 shadow-[0_32px_80px_rgba(28,57,187,0.18)] animate-[fadeInUp_0.3s_ease-out]">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Checkout</p>
                <h2 className="text-2xl font-semibold text-slate-950">Choose Payment Method</h2>
              </div>
              <button
                type="button"
                onClick={() => { setShowPaymentModal(false); setPaymentMethod(null); setFormError(""); }}
                className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-slate-500 hover:bg-slate-200 transition"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            {/* Grand Total Display */}
            <div className="mb-6 rounded-2xl bg-gradient-to-r from-[#1c39bb] to-[#4b5fd1] px-5 py-4 text-white">
              <p className="text-sm font-medium text-white/75">Amount to Pay</p>
              <p className="text-3xl font-bold mt-1">{formatPrice(cartTotal * 1.04)}</p>
              <p className="text-xs text-white/60 mt-1">Includes {formatPrice(cartTotal * 0.04)} freight</p>
            </div>

            {/* Payment Method Selection */}
            {!paymentMethod && (
              <div className="grid grid-cols-2 gap-4">
                <button
                  type="button"
                  onClick={() => { setPaymentMethod("upi"); setFormError(""); }}
                  className="group relative overflow-hidden rounded-2xl border-2 border-slate-200 bg-white p-5 text-left transition-all hover:border-[#1c39bb] hover:shadow-[0_12px_30px_rgba(28,57,187,0.12)]"
                >
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#eef2ff] to-[#dde5ff] text-[#1c39bb] mb-4">
                    <span className="material-symbols-outlined text-2xl">qr_code_2</span>
                  </div>
                  <h3 className="text-lg font-semibold text-slate-950">UPI Payment</h3>
                  <p className="mt-1 text-sm text-slate-500">Pay via UPI QR code</p>
                  <div className="mt-3 flex items-center gap-1 text-xs font-semibold text-[#1c39bb] opacity-0 transition group-hover:opacity-100">
                    <span>Select</span>
                    <span className="material-symbols-outlined text-sm">arrow_forward</span>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => { setPaymentMethod("cash"); setFormError(""); }}
                  className="group relative overflow-hidden rounded-2xl border-2 border-slate-200 bg-white p-5 text-left transition-all hover:border-[#d97706] hover:shadow-[0_12px_30px_rgba(217,119,6,0.12)]"
                >
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#fef3c7] to-[#fde68a] text-[#d97706] mb-4">
                    <span className="material-symbols-outlined text-2xl">payments</span>
                  </div>
                  <h3 className="text-lg font-semibold text-slate-950">Cash on Delivery</h3>
                  <p className="mt-1 text-sm text-slate-500">Pay when delivered</p>
                  <div className="mt-3 flex items-center gap-1 text-xs font-semibold text-[#d97706] opacity-0 transition group-hover:opacity-100">
                    <span>Select</span>
                    <span className="material-symbols-outlined text-sm">arrow_forward</span>
                  </div>
                </button>
              </div>
            )}

            {/* UPI QR Code Section */}
            {paymentMethod === "upi" && (
              <div className="space-y-5">
                <button
                  type="button"
                  onClick={() => { setPaymentMethod(null); setFormError(""); }}
                  className="inline-flex items-center gap-1 text-sm font-semibold text-slate-500 hover:text-slate-700 transition"
                >
                  <span className="material-symbols-outlined text-base">arrow_back</span>
                  Change method
                </button>

                <div className="flex flex-col items-center">
                  <div className="rounded-2xl border-2 border-dashed border-[#dde5ff] bg-white p-5">
                    <QRCodeSVG
                      value={getUpiPaymentString()}
                      size={220}
                      level="H"
                      includeMargin
                      bgColor="#ffffff"
                      fgColor="#1c39bb"
                    />
                  </div>
                  <p className="mt-3 text-sm font-semibold text-slate-900">Scan to Pay</p>
                  <p className="text-xs text-slate-500 mt-1">UPI ID: <span className="font-mono font-semibold text-[#1c39bb]">{UPI_ID}</span></p>
                  <p className="text-xs text-slate-400 mt-1">Amount: {formatPrice(cartTotal * 1.04)}</p>
                </div>

                <div className="rounded-2xl bg-[#f0fdf4] border border-emerald-200 px-4 py-3">
                  <div className="flex items-start gap-2">
                    <span className="material-symbols-outlined text-emerald-500 text-base mt-0.5">info</span>
                    <p className="text-xs text-emerald-700">Scan the QR code using any UPI app (Google Pay, PhonePe, Paytm, etc.) and enter the transaction ID below after successful payment.</p>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-[0.14em] text-slate-500 mb-2">
                    UTR / Transaction ID <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={upiTransactionId}
                    onChange={(e) => setUpiTransactionId(e.target.value)}
                    placeholder="Enter 12-digit UTR number"
                    className="w-full rounded-2xl border border-[#d6dbf7] bg-[#f8f9ff] px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-[#1c39bb] focus:ring-2 focus:ring-[#1c39bb]/15 font-mono"
                  />
                </div>

                {formError && <div className="text-red-500 text-xs font-semibold">{formError}</div>}

                <button
                  type="button"
                  onClick={confirmPayment}
                  disabled={paymentProcessing}
                  className="w-full rounded-2xl bg-gradient-to-r from-[#1c39bb] to-[#4b5fd1] px-4 py-4 text-base font-semibold text-white shadow-[0_12px_30px_rgba(28,57,187,0.25)] transition hover:shadow-[0_16px_40px_rgba(28,57,187,0.35)] disabled:opacity-50"
                >
                  {paymentProcessing ? (
                    <span className="flex items-center justify-center gap-2">
                      <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                      Processing...
                    </span>
                  ) : (
                    "Confirm UPI Payment"
                  )}
                </button>
              </div>
            )}

            {/* Cash on Delivery Section */}
            {paymentMethod === "cash" && (
              <div className="space-y-5">
                <button
                  type="button"
                  onClick={() => { setPaymentMethod(null); setFormError(""); }}
                  className="inline-flex items-center gap-1 text-sm font-semibold text-slate-500 hover:text-slate-700 transition"
                >
                  <span className="material-symbols-outlined text-base">arrow_back</span>
                  Change method
                </button>

                <div className="rounded-2xl bg-[#fffbeb] border border-amber-200 p-5 text-center">
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-[#fde68a] to-[#f59e0b] mx-auto mb-4">
                    <span className="material-symbols-outlined text-3xl text-white">account_balance_wallet</span>
                  </div>
                  <h3 className="text-lg font-semibold text-slate-950">Cash on Delivery</h3>
                  <p className="mt-2 text-sm text-slate-600">
                    Pay <span className="font-bold text-[#d97706]">{formatPrice(cartTotal * 1.04)}</span> in cash when the order is delivered to your location.
                  </p>
                </div>

                <div className="rounded-2xl bg-[#fef3c7] border border-amber-200 px-4 py-3">
                  <div className="flex items-start gap-2">
                    <span className="material-symbols-outlined text-amber-600 text-base mt-0.5">warning</span>
                    <p className="text-xs text-amber-800">Please keep the exact amount ready at the time of delivery. Our delivery partner will collect the payment and provide a receipt.</p>
                  </div>
                </div>

                {formError && <div className="text-red-500 text-xs font-semibold">{formError}</div>}

                <button
                  type="button"
                  onClick={confirmPayment}
                  disabled={paymentProcessing}
                  className="w-full rounded-2xl bg-gradient-to-r from-[#d97706] to-[#f59e0b] px-4 py-4 text-base font-semibold text-white shadow-[0_12px_30px_rgba(217,119,6,0.25)] transition hover:shadow-[0_16px_40px_rgba(217,119,6,0.35)] disabled:opacity-50"
                >
                  {paymentProcessing ? (
                    <span className="flex items-center justify-center gap-2">
                      <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                      Processing...
                    </span>
                  ) : (
                    "Place Order (Cash on Delivery)"
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ===== Invoice / Bill Modal ===== */}
      {showInvoice && invoice && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="w-full max-w-2xl rounded-[2rem] bg-white shadow-[0_32px_80px_rgba(28,57,187,0.18)] animate-[fadeInUp_0.3s_ease-out]">
            {/* Invoice Actions Bar */}
            <div className="flex items-center justify-between p-5 border-b border-slate-100">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                  <span className="material-symbols-outlined">check_circle</span>
                </div>
                <div>
                  <p className="text-sm font-semibold text-emerald-700">
                    {invoice.payment_method === "upi" ? "Payment Successful" : "Order Placed"}
                  </p>
                  <p className="text-xs text-slate-500">{invoice.invoice_number}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={printInvoice}
                  className="flex items-center gap-2 rounded-2xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition"
                >
                  <span className="material-symbols-outlined text-base">print</span>
                  Print
                </button>
                <button
                  type="button"
                  onClick={closeInvoice}
                  className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-slate-500 hover:bg-slate-200 transition"
                >
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>
            </div>

            {/* Invoice Content */}
            <div ref={invoiceRef} className="p-6">
              {/* Invoice Header */}
              <div className="header" style={{ textAlign: "center", marginBottom: 24 }}>
                <h1 style={{ fontSize: 28, color: "#1c39bb", margin: 0, fontWeight: 700 }}>SupplyCentral</h1>
                <p style={{ color: "#64748b", margin: "4px 0", fontSize: 14 }}>Supply Chain Management Platform</p>
                <p style={{ color: "#94a3b8", margin: "2px 0", fontSize: 12 }}>--- TAX INVOICE ---</p>
              </div>

              {/* Invoice Info Grid */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, margin: "16px 0" }}>
                <div>
                  <p style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.1em", color: "#94a3b8", margin: "2px 0" }}>Invoice No.</p>
                  <p style={{ fontSize: 14, fontWeight: 600, color: "#1e293b", margin: "2px 0" }}>{invoice.invoice_number}</p>
                </div>
                <div style={{ textAlign: "right" }}>
                  <p style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.1em", color: "#94a3b8", margin: "2px 0" }}>Date</p>
                  <p style={{ fontSize: 14, fontWeight: 600, color: "#1e293b", margin: "2px 0" }}>
                    {new Date(invoice.order_date).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}
                  </p>
                </div>
                <div>
                  <p style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.1em", color: "#94a3b8", margin: "2px 0" }}>Bill To</p>
                  <p style={{ fontSize: 14, fontWeight: 600, color: "#1e293b", margin: "2px 0" }}>{invoice.retailer_name}</p>
                  <p style={{ fontSize: 13, color: "#64748b", margin: "2px 0" }}>{invoice.retailer_email}</p>
                  <p style={{ fontSize: 13, color: "#64748b", margin: "2px 0" }}>{invoice.retailer_phone}</p>
                </div>
                <div style={{ textAlign: "right" }}>
                  <p style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.1em", color: "#94a3b8", margin: "2px 0" }}>Payment</p>
                  <p style={{ margin: "4px 0" }}>
                    <span
                      className={`badge ${invoice.payment_method === "upi" ? "badge-upi" : "badge-cash"}`}
                      style={{
                        display: "inline-block",
                        padding: "4px 12px",
                        borderRadius: 20,
                        fontSize: 12,
                        fontWeight: 600,
                        background: invoice.payment_method === "upi" ? "#dcfce7" : "#fef3c7",
                        color: invoice.payment_method === "upi" ? "#16a34a" : "#d97706",
                      }}
                    >
                      {invoice.payment_method === "upi" ? "UPI Paid" : "Cash on Delivery"}
                    </span>
                  </p>
                  {invoice.upi_transaction_id && (
                    <p style={{ fontSize: 12, color: "#64748b", margin: "4px 0", fontFamily: "monospace" }}>
                      UTR: {invoice.upi_transaction_id}
                    </p>
                  )}
                </div>
              </div>

              <hr style={{ border: "none", borderTop: "1px solid #e2e8f0", margin: "16px 0" }} />

              {/* Items Table */}
              <table style={{ width: "100%", borderCollapse: "collapse", margin: "16px 0" }}>
                <thead>
                  <tr>
                    <th style={{ padding: "10px 14px", textAlign: "left", borderBottom: "2px solid #e2e8f0", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.06em", color: "#475569", background: "#f8fafc" }}>#</th>
                    <th style={{ padding: "10px 14px", textAlign: "left", borderBottom: "2px solid #e2e8f0", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.06em", color: "#475569", background: "#f8fafc" }}>Product</th>
                    <th style={{ padding: "10px 14px", textAlign: "left", borderBottom: "2px solid #e2e8f0", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.06em", color: "#475569", background: "#f8fafc" }}>SKU</th>
                    <th style={{ padding: "10px 14px", textAlign: "right", borderBottom: "2px solid #e2e8f0", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.06em", color: "#475569", background: "#f8fafc" }}>Qty</th>
                    <th style={{ padding: "10px 14px", textAlign: "right", borderBottom: "2px solid #e2e8f0", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.06em", color: "#475569", background: "#f8fafc" }}>Rate</th>
                    <th style={{ padding: "10px 14px", textAlign: "right", borderBottom: "2px solid #e2e8f0", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.06em", color: "#475569", background: "#f8fafc" }}>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {invoice.items.map((item: any, idx: number) => (
                    <tr key={idx}>
                      <td style={{ padding: "10px 14px", borderBottom: "1px solid #f1f5f9", fontSize: 13, color: "#64748b" }}>{idx + 1}</td>
                      <td style={{ padding: "10px 14px", borderBottom: "1px solid #f1f5f9", fontSize: 13, fontWeight: 600, color: "#1e293b" }}>{item.product_name}</td>
                      <td style={{ padding: "10px 14px", borderBottom: "1px solid #f1f5f9", fontSize: 12, color: "#64748b", fontFamily: "monospace" }}>{item.sku}</td>
                      <td style={{ padding: "10px 14px", borderBottom: "1px solid #f1f5f9", fontSize: 13, color: "#1e293b", textAlign: "right" }}>{item.quantity}</td>
                      <td style={{ padding: "10px 14px", borderBottom: "1px solid #f1f5f9", fontSize: 13, color: "#1e293b", textAlign: "right" }}>{formatPrice(item.unit_price)}</td>
                      <td style={{ padding: "10px 14px", borderBottom: "1px solid #f1f5f9", fontSize: 13, fontWeight: 600, color: "#1e293b", textAlign: "right" }}>{formatPrice(item.line_total)}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr>
                    <td colSpan={5} style={{ padding: "10px 14px", textAlign: "right", fontSize: 13, color: "#64748b" }}>Subtotal</td>
                    <td style={{ padding: "10px 14px", textAlign: "right", fontSize: 14, fontWeight: 600, color: "#1e293b" }}>{formatPrice(invoice.subtotal)}</td>
                  </tr>
                  <tr>
                    <td colSpan={5} style={{ padding: "10px 14px", textAlign: "right", fontSize: 13, color: "#64748b" }}>Freight (4%)</td>
                    <td style={{ padding: "10px 14px", textAlign: "right", fontSize: 14, fontWeight: 600, color: "#1e293b" }}>{formatPrice(invoice.freight)}</td>
                  </tr>
                  <tr className="total-row">
                    <td colSpan={5} style={{ padding: "14px", textAlign: "right", fontSize: 16, fontWeight: 700, color: "#1e293b", borderTop: "2px solid #1c39bb" }}>Grand Total</td>
                    <td style={{ padding: "14px", textAlign: "right", fontSize: 18, fontWeight: 700, color: "#1c39bb", borderTop: "2px solid #1c39bb" }}>{formatPrice(invoice.grand_total)}</td>
                  </tr>
                </tfoot>
              </table>

              {/* Delivery Details */}
              <div style={{ borderRadius: 16, background: "#f8fafc", padding: 16, marginTop: 16 }}>
                <p style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.1em", color: "#94a3b8", margin: "0 0 6px" }}>Delivery Address</p>
                <p style={{ fontSize: 14, fontWeight: 600, color: "#1e293b", margin: 0 }}>{invoice.retailer_location}</p>
              </div>

              {/* Footer */}
              <div style={{ textAlign: "center", marginTop: 24, paddingTop: 16, borderTop: "1px solid #e2e8f0" }}>
                <p style={{ fontSize: 12, color: "#94a3b8", margin: "2px 0" }}>Thank you for your business!</p>
                <p style={{ fontSize: 11, color: "#cbd5e1", margin: "2px 0" }}>SupplyCentral &bull; AI-Powered Supply Chain Management</p>
              </div>
            </div>

            {/* Bottom Actions */}
            <div className="flex items-center justify-end gap-3 p-5 border-t border-slate-100">
              <button
                type="button"
                onClick={printInvoice}
                className="rounded-2xl border border-slate-200 px-5 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition"
              >
                <span className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-base">download</span>
                  Print Invoice
                </span>
              </button>
              <button
                type="button"
                onClick={closeInvoice}
                className="rounded-2xl bg-[#1c39bb] px-5 py-3 text-sm font-semibold text-white hover:bg-[#17319d] transition"
              >
                Continue Shopping
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// anything
