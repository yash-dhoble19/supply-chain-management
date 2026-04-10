import { useState, useRef, useMemo, useEffect } from "react";

import type { ChangeEvent, DragEvent, MouseEvent } from "react";
import { Header } from "../components/layout/Header";
import { Sidebar } from "../components/layout/Sidebar";
import type { AppPage } from "../types/app.types";
import * as XLSX from "xlsx-js-style";
import {
  generateSmartForecast,
  type ForecastSection,
  type SmartForecastOutput,
} from "./forecastEngine";
import ForecastOutput from "./ForecastOutput";
import { setLatestForecastSnapshot } from "../services/forecastStore";
import type {
  ForecastLevel,
  LocationField,
  ProductOption,
  ForecastSnapshot,
} from "../types/forecast.types";

type CsvRow = Record<string, string>;

interface ParsedCsvPreview {
  headers: string[];
  previewRows: CsvRow[];
  rawRows: CsvRow[];
}

interface DataMapping {
  dateColumn: string;
  salesColumn: string;
  productColumn: string;
  storeColumn: string;
}

interface ValidationModalInfo {
  title: string;
  message: string;
  bullets: string[];
}

interface DataSummary {
  fileName: string;
  rows: number;
  columns: number;
  duplicatesRemoved: number;
  status: string;
  productMetric?: { count: number; text: string };
  storeMetric?: { count: number; text: string };
  dataRetention?: string;
  timeRange?: string;
  fileSizeLabel?: string;
  missingValuesLabel?: string;
  negativeSalesLabel?: string;
  outliersLabel?: string;
}

type FeatureStore = {
  demandSeries: Record<string, number[]>;
  metadata: {
    products: string[];
    stores: string[];
    dateRange: string;
  };
  productMetadata: Record<string, ProductMetadata>;
};

interface DecisionInsights {
  heroAlert?: string | null;
  timeRange?: string;
}

interface ProductMetadata {
  productId?: string;
  productName?: string;
  productCategory?: string;
}

interface DemandInsightModalInfo {
  title: string;
  list: string[];
  more: string | null;
}

type UploadErrorType = "unsupported" | "empty" | "corrupt" | "tooLarge" | null;

interface ClearUploadedFileOptions {
  nextError?: UploadErrorType;
  keepStatus?: boolean;
}

const MAX_UPLOAD_BYTES = 50 * 1024 * 1024;
const FILE_TOO_LARGE_MESSAGE = "File too large. Max size is 50MB";
const DATASET_TOO_SMALL_ERROR = "Dataset too small to generate forecast";
const DATASET_TOO_SMALL_BULLET = "Upload at least 5 rows and 2 meaningful columns";
const LARGE_COLUMN_WARNING = "Large number of columns may affect performance";
const LARGE_DATASET_WARNING = "Large dataset detected. Performance may be slower.";
const VALID_UPLOAD_TYPES = [
  "text/csv",
  "application/vnd.ms-excel",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
];

const MAX_PREVIEW = 5;
const MS_PER_DAY = 1000 * 60 * 60 * 24;
const WEEK_START_DAY = "Monday";
const TIME_GROUPING_OPTIONS = [
  {
    value: "Daily",
    label: "Daily",
    minDays: 30,
    description: "Requires a forecast duration of at least 30 days.",
  },
  {
    value: "Weekly",
    label: "Weekly (Mon start)",
    minDays: 84,
    description: `Requires a forecast duration of at least 12 weeks; weeks start on ${WEEK_START_DAY}.`,
  },
  {
    value: "Monthly",
    label: "Monthly",
    minDays: 180,
    description: "Requires a forecast duration of at least 6 months.",
  },
];

const TIME_GROUPING_REQUIREMENTS = TIME_GROUPING_OPTIONS.map((option) => {
  if (option.value === "Weekly") {
    const weeks = option.minDays / 7;
    return `${option.label} requires ≥ ${weeks} weeks (weeks start on ${WEEK_START_DAY})`;
  }
  if (option.value === "Monthly") {
    const months = option.minDays / 30;
    return `${option.label} requires ≥ ${months} months`;
  }
  return `${option.label} requires ≥ ${option.minDays} days`;
});

const MIN_DURATION_FOR_GROUPING = Math.min(
  ...TIME_GROUPING_OPTIONS.map((option) => option.minDays),
);

const FORECAST_LEVEL_OPTIONS: { value: ForecastLevel; label: string; description: string }[] = [
  { value: "overall", label: "Overall Forecast", description: "Uses all data; recommended for single product/location teams." },
  { value: "product", label: "Product-Level Forecast", description: "" },
  { value: "location", label: "Location-Level Forecast", description: "Focuses on hierarchy (country → state → city/area → store)." },
  { value: "combined", label: "Product + Location Forecast", description: "Aligns SKU and location logic for precise distribution planning." },
];

const LOCATION_FIELD_PRIORITY = [
  { key: "country", label: "Country", keywords: ["country", "nation"] },
  { key: "state", label: "State", keywords: ["state", "province", "region"] },
  { key: "city", label: "City", keywords: ["city", "town", "district", "metro"] },
  { key: "area", label: "Area/Zone", keywords: ["area", "zone", "territory"] },
  { key: "storeId", label: "Store ID", keywords: ["store id", "storeid", "store_id", "branch_id", "outlet_id", "shop_id"] },
];

const FORECAST_DURATION_OPTIONS = [
  { value: 7, label: "7 Days" },
  { value: 15, label: "15 Days" },
  { value: 30, label: "30 Days" },
  { value: 90, label: "90 Days" },
  { value: 180, label: "180 Days" },
];

type ForecastStepKey =
  | "upload"
  | "mapping"
  | "summary"
  | "demand"
  | "config"
  | "generate"
  | "insights";

const FORECAST_STEPS: { key: ForecastStepKey; label: string }[] = [
  { key: "upload", label: "Upload & Inspect Data" },
  { key: "mapping", label: "Column Mapping" },
  { key: "summary", label: "Data Summary" },
  { key: "demand", label: "Demand Intelligence" },
  { key: "config", label: "Forecast Configuration" },
  { key: "generate", label: "Generate Forecast" },
  { key: "insights", label: "Insights" },
];

type DemandType = "Smooth" | "Erratic" | "Intermittent" | "New" | "Seasonal";

interface DemandAnalysisResult {
  counts: Record<DemandType, number>;
  totalGroups: number;
  groupsByType: Record<DemandType, string[]>;
}

interface AnalysisResults {
  productDemandAnalysis: DemandAnalysisResult;
  locationDemandAnalysis: DemandAnalysisResult;
  productMetadata: Record<string, ProductMetadata>;
}

const getDemandTypes = (): DemandType[] => [
  "New",
  "Intermittent",
  "Smooth",
  "Erratic",
  "Seasonal",
];

const DEMAND_EXPLANATIONS: Record<DemandType, string> = {
  Smooth: "Stable and consistent demand with low variability.",
  Erratic: "Highly variable demand with unpredictable fluctuations.",
  Intermittent: "Irregular demand with frequent zero-sales periods.",
  Seasonal: "Demand follows repeating time-based patterns.",
  New: "Insufficient historical data to establish a pattern.",
};

const createEmptyDemandAnalysis = (): DemandAnalysisResult => {
  const demandTypes = getDemandTypes();
  const counts = demandTypes.reduce((acc, type) => {
    acc[type] = 0;
    return acc;
  }, {} as Record<DemandType, number>);
  const groupsByType = demandTypes.reduce((acc, type) => {
    acc[type] = [];
    return acc;
  }, {} as Record<DemandType, string[]>);
  return {
    counts,
    totalGroups: 0,
    groupsByType,
  };
};

const getPreviewProducts = (products: string[]) => {
  const visible = products.slice(0, MAX_PREVIEW);
  return {
    visible,
    remaining: Math.max(0, products.length - visible.length),
  };
};

const CONFIG = {
  MIN_COVERAGE: 0.3,
  OUTLIER_SIGMA: 3,
  MIN_ROWS: 30,
  MISSING_THRESHOLDS: {
    LOW: 0.1,
    HIGH: 0.3,
  },
};

if (CONFIG.MISSING_THRESHOLDS.HIGH > CONFIG.MIN_COVERAGE) {
  CONFIG.MISSING_THRESHOLDS.HIGH = CONFIG.MIN_COVERAGE;
}

const convertWorkbookToCsv = (workbook: XLSX.WorkBook) => {
  const csvChunks: string[] = [];
  let headerLine: string | null = null;

  for (const sheetName of workbook.SheetNames) {
    const worksheet = workbook.Sheets[sheetName];
    if (!worksheet) {
      continue;
    }

    const sheetCsv = XLSX.utils.sheet_to_csv(worksheet, { blankrows: false });
    if (!sheetCsv.trim()) {
      continue;
    }

    const lines = sheetCsv.split(/\r?\n/);
    const filtered = lines.filter((line) => line.trim().length > 0);
    if (!filtered.length) {
      continue;
    }

    if (!headerLine) {
      csvChunks.push(filtered.join("\n"));
      headerLine = filtered[0];
      continue;
    }

    const sheetRows = filtered.slice(1);
    if (sheetRows.length) {
      csvChunks.push(sheetRows.join("\n"));
    }
  }

  return csvChunks.join("\n");
};

const loadFileAsCsv = (file: File): Promise<string> => {
  const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onerror = () => {
      reject("Unable to read the selected file.");
    };

    reader.onload = () => {
      const result = reader.result;

      if (extension === "csv") {
        if (typeof result !== "string") {
          reject("Unable to read the selected file.");
          return;
        }

        resolve(result);
        return;
      }

      if (!(result instanceof ArrayBuffer)) {
        reject("Unable to parse the spreadsheet.");
        return;
      }

      try {
        const workbook = XLSX.read(result, { type: "array" });
        if (!workbook.SheetNames.length) {
          reject("Spreadsheet does not contain any sheets.");
          return;
        }

        const csv = convertWorkbookToCsv(workbook);
        if (!csv.trim()) {
          reject("Spreadsheet does not contain any tabular data.");
          return;
        }

        resolve(csv);
      } catch {
        reject("Failed to convert the spreadsheet to CSV.");
      }
    };

    if (extension === "csv") {
      reader.readAsText(file);
      return;
    }

    reader.readAsArrayBuffer(file);
  });
};

interface CreateForecastProps {
  activePage: AppPage;
  onNavigate: (page: AppPage) => void;
}

const splitCsvLine = (line: string) => {
  const cells: string[] = [];
  let current = "";
  let inQuotes = false;

  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];

    if (char === '"' && line[i + 1] === '"') {
      current += '"';
      i += 1;
      continue;
    }

    if (char === '"') {
      inQuotes = !inQuotes;
      continue;
    }

    if (char === "," && !inQuotes) {
      cells.push(current.trim());
      current = "";
      continue;
    }

    current += char;
  }

  cells.push(current.trim());
  return cells;
};

const parseCsvPreview = (text: string, rowLimit = 5): ParsedCsvPreview | null => {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0);

  if (lines.length === 0) {
    return null;
  }

  const parsed = lines.map(splitCsvLine);
  const headersRaw = parsed[0].map((value, index) =>
    value ? value : `Column ${index + 1}`
  );
  const seenHeaders = new Map<string, number>();
  const headers = headersRaw.map((col) => {
    if (!seenHeaders.has(col)) {
      seenHeaders.set(col, 0);
      return col;
    }
    const next = seenHeaders.get(col)! + 1;
    seenHeaders.set(col, next);
    return `${col}_${next}`;
  });

  const rawRows = parsed.slice(1).map((cells) => {
    const row: CsvRow = {};
    headers.forEach((header, index) => {
      row[header] = cells[index] ?? "";
    });
    return row;
  });

  const previewRows = rawRows.slice(0, rowLimit);

  return { headers, previewRows, rawRows };
};

interface CleanResult {
  rows: CsvRow[];
  hasNegativeSales: boolean;
}

const cleanForecastData = (
  rows: CsvRow[],
  columns: string[],
  mapping: DataMapping
): CleanResult => {
  const seen = new Set<string>();
  const cleaned: CsvRow[] = [];
  const numericColumns = new Set(
    columns.filter((column) => isNumericColumn(rows, column))
  );
  let hasNegativeSales = false;

  rows.forEach((row) => {
    const normalized: CsvRow = {};
    columns.forEach((column) => {
      normalized[column] = (row[column] ?? "").trim();
    });

    const hasAnyValue = Object.values(normalized).some((value) => value !== "");
    if (!hasAnyValue) {
      return;
    }

    const essentialMissing =
      (mapping.dateColumn && !normalized[mapping.dateColumn]) ||
      (mapping.salesColumn && !normalized[mapping.salesColumn]);
    if (essentialMissing) {
      return;
    }

    columns.forEach((column) => {
      if (!normalized[column]) {
        normalized[column] = numericColumns.has(column) ? "0" : "Unknown";
      }
    });

    if (mapping.dateColumn) {
      const rawDate = normalized[mapping.dateColumn];
      if (!rawDate) {
        return;
      }
      const parsedDate = new Date(rawDate);
      if (Number.isNaN(parsedDate.getTime())) {
        return;
      }
      normalized[mapping.dateColumn] = parsedDate.toISOString().split("T")[0];
    }

    if (
      mapping.productColumn &&
      normalized[mapping.productColumn] === "Unknown"
    ) {
      normalized[mapping.productColumn] = "Unknown Product";
    }

    if (
      mapping.storeColumn &&
      normalized[mapping.storeColumn] === "Unknown"
    ) {
      normalized[mapping.storeColumn] = "Unknown Store";
    }

    if (mapping.salesColumn) {
      const rawSales = normalized[mapping.salesColumn];
      if (!rawSales) {
        return;
      }
      const cleanedSales = rawSales.replace(/[^0-9.\-]/g, "");
      const parsedSales = Number(cleanedSales);
      if (Number.isNaN(parsedSales)) {
        return;
      }
      if (parsedSales < 0) {
        hasNegativeSales = true;
      }
      normalized[mapping.salesColumn] = parsedSales.toString();
    }

    const rowKey = columns.map((column) => normalized[column]).join("|");
    if (seen.has(rowKey)) {
      return;
    }

    seen.add(rowKey);
    cleaned.push(normalized);
  });

  return { rows: cleaned, hasNegativeSales };
};

