import { useState, useRef } from "react";
import type { ChangeEvent, MouseEvent } from "react";
import { Header } from "../components/layout/Header";
import { Sidebar } from "../components/layout/Sidebar";
import type { AppPage } from "../types/app.types";
import * as XLSX from "xlsx";

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
  priceColumn: string;
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
}

interface ProductMappingState {
  fileName: string | null;
  headers: string[];
  rows: CsvRow[];
  status: string | null;
  idColumn: string;
  nameColumn: string;
  fileSize: string | null;
}

interface StoreMappingState {
  fileName: string | null;
  headers: string[];
  rows: CsvRow[];
  status: string | null;
  storeIdColumn: string;
  cityColumn: string;
  stateColumn: string;
  countryColumn: string;
  fileSize: string | null;
}

const initialProductMapping: ProductMappingState = {
  fileName: null,
  headers: [],
  rows: [],
  status: null,
  idColumn: "",
  nameColumn: "",
  fileSize: null,
};

const initialStoreMapping: StoreMappingState = {
  fileName: null,
  headers: [],
  rows: [],
  status: null,
  storeIdColumn: "",
  cityColumn: "",
  stateColumn: "",
  countryColumn: "",
  fileSize: null,
};

const detectProductColumns = (headers: string[]) => ({
  idColumn: pickColumn(headers, ["product_id", "id", "sku", "product"]),
  nameColumn: pickColumn(headers, ["product_name", "name", "title", "label"]),
});

const detectStoreColumns = (headers: string[]) => ({
  storeIdColumn: pickColumn(headers, ["store_id", "store", "id", "branch"]),
  cityColumn: pickColumn(headers, ["city", "town", "district", "metro"]),
  stateColumn: pickColumn(headers, ["state", "region", "province", "state/region"]),
  countryColumn: pickColumn(headers, ["country", "nation", "country_name"]),
});

const readMappingFile = (
  file: File,
  onCsv: (content: string) => void,
  onError: (message: string) => void
) => {
  const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
  const reader = new FileReader();

  reader.onerror = () => {
    onError("Unable to read the selected file.");
  };

  if (extension === "xlsx" || extension === "xls") {
    reader.onload = () => {
      const arrayBuffer = reader.result;
      if (!(arrayBuffer instanceof ArrayBuffer)) {
        onError("Unable to parse the spreadsheet.");
        return;
      }

      try {
        const workbook = XLSX.read(arrayBuffer, { type: "array" });
        if (!workbook.SheetNames.length) {
          onError("Spreadsheet does not contain any sheets.");
          return;
        }

        const csv = XLSX.utils.sheet_to_csv(workbook.Sheets[workbook.SheetNames[0]]);
        onCsv(csv);
      } catch {
        onError("Failed to convert the spreadsheet to CSV.");
      }
    };
    reader.readAsArrayBuffer(file);
    return;
  }

  reader.onload = () => {
    const content = reader.result;
    if (typeof content !== "string") {
      onError("Unable to read the selected file.");
      return;
    }

    onCsv(content);
  };
  reader.readAsText(file);
};

const processMappingFile = (
  file: File,
  onParsed: (headers: string[], rows: CsvRow[]) => void,
  onError: (message: string) => void
) => {
  readMappingFile(
    file,
    (csvContent) => {
      const parsed = parseCsvPreview(csvContent);
      if (!parsed || !parsed.headers.length) {
        onError("Unable to find tabular data inside the file.");
        return;
      }

      onParsed(parsed.headers, parsed.rawRows);
    },
    onError
  );
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
  const headers = parsed[0].map((value, index) =>
    value ? value : `Column ${index + 1}`
  );

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

const cleanForecastData = (
  rows: CsvRow[],
  columns: string[],
  mapping: DataMapping
): CsvRow[] => {
  const seen = new Set<string>();
  const cleaned: CsvRow[] = [];

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

    if (mapping.dateColumn && normalized[mapping.dateColumn]) {
      const parsedDate = new Date(normalized[mapping.dateColumn]);
      if (!Number.isNaN(parsedDate.getTime())) {
        normalized[mapping.dateColumn] = parsedDate.toISOString().split("T")[0];
      }
    }

    if (mapping.productColumn && !normalized[mapping.productColumn]) {
      normalized[mapping.productColumn] = "Unknown Product";
    }

    if (mapping.storeColumn && !normalized[mapping.storeColumn]) {
      normalized[mapping.storeColumn] = "Unknown Store";
    }

    if (mapping.priceColumn && !normalized[mapping.priceColumn]) {
      normalized[mapping.priceColumn] = "0";
    }

    const rowKey = columns.map((column) => normalized[column]).join("|");
    if (seen.has(rowKey)) {
      return;
    }

    seen.add(rowKey);
    cleaned.push(normalized);
  });

  return cleaned;
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

