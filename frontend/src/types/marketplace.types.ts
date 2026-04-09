import type { ManufacturingGoods } from "./manufacturing.types";

export interface PublishedMarketplaceItem extends ManufacturingGoods {
  category: string;
  imageUrl: string;
  notes: string;
  publishedAt: string;
}

// anything