const isNumericColumn = (rows: CsvRow[], column: string) => {
  if (!column) {
    return false;
  }

  const sample = rows.slice(0, 40);
  let total = 0;
  let numeric = 0;

  sample.forEach((row) => {
    const value = (row[column] ?? "").trim();
    if (!value) {
      return;
    }

    total += 1;
    const normalized = value.replace(/[^0-9.\-]/g, "");
    const parsed = Number(normalized);
    if (!Number.isNaN(parsed)) {
      numeric += 1;
    }
  });

  if (total === 0) {
    return false;
  }

  return numeric / total >= 0.7;
};

const isDateColumn = (rows: CsvRow[], column: string) => {
  if (!column) {
    return false;
  }

  const sample = rows.slice(0, 40);
  let total = 0;
  let validDates = 0;

  sample.forEach((row) => {
    const value = (row[column] ?? "").trim();
    if (!value) {
      return;
    }

    total += 1;
    const parsed = Date.parse(value);
    if (!Number.isNaN(parsed)) {
      validDates += 1;
    }
  });

  if (total === 0) {
    return false;
  }

  return validDates / total >= 0.6;
};

const normalizeColumnName = (value: string) =>
  value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "");

const calculateNameMatchScore = (column: string, keywords: string[]) => {
  const normalizedColumn = normalizeColumnName(column);
  if (!normalizedColumn) {
    return 0;
  }

  return keywords.reduce((best, keyword) => {
    const normalizedKeyword = normalizeColumnName(keyword);
    if (!normalizedKeyword) {
      return best;
    }

    if (normalizedColumn.includes(normalizedKeyword)) {
      return 1;
    }

    let partialScore = 0;
    if (
      normalizedKeyword.length >= 3 &&
      normalizedColumn.includes(normalizedKeyword.slice(0, 3))
    ) {
      partialScore = 0.5;
    }

    if (
      normalizedKeyword.length >= 5 &&
      (normalizedColumn.startsWith(normalizedKeyword.slice(0, 5)) ||
        normalizedColumn.endsWith(normalizedKeyword.slice(-5)))
    ) {
      partialScore = Math.max(partialScore, 0.7);
    }

    return Math.max(best, partialScore);
  }, 0);
};

const calculateDataTypeMatchScore = (
  stats: ColumnMetrics,
  expectedType: ColumnExpectation
) => {
  if (expectedType === "date") {
    return stats.isDate ? 1 : stats.nonNullRatio > 0 ? 0.3 : 0;
  }
  if (expectedType === "numeric") {
    return stats.isNumeric ? 1 : stats.nonNullRatio > 0 ? 0.4 : 0;
  }
  if (expectedType === "id") {
    if (stats.uniquenessScore > 0.6) {
      return 1;
    }
    if (stats.uniquenessScore > 0.2) {
      return 0.5;
    }
    return 0.2;
  }
  if (expectedType === "text" || expectedType === "category") {
    return !stats.isNumeric && stats.nonNullRatio > 0.4 ? 0.8 : 0.3;
  }
  return 0.4;
};

const calculateColumnScore = ({
  nameMatch,
  dataTypeMatch,
  nonNullRatio,
  uniquenessScore,
}: {
  nameMatch: number;
  dataTypeMatch: number;
  nonNullRatio: number;
  uniquenessScore: number;
}) =>
  nameMatch * COLUMN_SCORE_WEIGHTS.name +
  dataTypeMatch * COLUMN_SCORE_WEIGHTS.dataType +
  nonNullRatio * COLUMN_SCORE_WEIGHTS.nonNull +
  uniquenessScore * COLUMN_SCORE_WEIGHTS.uniqueness;

const getConfidenceLabel = (score: number): ConfidenceBadge => {
  if (score >= 0.75) {
    return { label: "✅ Auto-detected (High confidence)", tone: "high" };
  }
  if (score >= 0.45) {
    return { label: "⚠ Needs attention", tone: "medium" };
  }
  return { label: "🟡 Suggested", tone: "low" };
};

const getNegativeSignalsForRole = (roleId: string, stats: ColumnMetrics) => {
  const signals: string[] = [];
  if (["sales"].includes(roleId)) {
    if (stats.nonNullRatio > 0.4 && !stats.isNumeric) {
      signals.push("❌ not sales");
    }
  }
  if (["date"].includes(roleId)) {
    if (stats.nonNullRatio > 0.4 && !stats.isDate) {
      signals.push("❌ not date");
    }
  }
  if (["product", "sku", "productId", "storeId"].includes(roleId)) {
    if (stats.nonNullRatio > 0.3 && stats.uniquenessScore < 0.4) {
      signals.push("❌ not ID");
    }
  }
  if (["unitPrice", "units", "promotion"].includes(roleId)) {
    if (stats.nonNullRatio > 0.4 && !stats.isNumeric) {
      signals.push("❌ not numeric");
    }
  }
  return signals;
};

const pickColumn = (headers: string[], keywords: string[]) => {
  const normalized = headers.map((column) => normalizeColumnName(column));

  for (const keyword of keywords) {
    const normalizedKeyword = normalizeColumnName(keyword);
    const matchIndex = normalized.findIndex((value) =>
      value.includes(normalizedKeyword)
    );
    if (matchIndex !== -1) {
      return headers[matchIndex];
    }
  }

  return "";
};

const formatFileSize = (size: number) => {
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 ** 2) {
    return `${(size / 1024).toFixed(1)} KB`;
  }
  if (size < 1024 ** 3) {
    return `${(size / 1024 ** 2).toFixed(1)} MB`;
  }
  return `${(size / 1024 ** 3).toFixed(1)} GB`;
};

const formatNumber = (value: number) => value.toLocaleString();
const supportedForecastExtensions = new Set(["csv", "xlsx", "xls"]);

const detectionKeywords = {
  date: ["date", "order date", "transaction date", "ship date"],
  sales: ["sales", "units", "quantity", "qty", "volume", "demand", "revenue", "amount"],
  price: ["price", "unit price", "price per unit", "rate", "value", "cost", "selling price"],
  storeGeneral: ["store", "location", "branch", "outlet"],
  storeId: ["store id", "storeid", "store_id", "branch_id", "outlet_id"],
  storeName: ["store name", "store_name", "branch name", "outlet name"],
  location: ["location", "address"],
  region: ["region", "region name"],
  city: ["city", "town", "district", "metro"],
  state: ["state", "province", "state region", "state/region"],
  country: ["country", "nation", "country name"],
  area: ["area", "zone", "territory"],
  sku: ["sku", "product sku", "productsku"],
  productId: [
    "product id",
    "productid",
    "product_id",
    "item id",
    "itemid",
    "item_id",
    "item code",
    "product code",
  ],
  productName: ["product name", "productname", "name", "item", "label"],
  productCategory: ["category", "segment", "class", "type", "product category"],
  productGeneral: ["product", "item", "sku", "name", "product name"],
};

const PRODUCT_ID_KEYWORDS = ["sku", "product_id", "item_id", "code"];
const PRODUCT_NAME_KEYWORDS = ["product", "name", "item", "description"];
const PRODUCT_CATEGORY_KEYWORDS = ["category", "segment", "type"];

interface DateCandidate {
  header: string;
  parseRatio: number;
  nonNull: number;
}

interface SalesCandidate {
  column: string;
  nonNull: number;
  variance: number;
}

const DATE_NAME_KEYWORDS = [
  "date",
  "time",
  "day",
  "invoice",
  "order",
  "created",
];

const SALES_NAME_KEYWORDS = [
  "sales",
  "revenue",
  "amount",
  "total",
  "gmv",
];

const SALES_REJECT_KEYWORDS = ["person", "name", "id", "code"];

const ROW_SAMPLE_SIZE = 40;

const collectSampleValues = (rows: CsvRow[], column: string) =>
  rows
    .slice(0, ROW_SAMPLE_SIZE)
    .map((row) => (row[column] ?? "").trim())
    .filter((value) => value.length > 0);

const computeVariance = (numbers: number[]) => {
  if (!numbers.length) {
    return 0;
  }
  const mean = numbers.reduce((sum, value) => sum + value, 0) / numbers.length;
  const squaredDiffs = numbers.reduce(
    (acc, value) => acc + (value - mean) ** 2,
    0
  );
  return squaredDiffs / numbers.length;
};

const detectDateColumnSimple = (headers: string[], rows: CsvRow[]) => {
  if (!rows.length) {
    return "";
  }

  const candidates = headers
    .map((header) => ({
      header,
      normalized: normalizeColumnName(header),
    }))
    .filter(({ normalized }) =>
      DATE_NAME_KEYWORDS.some((keyword) => normalized.includes(keyword))
    )
    .map((candidate) => {
      const values = collectSampleValues(rows, candidate.header);
      if (!values.length) {
        return null;
      }
      const parseable = values.filter(
        (value) => !Number.isNaN(Date.parse(value))
      ).length;
      const ratio = values.length ? parseable / values.length : 0;
      return {
        header: candidate.header,
        parseRatio: ratio,
        nonNull: values.length,
      };
    })
    .filter(
      (entry): entry is DateCandidate =>
        Boolean(entry && (entry.parseRatio >= 0.5 || entry.nonNull > 0))
    );

  if (!candidates.length) {
    return "";
  }

  candidates.sort((a, b) => {
    if (b.parseRatio !== a.parseRatio) {
      return b.parseRatio - a.parseRatio;
    }
    return b.nonNull - a.nonNull;
  });

  return candidates[0].header;
};

const detectSalesColumnSimple = (headers: string[], rows: CsvRow[]) => {
  if (!rows.length) {
    return "";
  }

  const candidates = headers
    .map((header) => ({
      header,
      normalized: normalizeColumnName(header),
    }))
    .filter(({ normalized }) =>
      SALES_NAME_KEYWORDS.some((keyword) => normalized.includes(keyword))
    )
    .filter(
      ({ normalized }) =>
        !SALES_REJECT_KEYWORDS.some((keyword) =>
          normalized.includes(keyword)
        )
    )
    .filter(({ header }) => isNumericColumn(rows, header))
    .map(({ header }) => {
      const values = collectSampleValues(rows, header)
        .map((value) => {
          const normalized = value.replace(/[^0-9.\-]/g, "");
          const parsed = Number(normalized);
          return Number.isNaN(parsed) ? null : parsed;
        })
        .filter((value): value is number => value !== null);

      if (!values.length) {
        return null;
      }

      return {
        column: header,
        nonNull: values.length,
        variance: computeVariance(values),
      };
    })
    .filter((entry): entry is SalesCandidate => Boolean(entry));

  if (!candidates.length) {
    return "";
  }

  candidates.sort((a, b) => {
    if (b.nonNull !== a.nonNull) {
      return b.nonNull - a.nonNull;
    }
    return b.variance - a.variance;
  });

  return candidates[0].column;
};

const shouldRejectSalesColumn = (column: string) => {
  if (!column) {
    return false;
  }
  const normalized = normalizeColumnName(column);
  return SALES_REJECT_KEYWORDS.some((keyword) =>
    normalized.includes(normalizeColumnName(keyword))
  );
};

const LOCATION_KEYWORDS = [
  "city",
  "state",
  "region",
  "country",
  "area",
  "zone",
  "location",
];

type ColumnExpectation = "date" | "numeric" | "id" | "text" | "category" | "any";
type ConfidenceTone = "high" | "medium" | "low";

interface ConfidenceBadge {
  label: string;
  tone: ConfidenceTone;
}

interface RoleDefinition {
  id: string;
  label: string;
  keywords: string[];
  expectedType: ColumnExpectation;
  section: "core" | "product" | "location" | "extra" | "support";
  helper?: string;
}

interface ColumnMetrics {
  nonNullRatio: number;
  uniquenessScore: number;
  isNumeric: boolean;
  isDate: boolean;
  sampleSize: number;
}

interface ColumnRoleScore {
  column: string;
  score: number;
  nameMatch: number;
  dataTypeMatch: number;
  nonNullRatio: number;
  uniquenessScore: number;
  negativeSignals: string[];
}

const COLUMN_SCORE_WEIGHTS = {
  name: 0.4,
  dataType: 0.3,
  nonNull: 0.2,
  uniqueness: 0.1,
};

