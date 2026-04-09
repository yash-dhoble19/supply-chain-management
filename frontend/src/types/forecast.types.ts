import type { ForecastSection } from "../pages/forecastEngine";

export type ForecastLevel = "overall" | "product" | "location" | "combined";

export interface ProductOption {
  key: string;
  label: string;
}

export interface LocationField {
  key: string;
  label: string;
  column: string;
}

export interface ForecastSnapshot {
  section: ForecastSection;
  forecastLevel: ForecastLevel;
  productCategoryOptions: string[];
  productOptions: ProductOption[];
  selectedCategory: string;
  selectedProductKey: string;
  locationFieldConfig: LocationField[];
  locationOptionsByField: Record<string, string[]>;
  locationSelections: Record<string, string>;
  insightHighlights: string[];
}
