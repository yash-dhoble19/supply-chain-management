import type { CartItem } from "../types/cart.types";
import type { PublishedMarketplaceItem } from "../types/marketplace.types";

const STORAGE_KEY = "chainmind-retailer-cart";
export const CART_UPDATED_EVENT = "retailer-cart-updated";

function isBrowser() {
  return typeof window !== "undefined";
}

function sanitizeItem(item: Partial<CartItem>): CartItem | null {
  if (
    typeof item.id !== "number" ||
    typeof item.sku !== "string" ||
    typeof item.product_name !== "string" ||
    typeof item.status !== "string" ||
    typeof item.progress !== "number" ||
    typeof item.unit_price !== "number" ||
    typeof item.category !== "string" ||
    typeof item.imageUrl !== "string" ||
    typeof item.notes !== "string" ||
    typeof item.publishedAt !== "string" ||
    typeof item.quantity !== "number"
  ) {
    return null;
  }

  return {
    id: item.id,
    sku: item.sku,
    product_name: item.product_name,
    status: item.status,
    progress: item.progress,
    start_date: item.start_date ?? null,
    est_completion: item.est_completion ?? null,
    unit_price: item.unit_price,
    category: item.category,
    imageUrl: item.imageUrl,
    notes: item.notes,
    publishedAt: item.publishedAt,
    quantity: item.quantity,
  };
}

function readCart() {
  if (!isBrowser()) return [];

  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) return [];

  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];

    return parsed
      .map((item) => sanitizeItem(item))
      .filter((item): item is CartItem => item !== null);
  } catch {
    return [];
  }
}

function writeCart(items: CartItem[]) {
  if (!isBrowser()) return;

  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  window.dispatchEvent(new Event(CART_UPDATED_EVENT));
}

export function getCartItems() {
  return readCart();
}

export function addToCart(item: PublishedMarketplaceItem, quantity: number) {
  const safeQuantity = Math.max(1, quantity);
  const current = readCart();
  const existing = current.find((entry) => entry.id === item.id);

  const next = existing
    ? current.map((entry) =>
        entry.id === item.id ? { ...entry, quantity: entry.quantity + safeQuantity } : entry,
      )
    : [...current, { ...item, quantity: safeQuantity }];

  writeCart(next);
  return next;
}

export function setCartItemQuantity(itemId: number, quantity: number) {
  const safeQuantity = Math.max(1, quantity);
  const next = readCart().map((item) => (item.id === itemId ? { ...item, quantity: safeQuantity } : item));
  writeCart(next);
  return next;
}

export function removeFromCart(itemId: number) {
  const next = readCart().filter((item) => item.id !== itemId);
  writeCart(next);
  return next;
}

export function replaceCartWithSingleItem(item: PublishedMarketplaceItem, quantity: number) {
  const safeQuantity = Math.max(1, quantity);
  writeCart([{ ...item, quantity: safeQuantity }]);
}

export function clearCart() {
  writeCart([]);
}

// anything