const FINAL_COLUMN_ROLE_DEFINITIONS: RoleDefinition[] = [
  {
    id: "date",
    label: "Date column",
    keywords: [
      "date",
      "order_date",
      "transaction_date",
      "invoice_date",
      "timestamp",
      "datetime",
      "created_at",
      "day",
      "sales_date",
    ],
    expectedType: "date",
    section: "core",
  },
  {
    id: "sales",
    label: "Sales column",
    keywords: [
      "sales",
      "revenue",
      "amount",
      "total",
      "net_sales",
      "gross_sales",
      "sales_value",
      "order_value",
      "gmv",
      "booking_value",
    ],
    expectedType: "numeric",
    section: "core",
  },
  {
    id: "product",
    label: "Product identifier",
    keywords: ["sku", "product_id", "item_id", "product_code", "product", "product_name"],
    expectedType: "id",
    section: "product",
    helper: "Priority: SKU > Product ID > Product Name",
  },
  {
    id: "sku",
    label: "SKU / Product ID",
    keywords: ["sku", "product_sku", "item_id", "product_id", "product_code", "item_code"],
    expectedType: "id",
    section: "product",
  },
  {
    id: "productId",
    label: "Product ID",
    keywords: ["product id", "productid", "product_id", "item id", "item_id", "itemid"],
    expectedType: "id",
    section: "product",
  },
  {
    id: "productName",
    label: "Product Name",
    keywords: ["product name", "name", "item", "description", "label"],
    expectedType: "text",
    section: "product",
  },
  {
    id: "productCategory",
    label: "Product Category",
    keywords: ["category", "product_category", "segment", "type", "class"],
    expectedType: "category",
    section: "product",
  },
  {
    id: "store",
    label: "Store / Store Name",
    keywords: ["store", "shop", "outlet", "branch"],
    expectedType: "text",
    section: "location",
    helper: "Priority: Store ID > Store Name",
  },
  {
    id: "storeId",
    label: "Store ID",
    keywords: ["store id", "store_id", "storeid", "branch_id", "outlet_id"],
    expectedType: "id",
    section: "location",
  },
  {
    id: "location",
    label: "Location reference",
    keywords: ["location", "address", "site"],
    expectedType: "text",
    section: "location",
  },
  {
    id: "region",
    label: "Region",
    keywords: ["region", "region name"],
    expectedType: "text",
    section: "location",
  },
  {
    id: "city",
    label: "City",
    keywords: ["city", "town", "metro", "district"],
    expectedType: "text",
    section: "location",
  },
  {
    id: "state",
    label: "State / Province",
    keywords: ["state", "province", "state region", "state/region"],
    expectedType: "text",
    section: "location",
  },
  {
    id: "country",
    label: "Country",
    keywords: ["country", "nation", "country name"],
    expectedType: "text",
    section: "location",
  },
  {
    id: "area",
    label: "Area / Zone",
    keywords: ["area", "zone", "territory"],
    expectedType: "text",
    section: "location",
  },
];

const countUniqueValues = (rows: CsvRow[], column?: string) => {
  if (!column) {
    return 0;
  }
  const values = new Set<string>();
  rows.forEach((row) => {
    const value = (row[column] ?? "").trim();
    if (value) {
      values.add(value);
    }
  });
  return values.size;
};

const STORE_ID_KEYWORDS = [
  "store id",
  "storeid",
  "store_id",
  "branch_id",
  "branchid",
  "branch id",
  "outlet_id",
  "outletid",
  "outlet id",
  "shop_id",
  "shopid",
  "shop id",
  "id",
];

const STORE_NAME_KEYWORDS = ["store", "shop", "outlet", "branch", "name"];
const REQUIRED_STORE_ID_UNIQUENESS = 0.55;

const getColumnUniquenessRatio = (rows: CsvRow[], column: string) => {
  if (!column || !rows.length) {
    return 0;
  }
  const uniqueValues = countUniqueValues(rows, column);
  return rows.length ? uniqueValues / rows.length : 0;
};

const detectStoreIdColumnSimple = (headers: string[], rows: CsvRow[]) => {
  const normalizedHeaders = headers.map((header) => ({
    header,
    normalized: normalizeColumnName(header),
  }));

  const candidates = normalizedHeaders
    .filter(({ normalized }) =>
      STORE_ID_KEYWORDS.some((keyword) =>
        normalized.includes(normalizeColumnName(keyword))
      )
    )
    .map(({ header, normalized }) => ({
      column: header,
      normalized,
      uniqueness: getColumnUniquenessRatio(rows, header),
    }));

  if (!candidates.length) {
    return "";
  }

  candidates.sort((a, b) => {
    if (b.uniqueness !== a.uniqueness) {
      return b.uniqueness - a.uniqueness;
    }
    return a.column.length - b.column.length;
  });

  const [best] = candidates;
  if (best.uniqueness >= REQUIRED_STORE_ID_UNIQUENESS) {
    return best.column;
  }

  const fallback = candidates.find((candidate) =>
    ["store", "branch", "outlet", "shop"].some((keyword) =>
      candidate.normalized.includes(keyword)
    )
  );
  if (fallback && fallback.uniqueness >= REQUIRED_STORE_ID_UNIQUENESS * 0.6) {
    return fallback.column;
  }

  return "";
};

const detectStoreNameColumnSimple = (
  headers: string[],
  rows: CsvRow[],
  excludedColumns: string[] = []
) => {
  const normalizedHeaders = headers.map((header) => ({
    header,
    normalized: normalizeColumnName(header),
  }));

  const candidates = normalizedHeaders
    .filter(
      ({ header, normalized }) =>
        !excludedColumns.includes(header) &&
        STORE_NAME_KEYWORDS.some((keyword) =>
          normalized.includes(normalizeColumnName(keyword))
        )
    )
    .filter(({ header }) => !isNumericColumn(rows, header))
    .map(({ header, normalized }) => ({
      column: header,
      score: STORE_NAME_KEYWORDS.reduce(
        (result, keyword) =>
          normalized.includes(normalizeColumnName(keyword)) ? result + 1 : result,
        0
      ),
    }));

  if (!candidates.length) {
    return "";
  }

  candidates.sort((a, b) => b.score - a.score);
  return candidates[0].column;
};

const buildProductMetric = (
  rows: CsvRow[],
  columns: string[],
  mapping: DataMapping
) => {
  const candidate =
    mapping.productColumn ||
    pickColumn(columns, ["product_id", "sku", "product", "item", "product name", "name"]);
  const count = countUniqueValues(rows, candidate);
  if (!candidate || !count) {
    return null;
  }
  return { count, text: `Unique products: ${formatNumber(count)}` };
};

const buildStoreMetric = (
  rows: CsvRow[],
  columns: string[],
  mapping: DataMapping
) => {
  const storeIdCandidate = pickColumn(columns, ["store_id", "storeid", "outlet_id", "branch_id"]);
  const locationCandidates = [
    {
      column: storeIdCandidate || mapping.storeColumn,
      text: (count: number) => `Unique stores: ${formatNumber(count)}`,
    },
    {
      column: pickColumn(columns, ["country", "nation", "country_name"]),
      text: (count: number) => `Business is spread across ${formatNumber(count)} countries`,
    },
    {
      column: pickColumn(columns, ["state", "region", "province", "state/region"]),
      text: (count: number) => `Business is spread across ${formatNumber(count)} states/regions`,
    },
    {
      column: pickColumn(columns, ["city", "town", "district", "metro"]),
      text: (count: number) => `Business is spread across ${formatNumber(count)} cities`,
    },
  ];

  for (const candidate of locationCandidates) {
    const count = countUniqueValues(rows, candidate.column);
    if (candidate.column && count) {
      return { count, text: candidate.text(count) };
    }
  }

  return null;
};

