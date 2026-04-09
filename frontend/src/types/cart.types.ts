import type { PublishedMarketplaceItem } from "./marketplace.types";

export interface CartItem extends PublishedMarketplaceItem {
  quantity: number;
}

// anything
