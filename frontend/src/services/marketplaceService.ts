import type { ManufacturingGoods } from "../types/manufacturing.types";
import type { PublishedMarketplaceItem } from "../types/marketplace.types";

const STORAGE_KEY = "chainmind-published-goods";
export const MARKETPLACE_UPDATED_EVENT = "published-goods-updated";

function isBrowser() {
  return typeof window !== "undefined";
}

function inferCategory(item: ManufacturingGoods, notes: string) {
  const source = `${item.product_name} ${item.sku} ${notes}`.toLowerCase();

  if (
    source.includes("chip") ||
    source.includes("board") ||
    source.includes("sensor") ||
    source.includes("circuit") ||
    source.includes("micro")
  ) {
    return "Electronics";
  }

  if (
    source.includes("helmet") ||
    source.includes("safety") ||
    source.includes("glove") ||
    source.includes("mask")
  ) {
    return "Safety Gear";
  }

  if (
    source.includes("steel") ||
    source.includes("copper") ||
    source.includes("metal") ||
    source.includes("coil") ||
    source.includes("tube")
  ) {
    return "Raw Materials";
  }

  if (
    source.includes("pack") ||
    source.includes("kit") ||
    source.includes("bundle") ||
    source.includes("assembly")
  ) {
    return "Bulk Supplies";
  }

  return "Published Goods";
}

function sanitizeItem(item: Partial<PublishedMarketplaceItem>): PublishedMarketplaceItem | null {
  if (
    typeof item.id !== "number" ||
    typeof item.sku !== "string" ||
    typeof item.product_name !== "string" ||
    typeof item.status !== "string" ||
    typeof item.progress !== "number" ||
    typeof item.unit_price !== "number"
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
    category: item.category ?? "Published Goods",
    imageUrl: item.imageUrl ?? "",
    notes: item.notes ?? "",
    publishedAt: item.publishedAt ?? new Date().toISOString(),
  };
}

function readPublishedGoods(): PublishedMarketplaceItem[] {
  if (!isBrowser()) return [];

  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) return [];

  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];

    return parsed
      .map((item) => sanitizeItem(item))
      .filter((item): item is PublishedMarketplaceItem => item !== null);
  } catch {
    return [];
  }
}

function writePublishedGoods(items: PublishedMarketplaceItem[]) {
  if (!isBrowser()) return;

  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  window.dispatchEvent(new Event(MARKETPLACE_UPDATED_EVENT));
}

export function getPublishedGoods() {
  return readPublishedGoods();
}

export function upsertPublishedGood(
  item: ManufacturingGoods,
  details: { notes?: string; imageUrl?: string } = {},
) {
  const nextItem: PublishedMarketplaceItem = {
    ...item,
    category: inferCategory(item, details.notes ?? ""),
    imageUrl: details.imageUrl ?? "",
    notes: details.notes ?? "",
    publishedAt: new Date().toISOString(),
  };

  const current = readPublishedGoods();
  const existing = current.find((entry) => entry.id === item.id);
  const updated = existing
    ? current.map((entry) =>
        entry.id === item.id
          ? {
              ...entry,
              ...nextItem,
              publishedAt: entry.publishedAt,
            }
          : entry,
      )
    : [nextItem, ...current];

  writePublishedGoods(updated);
  return nextItem;
}