export function CreateForecast({ activePage, onNavigate }: CreateForecastProps) {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const lastUpdated = new Date();
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [columns, setColumns] = useState<string[]>([]);
  const [rawRows, setRawRows] = useState<CsvRow[]>([]);
  const [cleanedRows, setCleanedRows] = useState<CsvRow[]>([]);
  const [dateColumn, setDateColumn] = useState("");
  const [salesColumn, setSalesColumn] = useState("");
  const [productColumn, setProductColumn] = useState("");
  const [storeColumn, setStoreColumn] = useState("");
  const [dataStoreNameColumn, setDataStoreNameColumn] = useState("");
  const [dataProductNameColumn, setDataProductNameColumn] = useState("");
  const [dataProductCategoryColumn, setDataProductCategoryColumn] = useState("");
  const [isValidating, setIsValidating] = useState(false);
  const [validationModal, setValidationModal] = useState<ValidationModalInfo | null>(null);
  const [dataSummary, setDataSummary] = useState<DataSummary | null>(null);
  const [previewExpanded, setPreviewExpanded] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [fileSizeLabel, setFileSizeLabel] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<UploadErrorType>(null);
  const [selectedAdditionalFeatures, setSelectedAdditionalFeatures] = useState<string[]>([]);
  const [selectedLocationColumns, setSelectedLocationColumns] = useState<string[]>([]);
  const [isDropzoneActive, setIsDropzoneActive] = useState(false);
  const resultsRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [forecastGranularity, setForecastGranularity] = useState("Weekly");
  const [forecastDurationDays, setForecastDurationDays] = useState(15);
  const [forecastRequested, setForecastRequested] = useState(false);
  const [hasSavedForecast, setHasSavedForecast] = useState(false);
  const [heroAlert, setHeroAlert] = useState<string | null>(null);
  const [analysisResults, setAnalysisResults] = useState<AnalysisResults | null>(null);
  const [demandInsightModal, setDemandInsightModal] = useState<DemandInsightModalInfo | null>(null);
  const [dataCoverageDays, setDataCoverageDays] = useState<number | null>(null);
  const [maxForecastDays, setMaxForecastDays] = useState<number | null>(null);
  const [forecastLevel, setForecastLevel] = useState<ForecastLevel>("overall");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [selectedProductKey, setSelectedProductKey] = useState("");
  const [locationSelections, setLocationSelections] = useState<Record<string, string>>({});
  const [lastConfirmedData, setLastConfirmedData] =
    useState<{ cleaned: CsvRow[]; mapping: DataMapping } | null>(null);
  const [overallForecastSection, setOverallForecastSection] =
    useState<ForecastSection | null>(null);

  const productMetadata = analysisResults?.productMetadata ?? {};
  const orderedProductKeys = useMemo(() => {
    const demandTypes = getDemandTypes();
    const seen = new Set<string>();
    const order: string[] = [];
    demandTypes.forEach((type) => {
      const keys =
        analysisResults?.productDemandAnalysis?.groupsByType[type] ?? [];
      keys.forEach((key) => {
        if (!seen.has(key)) {
          seen.add(key);
          order.push(key);
        }
      });
    });
    return order;
  }, [analysisResults?.productDemandAnalysis]);

  const productCategoryOptions = useMemo(() => {
    const seen = new Set<string>();
    const options: string[] = [];
    orderedProductKeys.forEach((key) => {
      const category = productMetadata[key]?.productCategory;
      if (category && !seen.has(category)) {
        seen.add(category);
        options.push(category);
      }
    });
    return options;
  }, [orderedProductKeys, productMetadata]);

  const productOptions = useMemo<ProductOption[]>(() => {
    return orderedProductKeys
      .filter((key) =>
        selectedCategory
          ? (productMetadata[key]?.productCategory ?? "") === selectedCategory
          : true
      )
      .map((key) => {
        const metadata = productMetadata[key] ?? {};
        const displayLabel = metadata.productName
          ? `${metadata.productName} (${metadata.productId ?? key})`
          : metadata.productId ?? key;
        return {
          key,
          label: displayLabel,
        };
      });
  }, [orderedProductKeys, productMetadata, selectedCategory]);

  const insightHighlights = useMemo(() => {
    if (!overallForecastSection) {
      return ["Generate a forecast to unlock curated insights."];
    }
    const { summary, model } = overallForecastSection.smart;
    const trendLabel = summary.trend || "steady";
    return [
      `${summary.demandType} demand with a ${trendLabel} trend at ${summary.confidence} confidence.`,
      `Model: ${model.name} — ${model.reason}`,
    ];
  }, [overallForecastSection]);


  const findColumnForKeywords = (keywords: string[]) => {
    const normalizedKeywords = keywords.map((keyword) =>
      normalizeColumnName(keyword)
    );
    return columns.find((column) => {
      const normalized = normalizeColumnName(column);
      return normalizedKeywords.some((keyword) => normalized.includes(keyword));
    });
  };

  const locationFieldConfig = useMemo<LocationField[]>(() => {
    return LOCATION_FIELD_PRIORITY.map((field) => {
      const column = findColumnForKeywords(field.keywords);
      return column ? { ...field, column } : null;
    }).filter(
      (entry): entry is (typeof LOCATION_FIELD_PRIORITY)[number] & { column: string } =>
        Boolean(entry)
    );
  }, [columns]);

  const locationOptionsByField = useMemo(() => {
    const rowsSource = cleanedRows.length ? cleanedRows : rawRows;
    const result: Record<string, string[]> = {};
    locationFieldConfig.forEach((field) => {
      const seen = new Set<string>();
      const values: string[] = [];
      rowsSource.forEach((row) => {
        const value = (row[field.column] ?? "").trim();
        if (value && !seen.has(value)) {
          seen.add(value);
          values.push(value);
        }
      });
      result[field.key] = values;
    });
    return result;
  }, [locationFieldConfig, cleanedRows, rawRows]);

  useEffect(() => {
    if (!overallForecastSection || !forecastRequested || hasSavedForecast) {
      return;
    }
    setLatestForecastSnapshot({
      section: overallForecastSection,
      forecastLevel,
      productCategoryOptions,
      productOptions,
      selectedCategory,
      selectedProductKey,
      locationFieldConfig,
      locationOptionsByField,
      locationSelections,
      insightHighlights,
    });
    setHasSavedForecast(true);
    setForecastRequested(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
    // // onNavigate("demandForecasting");
  }, [
    overallForecastSection,
    forecastRequested,
    hasSavedForecast,
    forecastLevel,
    productCategoryOptions,
    productOptions,
    selectedCategory,
    selectedProductKey,
    locationFieldConfig,
    locationOptionsByField,
    locationSelections,
    insightHighlights,
    onNavigate,
  ]);

  useEffect(() => {
    setSelectedCategory("");
    setSelectedProductKey("");
  }, [orderedProductKeys.length]);

  useEffect(() => {
    setLocationSelections((prev) => {
      const next: Record<string, string> = {};
      locationFieldConfig.forEach((field) => {
        if (prev[field.key]) {
          next[field.key] = prev[field.key];
        }
      });
      return next;
    });
  }, [locationFieldConfig]);

  
  useEffect(() => {
    if (overallForecastSection && resultsRef.current) {
      resultsRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [overallForecastSection]);

  const updateLocationSelection = (fieldKey: string, value: string) => {
    setLocationSelections((prev) => ({
      ...prev,
      [fieldKey]: value,
    }));
  };

  const columnStats = useMemo(() => {
    const statsMap: Record<string, ColumnMetrics> = {};
    if (!columns.length || !rawRows.length) {
      return statsMap;
    }
    columns.forEach((column) => {
      const sampleRows = rawRows.slice(0, ROW_SAMPLE_SIZE);
      const values = sampleRows.map((row) => (row[column] ?? "").trim());
      const nonNullValues = values.filter(Boolean);
      const ratio = values.length ? nonNullValues.length / values.length : 0;
      const uniqueCount = new Set(nonNullValues).size;
      statsMap[column] = {
        nonNullRatio: ratio,
        uniquenessScore: nonNullValues.length
          ? Math.min(1, uniqueCount / nonNullValues.length)
          : 0,
        isNumeric: isNumericColumn(rawRows, column),
        isDate: isDateColumn(rawRows, column),
        sampleSize: values.length,
      };
    });
    return statsMap;
  }, [columns, rawRows]);

  const detectionResults = useMemo(() => {
    const results: Record<string, ColumnRoleScore[]> = {};
    FINAL_COLUMN_ROLE_DEFINITIONS.forEach((role) => {
      results[role.id] = [];
    });
    columns.forEach((column) => {
      const stats = columnStats[column];
      if (!stats) {
        return;
      }
      FINAL_COLUMN_ROLE_DEFINITIONS.forEach((role) => {
        const nameMatch = calculateNameMatchScore(column, role.keywords);
        const dataTypeMatch = calculateDataTypeMatchScore(stats, role.expectedType);
        const score = calculateColumnScore({
          nameMatch,
          dataTypeMatch,
          nonNullRatio: stats.nonNullRatio,
          uniquenessScore: stats.uniquenessScore,
        });
        results[role.id].push({
          column,
          score,
          nameMatch,
          dataTypeMatch,
          nonNullRatio: stats.nonNullRatio,
          uniquenessScore: stats.uniquenessScore,
          negativeSignals: getNegativeSignalsForRole(role.id, stats),
        });
      });
    });
    Object.values(results).forEach((list) => list.sort((a, b) => b.score - a.score));
    return results;
  }, [columns, columnStats]);

  const renderRoleField = (
    roleId: string,
    value: string,
    setter: (column: string) => void,
    label: string,
    helper?: string
  ) => {
    const roleScores = detectionResults[roleId] ?? [];
    const autoDetected = roleScores[0];
    const selected =
      value && roleScores.length
        ? roleScores.find((entry) => entry.column === value) ?? autoDetected
        : autoDetected;
    return (
      <label className="mapping-column final-column">
        <div className="mapping-column-header">
          <span>{label}</span>
          {helper ? <small className="mapping-helper">{helper}</small> : null}
        </div>
        <select
          value={value}
          onChange={(event) => setter(event.target.value)}
          disabled={!columns.length}
        >
          <option value="">Not Available</option>
          {columns.map((column) => (
            <option key={`${roleId}-${column}`} value={column}>
              {column}
            </option>
          ))}
        </select>
      </label>
  );
};

const renderDemandList = (
  analysis: DemandAnalysisResult,
  onView: (type: DemandType) => void
) => {
  const demandTypes = getDemandTypes();
  const visibleTypes = demandTypes.filter(
    (type) => (analysis.counts[type] ?? 0) > 0
  );
  if (!visibleTypes.length) {
    return null;
  }
  const primaryType = visibleTypes[0];
  const primaryCount = analysis.counts[primaryType] ?? 0;
  return (
    <div className="demand-pattern-card">
      <div className="demand-pattern-border">
        <div className="demand-pattern-caption">Demand Pattern</div>
        <div className="demand-pattern-content">
          <p className="demand-pattern-title">{primaryType} Demand</p>
          <p className="demand-pattern-description">
            {DEMAND_EXPLANATIONS[primaryType]}
          </p>
        </div>
        <div className="demand-pattern-footer">
          <span className="demand-pattern-count">
            Products: {primaryCount}
          </span>
          <button
            type="button"
            className="demand-pattern-view"
            onClick={() => onView(primaryType)}
          >
            View
          </button>
        </div>
      </div>
    </div>
  );
};

const parseSalesValue = (value: string | undefined): number | null => {
  if (!value) {
    return null;
  }
  const cleaned = value.replace(/[^0-9.\-]/g, "");
  if (!cleaned) {
    return null;
  }
  const parsed = Number(cleaned);
  return Number.isNaN(parsed) ? null : parsed;
};

const detectSeasonalPattern = (series: number[]): boolean => {
  if (series.length < 24) {
    return false;
  }
  const cycleLengths = [7, 14, 28, 30];
  const mean =
    series.reduce((sum, value) => sum + value, 0) / (series.length || 1);

  if (mean === 0) {
    return false;
  }

  for (const cycle of cycleLengths) {
    if (series.length < cycle * 2) {
      continue;
    }
    const patternSums = new Array(cycle).fill(0);
    const patternCounts = new Array(cycle).fill(0);
    series.forEach((value, index) => {
      const position = index % cycle;
      patternSums[position] += value;
      patternCounts[position] += 1;
    });

    const patternAverages = patternSums.map((sum, index) =>
      patternCounts[index] ? sum / patternCounts[index] : 0
    );

    const rmse = Math.sqrt(
      series.reduce((acc, value, index) => {
        const expected = patternAverages[index % cycle];
        return acc + (value - expected) ** 2;
      }, 0) / series.length
    );

    const normalizedError = rmse / Math.abs(mean);
    if (normalizedError <= 0.15) {
      return true;
    }
  }

  return false;
};

const classifyDemand = (series: number[]): DemandType => {
  const length = series.length;
  const mean = length
    ? series.reduce((sum, value) => sum + value, 0) / length
    : 0;
  const variance = length
    ? series.reduce((sum, value) => sum + (value - mean) ** 2, 0) / length
    : 0;
  const std = Math.sqrt(variance);
  const cv = mean !== 0 ? std / mean : 0;
  const zeroRatio = length
    ? series.filter((value) => value === 0).length / length
    : 0;

  if (length < 20) {
    return "New";
  }
  if (zeroRatio >= 0.4) {
    return "Intermittent";
  }
  if (cv <= 0.5) {
    return "Smooth";
  }
  const classification: DemandType = "Erratic";
  if (detectSeasonalPattern(series)) {
    return "Seasonal";
  }
  return classification;
};

const buildFeatureStore = (
  rows: CsvRow[],
  mapping: {
    dateColumn: string;
    salesColumn: string;
    productColumn: string;
    storeColumn: string;
    dataProductNameColumn: string;
    dataProductCategoryColumn: string;
    dataStoreNameColumn: string;
  },
  selectedLocationColumns: string[]
): FeatureStore | null => {
  if (!mapping.salesColumn || !mapping.dateColumn) {
    return null;
  }

  const demandSeries: Record<string, number[]> = {};
  const products = new Set<string>();
  const stores = new Set<string>();
  let firstTimestamp: number | null = null;
  let lastTimestamp: number | null = null;
  const productMetadata: Record<string, ProductMetadata> = {};

  const addToSeries = (prefix: "product" | "location", key: string, value: number) => {
    const seriesKey = `${prefix}:${key}`;
    if (!demandSeries[seriesKey]) {
      demandSeries[seriesKey] = [];
    }
    demandSeries[seriesKey].push(value);
  };

  const sanitizeProductValue = (value?: string) => {
    if (!value) {
      return undefined;
    }
    const trimmed = value.trim();
    if (!trimmed) {
      return undefined;
    }
    const lower = trimmed.toLowerCase();
    if (lower === "unknown" || lower === "unknown product") {
      return undefined;
    }
    return trimmed;
  };

  rows.forEach((row) => {
    const salesValue = parseSalesValue(row[mapping.salesColumn]);
    if (salesValue === null) {
      return;
    }
    const dateValue = row[mapping.dateColumn];
    if (!dateValue) {
      return;
    }
    const parsedDate = new Date(dateValue);
    if (Number.isNaN(parsedDate.getTime())) {
      return;
    }

    const productKey = getProductGroupKey(row, {
      productColumn: mapping.productColumn,
      dataProductNameColumn: mapping.dataProductNameColumn,
      dataProductCategoryColumn: mapping.dataProductCategoryColumn,
    });
    const locationKey = getLocationGroupKey(row, {
      storeColumn: mapping.storeColumn,
      dataStoreNameColumn: mapping.dataStoreNameColumn,
      selectedLocationColumns,
    });

    const addProductMetadata = (key: keyof ProductMetadata, value?: string) => {
      const cleanValue = sanitizeProductValue(value);
      if (!productMetadata[productKey]) {
        productMetadata[productKey] = {};
      }
      if (cleanValue && !productMetadata[productKey][key]) {
        productMetadata[productKey][key] = cleanValue;
      }
    };
    addProductMetadata("productId", row[mapping.productColumn]);
    addProductMetadata("productName", row[mapping.dataProductNameColumn]);
    addProductMetadata("productCategory", row[mapping.dataProductCategoryColumn]);

    addToSeries("product", productKey, salesValue);
    addToSeries("location", locationKey, salesValue);

    products.add(productKey);
    stores.add(locationKey);

    const timestamp = parsedDate.getTime();
    if (firstTimestamp === null || timestamp < firstTimestamp) {
      firstTimestamp = timestamp;
    }
    if (lastTimestamp === null || timestamp > lastTimestamp) {
      lastTimestamp = timestamp;
    }
  });

  const dateRange =
    firstTimestamp !== null && lastTimestamp !== null
      ? `${new Date(firstTimestamp).toISOString().split("T")[0]} → ${new Date(
          lastTimestamp
        ).toISOString().split("T")[0]}`
      : "";

  return {
    demandSeries,
    metadata: {
      products: Array.from(products),
      stores: Array.from(stores),
      dateRange,
    },
    productMetadata,
  };
};

const analysisEngine = (store: FeatureStore): AnalysisResults => {
  const analyze = (prefix: "product" | "location"): DemandAnalysisResult => {
    const result = createEmptyDemandAnalysis();
    Object.entries(store.demandSeries).forEach(([key, series]) => {
      if (!key.startsWith(`${prefix}:`) || !series.length) {
        return;
      }
      result.totalGroups += 1;
      const classification = classifyDemand(series);
      result.counts[classification] += 1;
      const keyLabel = key.startsWith(`${prefix}:`)
        ? key.slice(prefix.length + 1)
        : key;
      result.groupsByType[classification].push(keyLabel || "Unknown");
    });
    return result;
  };

  return {
    productDemandAnalysis: analyze("product"),
    locationDemandAnalysis: analyze("location"),
    productMetadata: store.productMetadata,
  };
};

const decisionLayer = (
  store: FeatureStore,
  fallbackTimeRange?: string
): DecisionInsights => {
  const { metadata } = store;
  const heroNotes: string[] = [];
  if (!metadata.products.length) {
    heroNotes.push("Product identifiers could not be inferred.");
  }
  if (!metadata.stores.length) {
    heroNotes.push("Store identifiers could not be inferred.");
  }

  return {
    timeRange: metadata.dateRange || fallbackTimeRange,
    heroAlert: heroNotes.length ? heroNotes.join(" ") : undefined,
  };
};

const getProductGroupKey = (
  row: CsvRow,
  mapping: {
    productColumn: string;
    dataProductNameColumn: string;
    dataProductCategoryColumn: string;
  }
) => {
  if (mapping.productColumn && row[mapping.productColumn]) {
    return row[mapping.productColumn];
  }
  if (mapping.dataProductNameColumn && row[mapping.dataProductNameColumn]) {
    return row[mapping.dataProductNameColumn];
  }
  if (mapping.dataProductCategoryColumn && row[mapping.dataProductCategoryColumn]) {
    return row[mapping.dataProductCategoryColumn];
  }
  return "Unknown Product";
};

const getLocationGroupKey = (
  row: CsvRow,
  mapping: {
    storeColumn: string;
    dataStoreNameColumn: string;
    selectedLocationColumns: string[];
  }
) => {
  if (mapping.storeColumn && row[mapping.storeColumn]) {
    return row[mapping.storeColumn];
  }
  if (mapping.dataStoreNameColumn && row[mapping.dataStoreNameColumn]) {
    return row[mapping.dataStoreNameColumn];
  }
  if (mapping.selectedLocationColumns.length) {
    for (const column of mapping.selectedLocationColumns) {
      if (row[column]) {
        return row[column];
      }
    }
    const fallbackColumn = mapping.selectedLocationColumns[0];
    if (fallbackColumn) {
      return row[fallbackColumn] || "Unknown Location";
    }
  }
  return "Unknown Location";
};

const formatPercent = (value: number) => {
  const formatted = value.toFixed(1);
  if (formatted.endsWith(".0")) {
    return `${formatted.slice(0, -2)}%`;
  }
  return `${formatted}%`;
};

const getTimeRangeLabel = (rows: CsvRow[], column: string) => {
  if (!rows.length || !column) {
    return null;
  }
  const startValue = rows[0][column];
  const endValue = rows[rows.length - 1][column];
  if (!startValue || !endValue) {
    return null;
  }
  const startDate = new Date(startValue);
  const endDate = new Date(endValue);
  if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
    return null;
  }
  const format = (date: Date) =>
    date.toLocaleString("en-US", { month: "short", year: "numeric" });
  return `${format(startDate)} → ${format(endDate)}`;
};

const categorizeMissingLevel = (missingRatio: number) => {
  if (missingRatio < CONFIG.MISSING_THRESHOLDS.LOW) {
    return "Low";
  }
  if (missingRatio < CONFIG.MISSING_THRESHOLDS.HIGH) {
    return "Moderate";
  }
  return "High";
};

const togglePreview = () => {
  setPreviewExpanded((prev) => !prev);
};

  const previewRows = rawRows.slice(0, 5);
  const hasParsedData = Boolean(columns.length && rawRows.length);
  const uploadErrorMessage =
    uploadError === "unsupported"
      ? "Unsupported file format"
      : uploadError === "empty"
        ? "Empty File is not Supported"
        : uploadError === "corrupt"
          ? "File Uploaded is corrupt"
          : uploadError === "tooLarge"
            ? FILE_TOO_LARGE_MESSAGE
            : null;

  const uploadComplete = hasParsedData;
  const mappingComplete = Boolean(dataSummary);
  const summaryComplete = Boolean(dataSummary);
  const demandComplete = Boolean(analysisResults);
  const configComplete = forecastRequested;
  const generateComplete = Boolean(overallForecastSection);

  const completionFlags: Record<ForecastStepKey, boolean> = {
    upload: uploadComplete,
    mapping: mappingComplete,
    summary: summaryComplete,
    demand: demandComplete,
    config: configComplete,
    generate: generateComplete,
    insights: false,
  };

  const firstIncompleteStepIndex = FORECAST_STEPS.findIndex(
    (step) => !completionFlags[step.key]
  );
  const activeForecastStepIndex =
    firstIncompleteStepIndex !== -1 ? firstIncompleteStepIndex : FORECAST_STEPS.length - 1;

  const handleStepperClick = (stepKey: ForecastStepKey, index: number) => {
    if (index >= activeForecastStepIndex) {
      return;
    }
    if (typeof document === "undefined") {
      return;
    }
    const target = document.querySelector(`[data-step="${stepKey}"]`);
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  };

  const buildCurrentMapping = (): DataMapping => ({
    dateColumn,
    salesColumn,
    productColumn,
    storeColumn,
  });

  const matchesLocationKeyword = (column: string) => {
    const normalized = normalizeColumnName(column);
    return LOCATION_KEYWORDS.some((keyword) => normalized.includes(keyword));
  };

  const locationColumnCandidates = useMemo(
    () => columns.filter(matchesLocationKeyword),
    [columns]
  );

  useEffect(() => {
    setSelectedLocationColumns(locationColumnCandidates);
  }, [locationColumnCandidates]);

  const usedLocationColumns = Array.from(
    new Set([...locationColumnCandidates, ...selectedLocationColumns])
  );

  const assignedColumnsForAdditional = new Set(
    [
      dateColumn,
      salesColumn,
      productColumn,
      storeColumn,
      dataStoreNameColumn,
      dataProductNameColumn,
      dataProductCategoryColumn,
      ...usedLocationColumns,
    ].filter(Boolean)
  );
  const additionalColumns = columns.filter(
    (column) => column && !assignedColumnsForAdditional.has(column)
  );

  const IMPORTANT_ADDITIONAL_KEYWORDS = ["price", "discount", "promo", "cost"];
  const recommendedImportantColumns = useMemo(
    () =>
      additionalColumns
        .filter((column) =>
          IMPORTANT_ADDITIONAL_KEYWORDS.some((keyword) =>
            normalizeColumnName(column).includes(keyword)
          )
        )
        .slice(0, 3),
    [additionalColumns]
  );

  const productDemandAnalysis =
    analysisResults?.productDemandAnalysis ?? createEmptyDemandAnalysis();
  
  const locationDemandAnalysis =
    analysisResults?.locationDemandAnalysis ?? createEmptyDemandAnalysis();

  const availableDataDays = dataCoverageDays ?? 0;
  const availableTimeGroupingOptions = useMemo(
    () => TIME_GROUPING_OPTIONS.filter((option) => forecastDurationDays >= option.minDays),
    [forecastDurationDays],
  );
  useEffect(() => {
    if (!availableTimeGroupingOptions.length) {
      return;
    }
    if (
      availableTimeGroupingOptions.every(
        (option) => option.value !== forecastGranularity
      )
    ) {
      setForecastGranularity(availableTimeGroupingOptions[0].value);
    }
  }, [availableTimeGroupingOptions, forecastGranularity]);
  const timeGroupingHelperText = forecastDurationDays
    ? availableTimeGroupingOptions.length
      ? `${availableTimeGroupingOptions
          .map((option) => option.label)
          .join(", ")} unlocked by a ${forecastDurationDays}-day forecast.`
      : ""
    : "Select a forecast duration to unlock grouping options.";

  const visibleForecastDurations = useMemo(
    () =>
      maxForecastDays
        ? FORECAST_DURATION_OPTIONS.filter((option) => option.value <= maxForecastDays)
        : FORECAST_DURATION_OPTIONS,
    [maxForecastDays],
  );

  useEffect(() => {
    if (!visibleForecastDurations.length) {
      return;
    }
    if (
      visibleForecastDurations.every((option) => option.value !== forecastDurationDays)
    ) {
      setForecastDurationDays(visibleForecastDurations[0].value);
    }
  }, [visibleForecastDurations, forecastDurationDays]);



  const forecastDurationHelperText = maxForecastDays
    ? ""
    : "Clean the data to unlock forecast durations.";
  const handleExportDemandIntelligence = () => {
    if (!productDemandAnalysis.totalGroups) {
      return;
    }
    const productMetadata = analysisResults?.productMetadata ?? {};
    const exportRows: string[][] = [];
    const demandTypes = getDemandTypes();
    demandTypes.forEach((type) => {
      const productKeys = productDemandAnalysis.groupsByType[type] ?? [];
      productKeys.forEach((productKey) => {
        const metadata = productMetadata[productKey] ?? {};
        exportRows.push([
          metadata.productId ?? productKey,
          metadata.productName ?? "",
          metadata.productCategory ?? "",
          type,
        ]);
      });
    });
    const rows = [
      ["Product ID/SKU", "Product Name", "Product Category", "Demand Type"],
      ...exportRows,
    ];
    const quoteValue = (value: string) =>
      `"${(value ?? "").replace(/"/g, '""')}"`;
    const csvContent = rows
      .map((row) => row.map((value) => quoteValue(value)).join(","))
      .join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "demand-intelligence.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleViewDemandType = (
    type: DemandType,
    source: "product" | "location"
  ) => {
    const analysis =
      source === "product" ? productDemandAnalysis : locationDemandAnalysis;
    const products = analysis.groupsByType[type] ?? [];
    const { visible, remaining } = getPreviewProducts(products);
    const label = source === "product" ? "Products" : "Locations";
    setDemandInsightModal({
      title: `${type} ${label}`,
      list: visible,
      more: remaining > 0 ? `+${remaining} more...` : null,
    });
  };

  useEffect(() => {
    setSelectedAdditionalFeatures((prev) => {
      const filtered = prev.filter((column) => additionalColumns.includes(column));
      if (filtered.length) {
        return filtered;
      }
      return recommendedImportantColumns;
    });
  }, [additionalColumns, recommendedImportantColumns]);

  const clearUploadedFile = (options?: ClearUploadedFileOptions) => {
    setUploadedFileName(null);
    setFileSizeLabel(null);
    setColumns([]);
    // previewRows derived from rawRows, no need to reset separately
    setRawRows([]);
    setCleanedRows([]);
    setAnalysisResults(null);
    if (!options?.keepStatus) {
      setStatusMessage(null);
    }
    setDateColumn("");
    setSalesColumn("");
    setProductColumn("");
    setStoreColumn("");
    setDataStoreNameColumn("");
    setDataProductNameColumn("");
    setDataProductCategoryColumn("");
    setDataCoverageDays(null);
    setMaxForecastDays(null);
    setIsValidating(false);
    setValidationModal(null);
    setDataSummary(null);
    setPreviewExpanded(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    setSelectedAdditionalFeatures([]);
    setIsDropzoneActive(false);
    setUploadError(options?.nextError ?? null);
    setHeroAlert(null);
    setForecastRequested(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
    setHasSavedForecast(false);
  };

  const swallowLargeFileError = (error: unknown) => {
    if (error instanceof Error && error.message === FILE_TOO_LARGE_MESSAGE) {
      return;
    }
    throw error;
  };

  const handleBrowseAgain = (event: MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setUploadError(null);
    setStatusMessage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
      fileInputRef.current.click();
    }
  };

  const toggleAdditionalFeature = (column: string) => {
    setSelectedAdditionalFeatures((prev) => {
      if (prev.includes(column)) {
        return prev.filter((value) => value !== column);
      }
      return [...prev, column];
    });
  };

  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerateForecast = () => {
    setHasSavedForecast(false);
    setForecastRequested(true);
    
    if (!lastConfirmedData) {
      console.warn("Generate forecast clicked but no data is confirmed.");
      setStatusMessage("No data detected. Please upload and confirm mapping first.");
      setOverallForecastSection(null);
      return;
    }
    const { cleaned, mapping } = lastConfirmedData;
    if (!mapping.dateColumn || !mapping.salesColumn || !cleaned.length) {
      console.error("Missing column mapping:", mapping);
      setStatusMessage("Missing required column mapping (Date/Sales).");
      setOverallForecastSection(null);
      return;
    }

    const dates: string[] = [];
    const sales: number[] = [];

    let filtered = cleaned;
    // Apply filtering based on selection if level is not overall
    if ((forecastLevel === "product" || forecastLevel === "combined") && selectedProductKey) {
      filtered = cleaned.filter((row) => row[mapping.productColumn] === selectedProductKey);
    } else if ((forecastLevel === "product" || forecastLevel === "combined") && selectedCategory) {
      filtered = cleaned.filter(
        (row) => productMetadata[row[mapping.productColumn]]?.productCategory === selectedCategory
      );
    }

    filtered.forEach((row) => {
      const dateVal = row[mapping.dateColumn];
      const salesVal = parseFloat(row[mapping.salesColumn] || "");
      if (dateVal && !isNaN(salesVal)) {
        dates.push(String(dateVal).slice(0, 10));
        sales.push(salesVal);
      }
    });

    if (dates.length < 2) {
      console.error("Insufficient data points after filtering:", dates.length);
      setStatusMessage("Insufficient data points found for the selected filter. Need at least 2 points.");
      setOverallForecastSection(null);
      return;
    }

    console.log(`Starting forecast generation for ${dates.length} points...`);

    setIsGenerating(true);
    setHasSavedForecast(false);
    setOverallForecastSection(null);
    setStatusMessage("Running Facebook Prophet model on backend...");

    const apiBase = (import.meta as any).env?.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

    fetch(apiBase + "/forecast/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        dates,
        sales,
        forecastDays: forecastDurationDays,
        timeGrouping: forecastGranularity,
      }),
    })
      .then((res) => {
        if (!res.ok) {
          return res.json().then((errData) => {
            throw new Error(errData.detail || "Server error");
          });
        }
        return res.json();
      })
      .then((data) => {
        setIsGenerating(false);
        if (data.status === "success") {
          setOverallForecastSection(data);
          setStatusMessage("Prophet forecast generated successfully. Saving and redirecting...");
          
          // Save to global store so it shows up on the main demand page
          setLatestForecastSnapshot({
            section: data,
            forecastLevel,
            productCategoryOptions,
            productOptions,
            selectedCategory,
            selectedProductKey,
            locationFieldConfig,
            locationOptionsByField,
            locationSelections,
            insightHighlights,
          });
          
          console.log("Forecast saved to store. Navigating...");
          // Small delay ensures store notifyListeners finishes if there's any sync work
          // // setTimeout(() => onNavigate("demandForecasting"), 300);
        } else {
          setStatusMessage(data.detail || data.message || "Forecast failed.");
          setOverallForecastSection(null);
        }
      })
      .catch((err) => {
        setIsGenerating(false);
        console.error("Prophet backend error:", err);
        setStatusMessage(`Backend error: ${err.message}. Ensure backend is running.`);
        setOverallForecastSection(null);
      });
  };

  const toggleLocationColumn = (column: string) => {
    setSelectedLocationColumns((prev) =>
      prev.includes(column) ? prev.filter((value) => value !== column) : [...prev, column]
    );
  };

  const processForecastFile = (file: File) => {
    if (file.size > MAX_UPLOAD_BYTES) {
      clearUploadedFile({ nextError: "tooLarge", keepStatus: true });
      setStatusMessage(null);
      throw new Error(FILE_TOO_LARGE_MESSAGE);
    }

    if (file.type && !VALID_UPLOAD_TYPES.includes(file.type)) {
      clearUploadedFile({ nextError: "unsupported", keepStatus: true });
      setStatusMessage("Unsupported file type");
      throw new Error("Unsupported file type");
    }

    const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
    if (!supportedForecastExtensions.has(extension)) {
      clearUploadedFile({ nextError: "unsupported", keepStatus: true });
      setStatusMessage(null);
      return;
    }

    setUploadError(null);
    setStatusMessage(null);

    const processCsv = (content: string) => {
      try {
        const parsed = parseCsvPreview(content, 6);
        if (!parsed || !parsed.headers.length || !parsed.rawRows.length) {
          clearUploadedFile({ nextError: "empty", keepStatus: true });
          setStatusMessage("Empty File is not Supported");
          return;
        }

        if (parsed.rawRows.length < 5 || parsed.headers.length < 2) {
          setValidationModal({
            title: "Dataset too small",
            message: DATASET_TOO_SMALL_ERROR,
            bullets: [DATASET_TOO_SMALL_BULLET],
          });
          setStatusMessage(DATASET_TOO_SMALL_ERROR);
          setHeroAlert(null);
          return;
        }

        const datasetLarge = parsed.rawRows.length > 200000;
        const heroWarning =
          datasetLarge
            ? LARGE_DATASET_WARNING
            : parsed.headers.length > 100
              ? LARGE_COLUMN_WARNING
              : null;
        if (heroWarning) {
          setHeroAlert(heroWarning);
        } else {
          setHeroAlert(null);
        }

        const detectedDateColumn =
          detectDateColumnSimple(parsed.headers, parsed.rawRows) ||
          pickColumn(parsed.headers, detectionKeywords.date);
        const fallbackSalesColumn = pickColumn(parsed.headers, detectionKeywords.sales);
        const detectedSalesColumn =
          detectSalesColumnSimple(parsed.headers, parsed.rawRows) ||
          (shouldRejectSalesColumn(fallbackSalesColumn) ? "" : fallbackSalesColumn);
        const detectedProductColumn = pickColumn(
          parsed.headers,
          PRODUCT_ID_KEYWORDS
        );
        const detectedStoreColumn =
          detectStoreIdColumnSimple(parsed.headers, parsed.rawRows) ||
          pickColumn(parsed.headers, detectionKeywords.storeId) ||
          pickColumn(parsed.headers, detectionKeywords.storeGeneral);
        const detectedStoreNameColumn =
          detectStoreNameColumnSimple(parsed.headers, parsed.rawRows, [
            detectedStoreColumn,
          ]) ||
          pickColumn(parsed.headers, detectionKeywords.storeName);
        const detectedProductNameColumn = pickColumn(
          parsed.headers,
          PRODUCT_NAME_KEYWORDS
        );

        setColumns(parsed.headers);
        setRawRows(parsed.rawRows);
        setDateColumn(detectedDateColumn);
        setSalesColumn(detectedSalesColumn);
        setProductColumn(detectedProductColumn);
        setStoreColumn(detectedStoreColumn);
        setDataStoreNameColumn(detectedStoreNameColumn);
        setDataProductNameColumn(detectedProductNameColumn);
        setDataProductCategoryColumn(
          pickColumn(parsed.headers, PRODUCT_CATEGORY_KEYWORDS)
        );
        setUploadedFileName(file.name);
        setFileSizeLabel(formatFileSize(file.size));
        setCleanedRows([]);
        setDataSummary(null);
        setValidationModal(null);
        setUploadError(null);
        const parsedStatusMessage =
          heroWarning ?? "Parsed the uploaded data. Please confirm column mapping below.";
        setStatusMessage(parsedStatusMessage);
      } catch {
        clearUploadedFile({ nextError: "corrupt", keepStatus: true });
        setStatusMessage("File Uploaded is corrupt");
      }
    };

    loadFileAsCsv(file)
      .then(processCsv)
      .catch(() => {
        clearUploadedFile({ nextError: "corrupt", keepStatus: true });
        setStatusMessage("File Uploaded is corrupt");
      });
  };

    const handleDropzoneDragEnter = (event: DragEvent<HTMLLabelElement>) => {
      event.preventDefault();
      setIsDropzoneActive(true);
    };

    const handleDropzoneDragOver = (event: DragEvent<HTMLLabelElement>) => {
      event.preventDefault();
      event.dataTransfer.dropEffect = "copy";
      setIsDropzoneActive(true);
    };

  const handleDropzoneDragLeave = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    const nextTarget = event.relatedTarget;
    if (nextTarget instanceof Node && event.currentTarget.contains(nextTarget)) {
      return;
    }
    setIsDropzoneActive(false);
  };

  const handleDropzoneDrop = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    setIsDropzoneActive(false);
    const files = event.dataTransfer?.files;
    if (!files?.length) {
      return;
    }

    if (files.length > 1) {
      setStatusMessage("Please drop only one file at a time.");
      return;
    }

    try {
      processForecastFile(files[0]);
    } catch (error) {
      swallowLargeFileError(error);
    }
  };

  const loadSampleData = () => {
    const headers = ["Order Date", "Product Name", "Product Category", "Sales"];
    const rows: CsvRow[] = [];
    const products = [
      { name: "Headphones", cat: "Electronics" },
      { name: "Sneakers", cat: "Apparel" },
      { name: "Smartwatch", cat: "Electronics" }
    ];
    
    const now = new Date();
    // Generate 2 years of daily data
    for (let i = 730; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      const dateStr = date.toISOString().split('T')[0];
      
      products.forEach(p => {
        // Generate some seasonal/trended sales
        const base = p.name === "Headphones" ? 50 : 30;
        const trend = (730 - i) / 10;
        const seasonality = Math.sin(i / 10) * 20;
        const noise = Math.random() * 10;
        const sales = Math.max(0, Math.round(base + trend + seasonality + noise));
        
        const row: CsvRow = {
          "Order Date": dateStr,
          "Product Name": p.name,
          "Product Category": p.cat,
          "Sales": sales.toString()
        };
        // Add some noise columns
        row["Store ID"] = "S001";
        row["Region"] = "West";
        rows.push(row);
      });
    }

    setColumns(headers.concat(["Store ID", "Region"]));
    setRawRows(rows);
    setDateColumn("Order Date");
    setSalesColumn("Sales");
    setProductColumn("Product Name");
    setDataProductCategoryColumn("Product Category");
    setStoreColumn("Store ID");
    setUploadedFileName("sample_demand_data.csv");
    setStatusMessage("Loaded 2 years of sample data. Click 'Confirm Mapping' to continue.");
  };

  const handleConfirmMapping = () => {
    if (!columns.length || !rawRows.length) {
      setStatusMessage("Upload a dataset before confirming the mapping.");
      return;
    }

    const mapping = buildCurrentMapping();
    setIsValidating(true);
    setForecastRequested(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
    setValidationModal(null);
    setDataSummary(null);
    setPreviewExpanded(false);
    setStatusMessage("Validating your data...");
    setCleanedRows([]);
    setAnalysisResults(null);

    const runValidation = () => {
      const missingFields: string[] = [];
      if (!mapping.dateColumn) {
        missingFields.push("Date column");
      }
      if (!mapping.salesColumn) {
        missingFields.push("Sales column");
      }

      if (missingFields.length) {
        setValidationModal({
          title: "Required columns missing",
          message:
            "Forecast cannot be generated until the following required fields are mapped:",
          bullets: missingFields.map((field) => `${field} is required.`),
        });
        setStatusMessage("Cannot generate forecast without required columns.");
        setIsValidating(false);
        return;
      }

      const selectedColumns = [
        mapping.dateColumn,
        mapping.salesColumn,
        mapping.productColumn,
        mapping.storeColumn,
      ].filter(Boolean);
      if (new Set(selectedColumns).size !== selectedColumns.length) {
        setValidationModal({
          title: "Column conflict",
          message:
            "Each role must map to a unique column before the forecast can be generated.",
          bullets: ["Ensure Date, Sales, Product, and Store each point to a different column."],
        });
        setStatusMessage("Resolve duplicate column assignments.");
        setIsValidating(false);
        return;
      }

      if (
        mapping.dateColumn &&
        mapping.salesColumn &&
        mapping.dateColumn === mapping.salesColumn
      ) {
        setValidationModal({
          title: "Column conflict",
          message:
            "Date and Sales columns cannot be the same because each must represent a different dimension.",
          bullets: ["Select distinct columns for Date and Sales."],
        });
        setStatusMessage("Cannot generate forecast with overlapping columns.");
        setIsValidating(false);
        return;
      }

      const lowQualityColumns: string[] = [];
      const collectLowCoverage = (column: string, label: string) => {
        const ratio = columnStats[column]?.nonNullRatio;
        if (column && ratio !== undefined && ratio < CONFIG.MIN_COVERAGE) {
          lowQualityColumns.push(label);
        }
      };
      collectLowCoverage(mapping.salesColumn, "Sales");
      collectLowCoverage(mapping.dateColumn, "Date");
      const hasLowCoverage = lowQualityColumns.length > 0;
      if (hasLowCoverage) {
        const columnListDisplay =
          lowQualityColumns.length === 1
            ? lowQualityColumns[0]
            : lowQualityColumns.join("/");
        setValidationModal({
          title: `${columnListDisplay} column${lowQualityColumns.length > 1 ? "s" : ""} have too many missing values`,
          message: `Forecast needs ${columnListDisplay.toLowerCase()} data in at least 30% of rows.`,
          bullets: [],
        });
        setStatusMessage(
          `${columnListDisplay} column${lowQualityColumns.length > 1 ? "s" : ""} have many missing values — forecast accuracy may be affected`
        );
      }

      const invalidSales = !isNumericColumn(rawRows, mapping.salesColumn);
      const invalidDate = !isDateColumn(rawRows, mapping.dateColumn);

      if (invalidSales || invalidDate) {
        setValidationModal({
          title: "Invalid column selection",
          message:
            "Forecast cannot be generated until these columns contain valid data:",
          bullets: [
            "Sales column contains numeric values",
            "Date column contains valid dates",
          ],
        });
        setStatusMessage("Cannot generate forecast with invalid columns.");
        setIsValidating(false);
        return;
      }

      const { rows: cleaned, hasNegativeSales } = cleanForecastData(
        rawRows,
        columns,
        mapping
      );
      if (mapping.dateColumn) {
        cleaned.sort(
          (a, b) =>
            new Date(a[mapping.dateColumn]).getTime() -
            new Date(b[mapping.dateColumn]).getTime()
        );
      }
      const salesValues =
        mapping.salesColumn && cleaned.length
          ? cleaned
              .map((row) => {
                const value = Number(row[mapping.salesColumn]);
                return Number.isNaN(value) ? null : value;
              })
              .filter((value): value is number => value !== null)
          : [];
      let hasOutliers = false;
      if (salesValues.length) {
        const mean = salesValues.reduce((sum, val) => sum + val, 0) / salesValues.length;
        const variance =
          salesValues.reduce((sum, val) => sum + (val - mean) ** 2, 0) /
          salesValues.length;
        const stdDev = Math.sqrt(variance);
        const outliers = stdDev
          ? salesValues.filter((val) => Math.abs(val - mean) > CONFIG.OUTLIER_SIGMA * stdDev)
          : salesValues.filter((val) => Math.abs(val - mean) > 0);
        hasOutliers = outliers.length > 0;
      }
      const coverageColumns = [mapping.salesColumn, mapping.dateColumn].filter(Boolean);
      const coverageRatios = coverageColumns
        .map((column) => columnStats[column])
        .filter((stats): stats is ColumnMetrics => Boolean(stats))
        .map((stats) => stats.nonNullRatio);
      const coverageForMissing = coverageRatios.length
        ? Math.min(...coverageRatios)
        : 1;
      const missingValuesLabel = categorizeMissingLevel(1 - coverageForMissing);
      const retentionValue = rawRows.length
        ? (cleaned.length / rawRows.length) * 100
        : 0;
      const dataRetention = formatPercent(retentionValue);
      const timeRangeLabel =
        mapping.dateColumn && cleaned.length
          ? getTimeRangeLabel(cleaned, mapping.dateColumn) ?? undefined
          : undefined;
      let coverageDays: number | null = null;
      if (mapping.dateColumn && cleaned.length) {
        const startValue = cleaned[0][mapping.dateColumn];
        const endValue = cleaned[cleaned.length - 1][mapping.dateColumn];
        if (startValue && endValue) {
          const startDate = new Date(startValue);
          const endDate = new Date(endValue);
          if (
            !Number.isNaN(startDate.getTime()) &&
            !Number.isNaN(endDate.getTime())
          ) {
            const span =
              Math.round((endDate.getTime() - startDate.getTime()) / MS_PER_DAY) + 1;
            coverageDays = Math.max(1, span);
          }
        }
      }
      const rowsTooSmall = cleaned.length <= CONFIG.MIN_ROWS;
      const forecastCap =
        coverageDays !== null ? Math.max(1, Math.floor(coverageDays * 0.5)) : null;
      setDataCoverageDays(coverageDays);
      setMaxForecastDays(forecastCap);

      const productMetric = buildProductMetric(cleaned, columns, mapping);
      const storeMetric = buildStoreMetric(cleaned, columns, mapping);
      const featureStorePayload =
        rowsTooSmall
          ? null
          : buildFeatureStore(
              cleaned,
              {
                dateColumn: mapping.dateColumn,
                salesColumn: mapping.salesColumn,
                productColumn: mapping.productColumn,
                storeColumn: mapping.storeColumn,
                dataProductNameColumn,
                dataProductCategoryColumn,
                dataStoreNameColumn,
              },
              selectedLocationColumns
            );
      const analysisPayload = featureStorePayload
        ? analysisEngine(featureStorePayload)
        : null;
      const insights = featureStorePayload
        ? decisionLayer(featureStorePayload, timeRangeLabel)
        : null;

      setAnalysisResults(analysisPayload);
      setHeroAlert((prev) => {
        if (prev) {
          return prev;
        }
        return insights?.heroAlert ?? null;
      });
      const summaryTimeRange = insights?.timeRange ?? timeRangeLabel;

      setCleanedRows(cleaned);
      const negativeSalesLabel = hasNegativeSales ? "Present" : "No";
      const outliersLabel = hasOutliers ? "Detected" : "Not Detected";
      const fallbackStatus = "Not enough data for demand classification";
      const summaryStatus = rowsTooSmall ? fallbackStatus : "Cleaned & Ready";

      setDataSummary({
        fileName: uploadedFileName ?? "Uploaded file",
        rows: cleaned.length,
        columns: columns.length,
        duplicatesRemoved: Math.max(0, rawRows.length - cleaned.length),
        status: summaryStatus,
        dataRetention,
        fileSizeLabel: fileSizeLabel ?? "—",
        missingValuesLabel,
        negativeSalesLabel,
        outliersLabel,
        ...(summaryTimeRange ? { timeRange: summaryTimeRange } : {}),
        ...(productMetric ? { productMetric } : {}),
        ...(storeMetric ? { storeMetric } : {}),
      });
      setLastConfirmedData({ cleaned, mapping });
      setPreviewExpanded(false);
      const finalStatusMessage = rowsTooSmall
        ? fallbackStatus
        : hasNegativeSales
        ? "Dataset contains negative sales values"
        : hasOutliers
        ? "Potential outliers detected in sales data"
        : "Data cleaned successfully. Ready for forecasting.";
      setStatusMessage(finalStatusMessage);
      setIsValidating(false);
    };

    setTimeout(runValidation, 400);
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      clearUploadedFile();
      return;
    }
    try {
      processForecastFile(file);
    } catch (error) {
      swallowLargeFileError(error);
    }
  };

  return (
    <div className="demand-page">
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setSidebarOpen(false)}
        activePage={activePage}
        onNavigate={onNavigate}
      />

        <main className="demand-main" style={{ marginTop: 12 }}>
          <Header
            title=" 📈 Generate New Forecast"
            subtitle="Configure Parameters to run high-fidelity AI prediction models"
            lastUpdated={lastUpdated}
            searchTerm={searchTerm}
            onSearchChange={setSearchTerm}
            onRefresh={() => setSidebarOpen((prev) => prev)}
            onMenuClick={() => setSidebarOpen(true)}
            showHelp
            showSearch={false}
          />
            {heroAlert ? (
              <div className="hero-alert">
                <span>{heroAlert}</span>
              </div>
            ) : null}
            <div className="demand-content">
              <div className="forecast-workspace">
                <div className="forecast-stepper-card">
                  <p className="forecast-section-kicker">
                    Step {activeForecastStepIndex + 1} of {FORECAST_STEPS.length}
                  </p>
                  <div className="forecast-stepper">
                    {FORECAST_STEPS.map((step, index) => {
                      const status =
                        index < activeForecastStepIndex
                          ? "completed"
                          : index === activeForecastStepIndex
                            ? "active"
                            : "pending";
                      return (
                        <div key={step.key} className={`forecast-stepper-stage ${status}`}>
                          <button
                            type="button"
                            className="forecast-stepper-button"
                            onClick={() => handleStepperClick(step.key, index)}
                            disabled={status !== "completed"}
                          >
                            <span className="forecast-stepper-circle" aria-hidden="true">
                              {status === "completed" ? "✔" : index + 1}
                            </span>
                            <span className="forecast-stepper-label">{step.label}</span>
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>
                <section className="forecast-section upload-section" data-step="upload">
                  <div className="forecast-section-header">
                    <div>
                      <h3>Upload &amp; Inspect</h3>
                    </div>
                  </div>
                  <p className="forecast-section-subtitle">
                    Drag or select your historical CSV/XLSX. We look for date, sales, product, store, and price columns.
                  </p>
                  <label
                    className={`upload-dropzone ${uploadedFileName ? "has-file" : ""} ${isDropzoneActive ? "drag-active" : ""}`}
                    htmlFor="forecast-upload"
                    onDragEnter={handleDropzoneDragEnter}
                    onDragOver={handleDropzoneDragOver}
                    onDragLeave={handleDropzoneDragLeave}
                    onDrop={handleDropzoneDrop}
                  >
                    <input
                      id="forecast-upload"
                      type="file"
                      accept=".csv,.xlsx,.xls"
                      onChange={handleFileChange}
                      ref={fileInputRef}
                    />
                    <div>
                      {uploadedFileName ? (
                        <div className="upload-loaded">
                          <button
                            type="button"
                            className="upload-clear"
                            aria-label="Remove uploaded file"
                            onClick={(event) => {
                              event.stopPropagation();
                              clearUploadedFile();
                            }}
                          >
                            ×
                          </button>
                          <p className="upload-loaded-name">
                            Loaded: {uploadedFileName}
                          </p>
                          {fileSizeLabel ? (
                            <p className="upload-loaded-size">{fileSizeLabel}</p>
                          ) : null}
                        </div>
                      ) : uploadErrorMessage ? (
                        <>
                          <p className="upload-error">{uploadErrorMessage}</p>
                          <div style={{ display: "flex", justifyContent: "center", marginTop: 12 }}>
                            <button
                              type="button"
                              className="confirm-mapping demand-cta browse-again"
                              onClick={handleBrowseAgain}
                            >
                              Browse Again
                            </button>
                          </div>
                        </>
                      ) : (
                        <>
                          <p>Drop CSV file here</p>
                          <p>Or browse files on your system</p>
                          <div style={{ display: "flex", gap: "12px", justifyContent: "center", marginTop: 12 }}>
                            <button
                              type="button"
                              className="confirm-mapping demand-cta"
                              onClick={(e) => { e.preventDefault(); e.stopPropagation(); loadSampleData(); }}
                              style={{ background: "#4f46e5", padding: "8px 16px", fontSize: "0.85rem" }}
                            >
                              🚀 Load Sample Data
                            </button>
                          </div>
                          <p className="upload-secondary">
                            [Supported formats: CSV (Recommended), Excel (.xlsx, .xls)]
                          </p>
                          <p className="upload-secondary">[Max file size: 50MB]</p>
                        </>
                      )}
                    </div>
                  </label>
                  {statusMessage ? <p className="status-text">{statusMessage}</p> : null}
                </section>

            {hasParsedData && (
              <>
                {dataSummary ? (
                  <>
                    <section className="forecast-section data-summary-card" data-step="summary">
                <div className="data-summary-title">
                  <h3>Data summary</h3>
                  <p>Cleaned dataset ready for forecasting</p>
                </div>
                <div className="summary-details">
                  <div className="summary-line">
                    📄 File: {dataSummary.fileName}
                  </div>
                  <div className="summary-line">
                    📊 Rows: {formatNumber(dataSummary.rows)} | Columns:{" "}
                    {formatNumber(dataSummary.columns)}
                  </div>
                  <div className="summary-line">
                    📉 Duplicates Removed: {formatNumber(dataSummary.duplicatesRemoved)}
                  </div>
                  <div className="summary-line">
                    📦 File Size: {dataSummary.fileSizeLabel ?? "—"}
                  </div>
                  <div className="summary-line">
                    📈 Data Retention: {dataSummary.dataRetention ?? "—"}
                  </div>
                </div>
                <div className="summary-quality">
                  <p>⚙️ Data Quality</p>
                  <ul>
                    <li>
                      Missing Values: {dataSummary.missingValuesLabel ?? "Unknown"}
                    </li>
                    <li>
                      Negative Sales: {dataSummary.negativeSalesLabel ?? "Unknown"}
                    </li>
                    <li>
                      Outliers: {dataSummary.outliersLabel ?? "Unknown"}
                    </li>
                  </ul>
                </div>
                <div className="summary-extra">
                  {dataSummary.productMetric ? (
                    <span>{dataSummary.productMetric.text}</span>
                  ) : null}
                  {dataSummary.storeMetric ? (
                    <span>{dataSummary.storeMetric.text}</span>
                  ) : null}
                </div>
                {dataSummary.timeRange ? (
                  <p className="summary-time-range">
                    📅 Time Range: {dataSummary.timeRange}
                  </p>
                ) : null}
                <p className="summary-status">Status: {dataSummary.status}</p>
                    </section>
                  </>
                ) : null}

            {!dataSummary && (
              <section className="forecast-section mapping-section" data-step="mapping">
                <div className="forecast-section-header">
                  <div>
                    <h3>Column Mapping</h3>
                    <p
                      className="forecast-section-subtitle mapping-subtitle"
                      style={{
                        marginTop: 32,
                        fontFamily: '"Inter", sans-serif',
                        fontSize: "0.95rem",
                        lineHeight: 1.6,
                      }}
                    >
                      ChainMind intelligently detects key columns and suggests a mapping based on the data. You can review and adjust everything manually.
                    </p>
                  </div>
                  <span className="status-pill status-pill-secondary">Auto mapping</span>
                </div>

                <div className="mapping-block" style={{ marginTop: 20, marginBottom: 24 }}>
                  <div className="mapping-block-header" style={{ marginBottom: 8 }}>
                    <h4>Section A: Core Inputs (Required)</h4>
                    <div className="mapping-description" style={{ marginTop: 8, display: "flex", gap: 16 }}>
                    </div>
                    <div className="mapping-description" style={{ marginTop: 6, display: "flex", gap: 16 }}>
                    </div>
                  </div>
                  <div className="mapping-grid final-grid" style={{ marginTop: 2 }}>
                    {renderRoleField(
                      "date",
                      dateColumn,
                      setDateColumn,
                      "Date column"
                    )}
                    {renderRoleField(
                      "sales",
                      salesColumn,
                      setSalesColumn,
                      "Sales column"
                    )}
                  </div>
                </div>

                <div className="mapping-block" style={{ marginBottom: 24 }}>
                  <div className="mapping-block-header" style={{ marginBottom: 10 }}>
                    <h4>Section B: Product (Recommended for product-level forecasting)</h4>
                    <div className="mapping-description" style={{ marginTop: 6, display: "flex", gap: 12 }}>
                    </div>
                    <p className="mapping-helper" style={{ marginTop: 6 }}>
                    </p>
                  </div>
                  <div className="mapping-grid final-grid" style={{ marginTop: 12 }}>
                    {renderRoleField(
                      "product",
                      productColumn,
                      setProductColumn,
                      "Product ID / SKU"
                    )}
                    {renderRoleField(
                      "productName",
                      dataProductNameColumn,
                      setDataProductNameColumn,
                      "Product Name"
                    )}
                    {renderRoleField(
                      "productCategory",
                      dataProductCategoryColumn,
                      setDataProductCategoryColumn,
                      "Category"
                    )}
                  </div>
                </div>

                <div className="mapping-block" style={{ marginBottom: 24 }}>
                  <div className="mapping-block-header" style={{ marginBottom: 12 }}>
                    <h4>Section C: Location Details (Optional – for location-based forecasting)</h4>
                    <p className="mapping-helper" style={{ marginTop: 6 }}>
                    </p>
                  </div>
                  <div className="mapping-grid final-grid" style={{ marginTop: 12, gap: 12 }}>
                    {renderRoleField(
                      "storeId",
                      storeColumn,
                      setStoreColumn,
                      "Store ID"
                    )}
                    {renderRoleField(
                      "store",
                      dataStoreNameColumn,
                      setDataStoreNameColumn,
                      "Store Name"
                    )}
                  </div>
                  <div
                    className="location-detail-panel"
                    style={{
                      marginTop: 24,
                      padding: 12,
                      marginLeft: 0,
                      marginRight: 0,
                      display: "flex",
                      flexDirection: "column",
                      gap: 8,
                      fontWeight: 600,
                      color: "#1f2937",
                      border: "1px solid #e2e8f0",
                      borderRadius: 12,
                      background: "#fff",
                    }}
                  >
                    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                      <p style={{ margin: 0 }}>Geographic Details</p>
                      <small
                        className="mapping-helper"
                        style={{ marginTop: 0, display: "block", lineHeight: 1.4 }}
                      >
                      </small>
                    </div>
                    <div
                      className="location-detail-grid"
                      style={{
                        marginTop: 12,
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
                        gap: "10px 16px",
                      }}
                    >
                      {columns.map((column) => (
                        <label
                          key={`location-column-${column}`}
                          className="location-detail-entry"
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: 6,
                            padding: "6px 8px",
                            borderRadius: 6,
                            border: "1px solid rgba(0,0,0,0.08)",
                            background: "#fff",
                          }}
                        >
                          <input
                            type="checkbox"
                            checked={selectedLocationColumns.includes(column)}
                            onChange={() => toggleLocationColumn(column)}
                          />
                          <span>{column}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="mapping-block" style={{ marginBottom: 16 }}>
                  <div className="mapping-block-header" style={{ marginBottom: 8 }}>
                    <h4>Section D: Additional Features (Optional)</h4>
                    <p className="mapping-helper" style={{ marginTop: 6 }}>
                      Select additional columns that may influence demand:
                    </p>
                    <p className="mapping-helper" style={{ marginTop: 4 }}>
                    </p>
                    <p className="mapping-helper" style={{ marginTop: 8, fontWeight: 600 }}>
                    </p>
                    {recommendedImportantColumns.length ? (
                      <div className="mapping-helper" style={{ marginTop: 2, display: "flex", gap: 12 }}>
                        {recommendedImportantColumns.map((column) => (
                          <span key={`recommended-${column}`}>{column}</span>
                        ))}
                      </div>
                    ) : (
                      <p className="mapping-helper" style={{ marginTop: 2 }}>None flagged</p>
                    )}
                    <p className="mapping-helper" style={{ marginTop: 4 }}>
                      These features help improve forecast accuracy by capturing external factors like pricing and promotions.
                    </p>
                  </div>
                  {additionalColumns.length ? (
                    <div
                      className="additional-checkbox-grid"
                      style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
                        gap: 12,
                      }}
                    >
                      {additionalColumns.map((column) => {
                        const normalized = normalizeColumnName(column);
                        const isImportant = IMPORTANT_ADDITIONAL_KEYWORDS.some((keyword) =>
                          normalized.includes(keyword)
                        );
                        return (
                          <label
                            key={`additional-${column}`}
                            className="mapping-column additional-checkbox"
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: 8,
                              padding: "8px 12px",
                            }}
                          >
                            <input
                              type="checkbox"
                              checked={selectedAdditionalFeatures.includes(column)}
                              onChange={() => toggleAdditionalFeature(column)}
                            />
                            <span style={{ flex: 1 }}>{column}</span>
                            {isImportant ? (
                              <small className="mapping-helper">Preferred</small>
                            ) : null}
                          </label>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="mapping-empty">No additional columns available.</p>
                  )}
                </div>

                <button
                  type="button"
                  className="confirm-mapping demand-cta"
                  onClick={handleConfirmMapping}
                  disabled={!columns.length || isValidating}
                >
                  {isValidating ? "Validating your data..." : "Confirm Mapping"}
                </button>
              </section>
            )}

            <section className="forecast-section preview-section">
              <div className="preview-header-row">
                <div>
                  <h3>Data preview</h3>
                  <p className="forecast-section-subtitle">
                    Preview the rows fed into the model. Use this view to double-check formatting before continuing.
                  </p>
                </div>
                <div className="preview-header-right">
                  <div className="preview-meta">
                    <span>{previewRows.length} sample rows</span>
                    <span>{columns.length} detected columns</span>
                    {cleanedRows.length ? (
                      <span>{cleanedRows.length} cleaned rows ready</span>
                    ) : null}
                  </div>
                  <button
                    type="button"
                    className="preview-toggle"
                    onClick={togglePreview}
                    aria-expanded={previewExpanded}
                  >
                  {previewExpanded ? "▲" : "▼"}
                  </button>
                </div>
              </div>
              <div className={`preview-table ${previewExpanded ? "expanded" : "collapsed"}`}>
                {previewExpanded && (
                  columns.length ? (
                    <div className="preview-table-scroll">
                      <div className="preview-table-row preview-table-header">
                        {columns.map((column) => (
                          <span key={`header-${column}`}>{column}</span>
                        ))}
                      </div>
                      {previewRows.length ? (
                        previewRows.map((row, rowIndex) => (
                          <div className="preview-table-row" key={`row-${rowIndex}`}>
                            {columns.map((column) => (
                              <span key={`${rowIndex}-${column}`}>
                                {row[column] || "—"}
                              </span>
                            ))}
                          </div>
                        ))
                      ) : (
                        <div className="preview-table-empty">
                          Upload a CSV to see the first rows, then confirm the mapping above.
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="preview-table-empty">
                      Start by uploading a CSV to unlock the preview.
                    </div>
                  )
                )}
              </div>
            </section>
          </>
        )}
            {hasParsedData && (
              <>
                <section className="forecast-section dual-demand-intelligence" data-step="demand">
                  <div className="dual-demand-header">
                    <h3>Demand Intelligence Engine</h3>
                    <p>
                      Automatically analyzes product demand patterns to reveal stability, risk, and data quality.
                    </p>
                  </div>
                    <div className="demand-intelligence-body">
                      <div className="demand-pattern-wrapper">
                        {productDemandAnalysis.totalGroups ? (
                          renderDemandList(
                            productDemandAnalysis,
                            (type) => handleViewDemandType(type, "product")
                          )
                        ) : (
                          <p className="demand-summary-empty">
                            Confirm the mapping and clean the data to run product demand classification.
                          </p>
                        )}
                      </div>
                      <div className="demand-intelligence-actions">
                        <button
                          type="button"
                          className="demand-intelligence-cta"
                          onClick={handleExportDemandIntelligence}
                          disabled={!productDemandAnalysis.totalGroups}
                        >
                          Export Demand Insights
                        </button>
                      </div>
                    </div>
                </section>
                {dataSummary && (
                  <section className="forecast-section config-section" data-step="config">
                    <div className="forecast-section-header">
                      <div>
                        <h3>Forecast Configuration</h3>
                        <p className="forecast-section-subtitle">
                          Adjust forecast duration, level, and time grouping.
                        </p>
                      </div>
                    </div>
                    <div className="forecast-config-note" style={{ marginBottom: 16 }}>
                      <p className="mapping-helper" style={{ marginTop: 0 }}>
                        {maxForecastDays
                          ? `Based on available data, you can forecast up to ${maxForecastDays} days (${availableDataDays} days of history).`
                          : "Clean the uploaded data to reveal how much horizon you can forecast."}
                      </p>
                      <div className="mapping-helper mapping-helper-list" style={{ marginTop: 4 }}>
                        {TIME_GROUPING_REQUIREMENTS.map((line) => (
                          <span key={line}>{line}</span>
                        ))}
                      </div>
                    </div>
                    <div className="config-grid">
                      <label className="config-field">
                        <span>Forecast Level</span>
                        <select
                          value={forecastLevel}
                          onChange={(event) => setForecastLevel(event.target.value as ForecastLevel)}
                        >
                          {FORECAST_LEVEL_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                        <small className="mapping-helper">
                          {FORECAST_LEVEL_OPTIONS.find((option) => option.value === forecastLevel)
                            ?.description}
                        </small>
                      </label>
                      <label className="config-field">
                        <span>Forecast Duration</span>
                        <select
                          value={
                            visibleForecastDurations.length ? forecastDurationDays.toString() : ""
                          }
                          onChange={(event) => setForecastDurationDays(Number(event.target.value))}
                          disabled={!visibleForecastDurations.length}
                        >
                          {visibleForecastDurations.length ? (
                            visibleForecastDurations.map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))
                          ) : (
                            <option value="">Clean the data to unlock durations</option>
                          )}
                        </select>
                        {forecastDurationHelperText && (
                          <small className="mapping-helper">{forecastDurationHelperText}</small>
                        )}
                      </label>
                      <label className="config-field">
                        <span>Time Grouping</span>
                        <select
                          value={forecastGranularity}
                          onChange={(event) => setForecastGranularity(event.target.value)}
                          disabled={!availableTimeGroupingOptions.length}
                        >
                          {availableTimeGroupingOptions.length ? (
                            availableTimeGroupingOptions.map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))
                          ) : (
                            <option value="">Add more history to unlock options</option>
                          )}
                        </select>
                        {timeGroupingHelperText && (
                          <small className="mapping-helper" style={{ marginTop: 4 }}>
                            {timeGroupingHelperText}
                          </small>
                        )}
                      </label>

                      {(forecastLevel === "product" || forecastLevel === "combined") && (
                        <>
                          {productCategoryOptions.length > 0 && (
                            <label className="config-field">
                              <span>Category Filter</span>
                              <select
                                value={selectedCategory}
                                onChange={(event) => {
                                  setSelectedCategory(event.target.value);
                                  setSelectedProductKey("");
                                }}
                              >
                                <option value="">All Categories</option>
                                {productCategoryOptions.map((cat) => (
                                  <option key={cat} value={cat}>
                                    {cat}
                                  </option>
                                ))}
                              </select>
                            </label>
                          )}
                          <label className="config-field">
                            <span>Select Product (Name & ID)</span>
                            <select
                              value={selectedProductKey}
                              onChange={(event) => setSelectedProductKey(event.target.value)}
                            >
                              <option value="">{selectedCategory ? `All ${selectedCategory} Products` : "All Products"}</option>
                              {productOptions.map((option) => (
                                <option key={option.key} value={option.key}>
                                  {option.label}
                                </option>
                              ))}
                            </select>
                            <small className="mapping-helper">
                              Target specific inventory for higher accuracy
                            </small>
                          </label>
                        </>
                      )}
                    </div>
                    <div className="forecast-config-actions">
                      <button
                        type="button"
                        className={`config-toggle ${forecastRequested ? "active" : ""}`}
                        onClick={handleGenerateForecast}
                      >
                        {forecastRequested ? "Regenerate Forecast" : "Generate Forecast"}
                      </button>
                    </div>
                  </section>
                )}

                            </>
                          )}
                        </div>

            {overallForecastSection && (
              <div ref={resultsRef} className="forecast-results-container animate-fade-in" style={{ marginTop: 60, borderTop: "2px solid #e2e8f0", paddingTop: 40, paddingBottom: 60 }}>
                  <div className="forecast-results-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32 }}>
                    <h2 style={{ fontSize: "1.85rem", fontWeight: 800, color: "#0f172a", letterSpacing: "-0.02em" }}>Intelligence Analysis Dashboard</h2>
                    <button 
                      className="demand-cta" 
                      style={{ 
                        width: "fit-content", 
                        padding: "12px 28px", 
                        background: "linear-gradient(135deg, #4f46e5 0%, #3730a3 100%)", 
                        borderRadius: 14,
                        boxShadow: "0 10px 15px -3px rgba(79, 70, 229, 0.4)",
                        border: "none",
                        color: "white",
                        fontWeight: 600,
                        cursor: "pointer"
                      }} 
                      onClick={() => {
                        window.scrollTo({ top: 0, behavior: "smooth" });
                        setTimeout(() => {
                          setOverallForecastSection(null);
                          setHasParsedData(false);
                          setDataSummary(null);
                          setUploadedFileName("");
                          setPreviewRows([]);
                          setColumns([]);
                          setCleanedRows([]);
                          setStatusMessage("");
                          setHasSavedForecast(false);
                        }, 400);
                      }}
                    >
                      🚀 Create New Forecast
                    </button>
                  </div>
                  <ForecastOutput
                    section={overallForecastSection}
                    forecastLevel={forecastLevel}
                    productCategoryOptions={productCategoryOptions}
                    productOptions={productOptions}
                    selectedCategory={selectedCategory}
                    selectedProductKey={selectedProductKey}
                    onCategoryChange={(v) => { setSelectedCategory(v); setSelectedProductKey(""); }}
                    onProductChange={setSelectedProductKey}
                    locationFieldConfig={locationFieldConfig}
                    locationOptionsByField={locationOptionsByField}
                    locationSelections={locationSelections}
                    onLocationChange={updateLocationSelection}
                  />
              </div>
            )}
          </div>
      </main>

      {validationModal && (
        <div className="demand-modal-backdrop">
          <div className="demand-modal">
              <button
                type="button"
                className="demand-modal-close"
                onClick={() => setValidationModal(null)}
                aria-label="Close validation modal"
              >
                ×
              </button>
            <h3>{validationModal.title}</h3>
            <p className="demand-modal-description">{validationModal.message}</p>
            {validationModal.bullets.length ? (
              <div className="demand-modal-flow">
                {validationModal.bullets.map((bullet) => (
                  <span key={bullet}>• {bullet}</span>
                ))}
              </div>
            ) : null}
          </div>
        </div>
      )}
      {demandInsightModal && (
        <div className="demand-modal-backdrop">
          <div className="demand-modal">
            <button
              type="button"
              className="demand-modal-close"
              onClick={() => setDemandInsightModal(null)}
              aria-label="Close demand insight modal"
            >
              ×
            </button>
            <h3>{demandInsightModal.title}</h3>
            <div className="demand-modal-flow">
              {demandInsightModal.list.length ? (
                demandInsightModal.list.map((item, index) => (
                  <span key={`${item}-${index}`}>• {item}</span>
                ))
              ) : (
                <span>No entries available for this demand bucket.</span>
              )}
              {demandInsightModal.more ? (
                <span>{demandInsightModal.more}</span>
              ) : null}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default CreateForecast;

// anything