const pickColumn = (headers: string[], keywords: string[]) => {
  const normalized = headers.map((column) => column.toLowerCase());

  for (const keyword of keywords) {
    const matchIndex = normalized.findIndex((value) => value.includes(keyword));
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
  const [priceColumn, setPriceColumn] = useState("");
  const [isValidating, setIsValidating] = useState(false);
  const [validationModal, setValidationModal] = useState<ValidationModalInfo | null>(null);
  const [dataSummary, setDataSummary] = useState<DataSummary | null>(null);
  const [previewExpanded, setPreviewExpanded] = useState(false);
  const [productMapping, setProductMapping] = useState<ProductMappingState>(
    initialProductMapping
  );
  const [storeMapping, setStoreMapping] = useState<StoreMappingState>(initialStoreMapping);
  const [mappingErrors, setMappingErrors] = useState<string[] | null>(null);
  const [mappingSuccess, setMappingSuccess] = useState<string | null>(null);
  const [showSuccessToast, setShowSuccessToast] = useState(false);
  const [enhanceConfirmed, setEnhanceConfirmed] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [fileSizeLabel, setFileSizeLabel] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const togglePreview = () => {
    setPreviewExpanded((prev) => !prev);
  };

  const previewRows = rawRows.slice(0, 5);
  const hasParsedData = Boolean(columns.length && rawRows.length);

const buildCurrentMapping = (): DataMapping => ({
  dateColumn,
  salesColumn,
  productColumn,
  storeColumn,
  priceColumn,
});

const clearUploadedFile = () => {
    setUploadedFileName(null);
    setFileSizeLabel(null);
    setColumns([]);
    // previewRows derived from rawRows, no need to reset separately
    setRawRows([]);
    setCleanedRows([]);
    setStatusMessage(null);
    setDateColumn("");
    setSalesColumn("");
    setProductColumn("");
    setStoreColumn("");
    setPriceColumn("");
    setIsValidating(false);
    setValidationModal(null);
    setDataSummary(null);
    setPreviewExpanded(false);
    setMappingSuccess(null);
    setEnhanceConfirmed(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleDropzoneClick = (event: MouseEvent<HTMLLabelElement>) => {
    if (uploadedFileName) {
      event.preventDefault();
    }
  };

  const handleConfirmMapping = () => {
    if (!columns.length || !rawRows.length) {
      setStatusMessage("Upload a dataset before confirming the mapping.");
      return;
    }

    const mapping = buildCurrentMapping();
    setIsValidating(true);
    setValidationModal(null);
    setDataSummary(null);
    setPreviewExpanded(false);
    setStatusMessage("Validating your data...");
    setCleanedRows([]);

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
          title: "Required data not found",
          message: "Please map valid:",
          bullets: missingFields,
        });
        setStatusMessage("Required columns are missing.");
        setIsValidating(false);
        return;
      }

      const invalidSales = !isNumericColumn(rawRows, mapping.salesColumn);
      const invalidDate = !isDateColumn(rawRows, mapping.dateColumn);

      if (invalidSales || invalidDate) {
        setValidationModal({
          title: "Invalid column selection",
          message: "Please ensure:",
          bullets: [
            "Sales column contains numeric values",
            "Date column contains valid dates",
          ],
        });
        setStatusMessage("Invalid column selection detected.");
        setIsValidating(false);
        return;
      }

      const cleaned = cleanForecastData(rawRows, columns, mapping);
      if (cleaned.length < 30) {
        setValidationModal({
          title: "Insufficient data",
          message: "At least 30 records are required to generate a forecast.",
          bullets: [],
        });
        setStatusMessage("Insufficient data after cleaning.");
        setIsValidating(false);
        return;
      }

      const productMetric = buildProductMetric(cleaned, columns, mapping);
      const storeMetric = buildStoreMetric(cleaned, columns, mapping);

      setCleanedRows(cleaned);
      setDataSummary({
        fileName: uploadedFileName ?? "Uploaded file",
        rows: cleaned.length,
        columns: columns.length,
        duplicatesRemoved: Math.max(0, rawRows.length - cleaned.length),
        status: "Ready for forecasting",
        ...(productMetric ? { productMetric } : {}),
        ...(storeMetric ? { storeMetric } : {}),
      });
      setPreviewExpanded(false);
      setStatusMessage("Data cleaned successfully. Ready for forecasting.");
      setIsValidating(false);
    };

    setTimeout(runValidation, 400);
  };

  const triggerSuccessMessage = (message: string) => {
    setMappingErrors(null);
    setMappingSuccess(message);
    setShowSuccessToast(true);
    setEnhanceConfirmed(true);
  };

  const handleConfirmMappingDetails = () => {
    triggerSuccessMessage("Now generate your forecast — all ready with input.");
  };

  const handleSkipMapping = () => {
    triggerSuccessMessage("Optional data skipped — ready for forecasting.");
  };

  const closeSuccessToast = () => {
    setShowSuccessToast(false);
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      clearUploadedFile();
      return;
    }

    const extension = file.name.split(".").pop()?.toLowerCase() ?? "";

    const processCsv = (content: string) => {
      const parsed = parseCsvPreview(content, 6);
      if (!parsed) {
        setStatusMessage("The file looks empty. Upload a CSV with headers and rows.");
        return;
      }

      const detectedDateColumn = pickColumn(parsed.headers, [
        "date",
        "month",
        "day",
        "time",
        "period",
      ]);
      const detectedSalesColumn = pickColumn(parsed.headers, [
        "sales",
        "units",
        "quantity",
        "qty",
        "volume",
        "demand",
        "revenue",
        "amount",
      ]);
      const detectedProductColumn = pickColumn(parsed.headers, [
        "product",
        "item",
        "sku",
        "category",
        "name",
      ]);
      const detectedStoreColumn = pickColumn(parsed.headers, [
        "store",
        "location",
        "branch",
        "outlet",
      ]);
      const detectedPriceColumn = pickColumn(parsed.headers, [
        "price",
        "cost",
        "unit price",
        "rate",
        "value",
      ]);

      const detectedMapping: DataMapping = {
        dateColumn: detectedDateColumn,
        salesColumn: detectedSalesColumn,
        productColumn: detectedProductColumn,
        storeColumn: detectedStoreColumn,
        priceColumn: detectedPriceColumn,
      };

      setColumns(parsed.headers);
      setRawRows(parsed.rawRows);
      setDateColumn(detectedDateColumn);
      setSalesColumn(detectedSalesColumn);
      setProductColumn(detectedProductColumn);
      setStoreColumn(detectedStoreColumn);
      setPriceColumn(detectedPriceColumn);
      setUploadedFileName(file.name);
      setFileSizeLabel(formatFileSize(file.size));
      setCleanedRows([]);
      setDataSummary(null);
      setValidationModal(null);
      setStatusMessage("Parsed the uploaded data. Please confirm column mapping below.");
    };

    const reader = new FileReader();
    reader.onerror = () => {
      setStatusMessage("Unable to read the selected file.");
    };

    if (extension === "xlsx" || extension === "xls") {
      reader.onload = () => {
        const arrayBuffer = reader.result;
        if (!(arrayBuffer instanceof ArrayBuffer)) {
          setStatusMessage("Unable to parse the spreadsheet.");
          return;
        }

        try {
          const workbook = XLSX.read(arrayBuffer, { type: "array" });
          if (!workbook.SheetNames.length) {
            setStatusMessage("Spreadsheet does not contain any sheets.");
            return;
          }

          const csv = XLSX.utils.sheet_to_csv(workbook.Sheets[workbook.SheetNames[0]]);
          processCsv(csv);
        } catch {
          setStatusMessage("Failed to convert the spreadsheet to CSV.");
        }
      };
      reader.readAsArrayBuffer(file);
      return;
    }

    reader.onload = () => {
      const content = reader.result;
      if (typeof content !== "string") {
        setStatusMessage("Unable to read the selected file.");
        return;
      }

      processCsv(content);
    };
    reader.readAsText(file);
  };

  const handleProductMappingChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      setProductMapping(initialProductMapping);
      return;
    }

    const fileSizeLabel = formatFileSize(file.size);

    setProductMapping({
      ...initialProductMapping,
      fileName: file.name,
      fileSize: fileSizeLabel,
      status: "Parsing product data...",
    });

    processMappingFile(
      file,
      (headers, rows) => {
        const detection = detectProductColumns(headers);
        setProductMapping({
          fileName: file.name,
          fileSize: fileSizeLabel,
          headers,
          rows,
          status: "Columns detected",
          idColumn: detection.idColumn,
          nameColumn: detection.nameColumn,
        });
        setMappingErrors(null);
        setMappingSuccess(null);
        setEnhanceConfirmed(false);
      },
      (message) => {
        setProductMapping({
          fileName: file.name,
          fileSize: fileSizeLabel,
          headers: [],
          rows: [],
          status: message,
          idColumn: "",
          nameColumn: "",
        });
      }
    );
  };

  const handleStoreMappingChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      setStoreMapping(initialStoreMapping);
      return;
    }

    const fileSizeLabel = formatFileSize(file.size);

    setStoreMapping({
      ...initialStoreMapping,
      fileName: file.name,
      fileSize: fileSizeLabel,
      status: "Parsing store data...",
    });

    processMappingFile(
      file,
      (headers, rows) => {
        const detection = detectStoreColumns(headers);
        setStoreMapping({
          fileName: file.name,
          fileSize: fileSizeLabel,
          headers,
          rows,
          status: "Columns detected",
          storeIdColumn: detection.storeIdColumn,
          cityColumn: detection.cityColumn,
          stateColumn: detection.stateColumn,
          countryColumn: detection.countryColumn,
        });
        setMappingErrors(null);
        setMappingSuccess(null);
        setEnhanceConfirmed(false);
      },
      (message) => {
        setStoreMapping({
          fileName: file.name,
          fileSize: fileSizeLabel,
          headers: [],
          rows: [],
          status: message,
          storeIdColumn: "",
          cityColumn: "",
          stateColumn: "",
          countryColumn: "",
        });
      }
    );
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
        <div className="demand-content">
          <div className="forecast-workspace">
            <section className="forecast-section upload-section">
              <div className="forecast-section-header">
                <div>
                  <h3>Upload &amp; Inspect</h3>
                </div>
              </div>
              <p className="forecast-section-subtitle">
                Drag or select your historical CSV/XLSX. We look for date, sales, product, store, and price columns.
              </p>
              <label
                className={`upload-dropzone ${uploadedFileName ? "has-file" : ""}`}
                htmlFor="forecast-upload"
                onClick={handleDropzoneClick}
              >
                <input
                  id="forecast-upload"
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={handleFileChange}
                  disabled={Boolean(uploadedFileName)}
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
                  ) : (
                    <>
                      <p>Drop CSV file here</p>
                      <p>Or browse files on your system</p>
                      <p className="upload-secondary">[Supported formats: CSV (Recommended), Excel (.xlsx, .xls)]</p>
                      <p className="upload-secondary">[Max file size: 50MB]</p>
                    </>
                  )}
                </div>
              </label>
              {statusMessage ? <p className="status-text">{statusMessage}</p> : null}
            </section>

            {dataSummary ? (
              <section className="forecast-section data-summary-card">
                <div className="data-summary-title">
                  <h3>Data summary</h3>
                  <p>Cleaned dataset ready for forecasting</p>
                </div>
                <div className="summary-grid">
                  <div>
                    <p>File</p>
                    <strong>{dataSummary.fileName}</strong>
                  </div>
                  <div>
                    <p>Rows</p>
                    <strong>{formatNumber(dataSummary.rows)}</strong>
                  </div>
                  <div>
                    <p>Columns</p>
                    <strong>{formatNumber(dataSummary.columns)}</strong>
                  </div>
                  <div>
                    <p>Duplicates removed</p>
                    <strong>{formatNumber(dataSummary.duplicatesRemoved)}</strong>
                  </div>
                </div>
                <div className="summary-checks">
                  <span>✔ Data cleaned successfully</span>
                  <span>✔ Duplicates removed</span>
                </div>
                {(dataSummary.productMetric || dataSummary.storeMetric) ? (
                  <div className="summary-extra">
                    {dataSummary.productMetric ? (
                      <span>{dataSummary.productMetric.text}</span>
                    ) : null}
                    {dataSummary.storeMetric ? (
                      <span>{dataSummary.storeMetric.text}</span>
                    ) : null}
                  </div>
                ) : null}
                <p className="summary-status">Status: {dataSummary.status}</p>
              </section>
            ) : null}

            {!dataSummary && (
              <section className="forecast-section">
                <div className="forecast-section-header">
                  <div>
                    <h3>Column Mapping</h3>
                  </div>
                  <span className="status-pill status-pill-secondary">Auto-detected</span>
                </div>
                <p className="mapping-description">
                  System have auto-detected columns. You can adjust them if needed.
                </p>
                <div className="mapping-grid">
                  <label className="mapping-column">
                    <span>Date column</span>
                    <select
                      value={dateColumn}
                      onChange={(event) => setDateColumn(event.target.value)}
                      disabled={!columns.length}
                    >
                      <option value="">Not Available</option>
                      {columns.map((column) => (
                        <option key={`date-${column}`} value={column}>
                          {column}
                        </option>
                      ))}
                    </select>
                    <small className="mapping-detected">
                      Detected: {dateColumn || "Not Available"}
                    </small>
                  </label>

                  <label className="mapping-column">
                    <span>Sales column</span>
                    <select
                      value={salesColumn}
                      onChange={(event) => setSalesColumn(event.target.value)}
                      disabled={!columns.length}
                    >
                      <option value="">Not Available</option>
                      {columns.map((column) => (
                        <option key={`sales-${column}`} value={column}>
                          {column}
                        </option>
                      ))}
                    </select>
                    <small className="mapping-detected">
                      Detected: {salesColumn || "Not Available"}
                    </small>
                  </label>

                  <label className="mapping-column">
                    <span>Product column</span>
                    <select
                      value={productColumn}
                      onChange={(event) => setProductColumn(event.target.value)}
                      disabled={!columns.length}
                    >
                      <option value="">Not Available</option>
                      {columns.map((column) => (
                        <option key={`product-${column}`} value={column}>
                          {column}
                        </option>
                      ))}
                    </select>
                    <small className="mapping-detected">
                      Detected: {productColumn || "Not Available"}
                    </small>
                  </label>

                  <label className="mapping-column">
                    <span>Store column</span>
                    <select
                      value={storeColumn}
                      onChange={(event) => setStoreColumn(event.target.value)}
                      disabled={!columns.length}
                    >
                      <option value="">Not Available</option>
                      {columns.map((column) => (
                        <option key={`store-${column}`} value={column}>
                          {column}
                        </option>
                      ))}
                    </select>
                    <small className="mapping-detected">
                      Detected: {storeColumn || "Not Available"}
                    </small>
                  </label>

                  <label className="mapping-column">
                    <span>Price column</span>
                    <select
                      value={priceColumn}
                      onChange={(event) => setPriceColumn(event.target.value)}
                      disabled={!columns.length}
                    >
                      <option value="">Not Available</option>
                      {columns.map((column) => (
                        <option key={`price-${column}`} value={column}>
                          {column}
                        </option>
                      ))}
                    </select>
                    <small className="mapping-detected">
                      Detected: {priceColumn || "Not Available"}
                    </small>
                  </label>
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
            {hasParsedData ? (
              enhanceConfirmed ? (
                <section className="forecast-section dual-demand-intelligence">
                  <div className="dual-demand-header">
                    <h3>Dual Demand Intelligence</h3>
                    <p>
                      Understand how demand behaves across your products and locations to make smarter forecasting decisions.
                    </p>
                  </div>
                  <div className="dual-demand-grid">
                    <div className="demand-box demand-box-product">
                      <h4>Product Demand Analysis</h4>
                      <p>Track SKU-level demand signals to surface top performers and risk areas.</p>
                    </div>
                    <div className="demand-box demand-box-store">
                      <h4>Store / Location Demand Analysis</h4>
                      <p>Compare performance across stores, regions, and countries to reveal coverage gaps.</p>
                    </div>
                  </div>
                </section>
              ) : (
                <section className="forecast-section mapping-section">
                  <div className="forecast-section-header">
                    <div>
                      <h3>Enhance Your Forecast (Optional)</h3>
                      <p className="forecast-section-subtitle">
                        Add additional data for better insights.
                      </p>
                    </div>
                  </div>

                  <div className="mapping-item">
                    <div className="mapping-side-left">
                      <h4 className="mapping-title">1. Upload Product Details</h4>
                      <p className="mapping-subtitle">Enable product-level forecasting.</p>
                      <div className="mapping-upload">
                        <label className="upload-pill" htmlFor="product-mapping">
                          Browse Data
                        </label>
                        <input
                          id="product-mapping"
                          type="file"
                          accept=".csv,.xlsx,.xls"
                          onChange={handleProductMappingChange}
                        />
                      </div>
                      <p className="mapping-supported">[Supported formats: CSV (Recommended), Excel (.xlsx, .xls)],[Max file size: 50MB]</p>
                      {productMapping.fileName ? (
                        <p className="mapping-hint">
                          Uploaded: {productMapping.fileName}
                          {productMapping.fileSize ? ` (${productMapping.fileSize})` : ""}
                        </p>
                      ) : null}
                    </div>
                    <div className="mapping-side-right">
                      {productMapping.headers.length ? (
                        <>
                          <h4>Column Mapping</h4>
                          <div className="mapping-grid">
                            <label className="mapping-column">
                              <span>Product ID</span>
                              <select
                                value={productMapping.idColumn}
                                onChange={(event) =>
                                  setProductMapping((prev) => ({
                                    ...prev,
                                    idColumn: event.target.value,
                                  }))
                                }
                              >
                                <option value="">Not Available</option>
                                {productMapping.headers.map((header) => (
                                  <option key={`prod-id-${header}`} value={header}>
                                    {header}
                                  </option>
                                ))}
                              </select>
                              <small className="mapping-detected">
                                Detected: {productMapping.idColumn || "Not Available"}
                              </small>
                            </label>
                            <label className="mapping-column">
                              <span>Product Name</span>
                              <select
                                value={productMapping.nameColumn}
                                onChange={(event) =>
                                  setProductMapping((prev) => ({
                                    ...prev,
                                    nameColumn: event.target.value,
                                  }))
                                }
                              >
                                <option value="">Not Available</option>
                                {productMapping.headers.map((header) => (
                                  <option key={`prod-name-${header}`} value={header}>
                                    {header}
                                  </option>
                                ))}
                              </select>
                              <small className="mapping-detected">
                                Detected: {productMapping.nameColumn || "Not Available"}
                              </small>
                            </label>
                          </div>
                          {productMapping.status ? (
                            <p className="mapping-hint">{productMapping.status}</p>
                          ) : null}
                        </>
                      ) : (
                        <p className="mapping-empty">Upload a file to configure product columns.</p>
                      )}
                    </div>
                  </div>

                  <div className="mapping-item">
                    <div className="mapping-side-left">
                      <h4 className="mapping-title">2. Upload Store Details</h4>
                      <p className="mapping-subtitle">Add location context to forecasts.</p>
                      <div className="mapping-upload">
                        <label className="upload-pill" htmlFor="store-mapping">
                          Browse Data
                        </label>
                        <input
                          id="store-mapping"
                          type="file"
                          accept=".csv,.xlsx,.xls"
                          onChange={handleStoreMappingChange}
                        />
                      </div>
                      <p className="mapping-supported">[Supported formats: CSV (Recommended), Excel (.xlsx, .xls)],[Max file size: 50MB]</p>
                      {storeMapping.fileName ? (
                        <p className="mapping-hint">
                          Uploaded: {storeMapping.fileName}
                          {storeMapping.fileSize ? ` (${storeMapping.fileSize})` : ""}
                        </p>
                      ) : null}
                    </div>
                    <div className="mapping-side-right">
                      {storeMapping.headers.length ? (
                        <>
                          <h4>Column Mapping</h4>
                          <div className="mapping-grid">
                            <label className="mapping-column">
                              <span>Store ID</span>
                              <select
                                value={storeMapping.storeIdColumn}
                                onChange={(event) =>
                                  setStoreMapping((prev) => ({
                                    ...prev,
                                    storeIdColumn: event.target.value,
                                  }))
                                }
                              >
                                <option value="">Not Available</option>
                                {storeMapping.headers.map((header) => (
                                  <option key={`store-id-${header}`} value={header}>
                                    {header}
                                  </option>
                                ))}
                              </select>
                              <small className="mapping-detected">
                                Detected: {storeMapping.storeIdColumn || "Not Available"}
                              </small>
                            </label>
                            <label className="mapping-column">
                              <span>City</span>
                              <select
                                value={storeMapping.cityColumn}
                                onChange={(event) =>
                                  setStoreMapping((prev) => ({
                                    ...prev,
                                    cityColumn: event.target.value,
                                  }))
                                }
                              >
                                <option value="">Not Available</option>
                                {storeMapping.headers.map((header) => (
                                  <option key={`store-city-${header}`} value={header}>
                                    {header}
                                  </option>
                                ))}
                              </select>
                              <small className="mapping-detected">
                                Detected: {storeMapping.cityColumn || "Not Available"}
                              </small>
                            </label>
                            <label className="mapping-column">
                              <span>State/Region</span>
                              <select
                                value={storeMapping.stateColumn}
                                onChange={(event) =>
                                  setStoreMapping((prev) => ({
                                    ...prev,
                                    stateColumn: event.target.value,
                                  }))
                                }
                              >
                                <option value="">Not Available</option>
                                {storeMapping.headers.map((header) => (
                                  <option key={`store-state-${header}`} value={header}>
                                    {header}
                                  </option>
                                ))}
                              </select>
                              <small className="mapping-detected">
                                Detected: {storeMapping.stateColumn || "Not Available"}
                              </small>
                            </label>
                            <label className="mapping-column">
                              <span>Country</span>
                              <select
                                value={storeMapping.countryColumn}
                                onChange={(event) =>
                                  setStoreMapping((prev) => ({
                                    ...prev,
                                    countryColumn: event.target.value,
                                  }))
                                }
                              >
                                <option value="">Not Available</option>
                                {storeMapping.headers.map((header) => (
                                  <option key={`store-country-${header}`} value={header}>
                                    {header}
                                  </option>
                                ))}
                              </select>
                              <small className="mapping-detected">
                                Detected: {storeMapping.countryColumn || "Not Available"}
                              </small>
                            </label>
                          </div>
                          <p className="mapping-status">
                            Required: store_id, city, state/region, country
                          </p>
                          {storeMapping.status ? (
                            <p className="mapping-hint">{storeMapping.status}</p>
                          ) : null}
                        </>
                      ) : (
                        <p className="mapping-empty">Upload a file to configure store columns.</p>
                      )}
                    </div>
                  </div>

                  {mappingErrors ? (
                    <div className="mapping-alert">
                      <ul>
                        {mappingErrors.map((error) => (
                          <li key={error}>• {error}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}

                  {mappingSuccess ? (
                    <p className="mapping-success">{mappingSuccess}</p>
                  ) : null}

                  <div className="mapping-actions">
                    <button
                      type="button"
                      className="mapping-skip"
                      onClick={handleSkipMapping}
                    >
                      Skip
                    </button>
                    <button
                      type="button"
                      className="confirm-mapping demand-cta"
                      onClick={handleConfirmMappingDetails}
                      disabled={!productMapping.fileName && !storeMapping.fileName}
                    >
                      Confirm Mapping
                    </button>
                  </div>
                </section>
              )
            ) : null}
          </div>
        </div>
      </main>

      {mappingSuccess && showSuccessToast && (
        <div className="mapping-success-popup">
          <div className="mapping-success-popup-card">
            <span className="mapping-success-icon" aria-hidden="true">
              ✓
            </span>
            <p>{mappingSuccess}</p>
            <button type="button" onClick={closeSuccessToast}>
              Close
            </button>
          </div>
        </div>
      )}

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
    </div>
  );
}

export default CreateForecast;
