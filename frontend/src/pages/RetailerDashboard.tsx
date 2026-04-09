import React, { useEffect, useMemo, useState } from "react";
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
  async function createLogisticsOrder(item: CartItem) {
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
    };
    try {
      await apiPost("/logistics/orders/create", payload);
      // Dispatch event to update logistics orders everywhere
      window.dispatchEvent(new Event("logistics-orders-updated"));
    } catch (e) {
      console.error("Failed to create logistics order", e);
    }
  }

  const handlePlaceOrder = async () => {
    if (!cartItems.length) return;
    // Optimistically update UI
    clearCart();
    setCartItems([]);
    setSelectedProduct(null);
    setOrderMessage("Order placed successfully for the selected retailer items.");
    setActiveView("browse");
    // Send each cart item as a logistics order (fire and forget)
    Promise.all(cartItems.map(createLogisticsOrder)).catch(() => {
      setOrderMessage("Order placed, but some items may not have been processed. Please check your orders.");
    });
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
    </div>
  );
}

// anything
