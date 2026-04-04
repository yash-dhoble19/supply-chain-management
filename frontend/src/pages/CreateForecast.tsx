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

export function CreateForecast({ activePage, onNavigate }: CreateForecastProps) {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const lastUpdated = new Date();
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [columns, setColumns] = useState<string[]>([]);
  const [previewRows, setPreviewRows] = useState<Record<string, string>[]>([]);
  const [rawRows, setRawRows] = useState<CsvRow[]>([]);
  const [cleanedRows, setCleanedRows] = useState<CsvRow[]>([]);
  const [dateColumn, setDateColumn] = useState("");
  const [salesColumn, setSalesColumn] = useState("");
  const [productColumn, setProductColumn] = useState("");
  const [storeColumn, setStoreColumn] = useState("");
  const [priceColumn, setPriceColumn] = useState("");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [fileSizeLabel, setFileSizeLabel] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const buildCurrentMapping = (): DataMapping => ({
    dateColumn,
    salesColumn,
    productColumn,
    storeColumn,
    priceColumn,
  });

  const rebuildCleanedRows = () => {
    if (!columns.length || !rawRows.length) {
      return;
    }

    setCleanedRows(cleanForecastData(rawRows, columns, buildCurrentMapping()));
  };

  const handleConfirmMapping = () => {
    rebuildCleanedRows();
    setStatusMessage("Column mapping confirmed. Cleaned data is ready for forecasting.");
  };

  const clearUploadedFile = () => {
    setUploadedFileName(null);
    setFileSizeLabel(null);
    setColumns([]);
    setPreviewRows([]);
    setRawRows([]);
    setCleanedRows([]);
    setStatusMessage(null);
    setDateColumn("");
    setSalesColumn("");
    setProductColumn("");
    setStoreColumn("");
    setPriceColumn("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleDropzoneClick = (event: MouseEvent<HTMLLabelElement>) => {
    if (uploadedFileName) {
      event.preventDefault();
    }
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

      const cleaned = cleanForecastData(parsed.rawRows, parsed.headers, detectedMapping);

      setColumns(parsed.headers);
      setPreviewRows(parsed.previewRows);
      setRawRows(parsed.rawRows);
      setCleanedRows(cleaned);
      setDateColumn(detectedDateColumn);
      setSalesColumn(detectedSalesColumn);
      setProductColumn(detectedProductColumn);
      setStoreColumn(detectedStoreColumn);
      setPriceColumn(detectedPriceColumn);
      setUploadedFileName(file.name);
      setFileSizeLabel(formatFileSize(file.size));
      setStatusMessage(
        "Parsed and cleaned the uploaded data. Please confirm column mapping below."
      );
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
          title="📈 Generate New Forecast"
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
          <div className="demand-hero">
            <div className="demand-hero-icon">
              <span className="demand-hero-icon-inner">📈</span>
            </div>
            <div>
              <p className="demand-welcome">Upload historical inputs</p>
              <h2>Step into forecast creation</h2>
              <p>Drop your CSV and let ChainMind guide you through column mapping and validation.</p>
              <p className="demand-steps-title">Workflow overview:</p>
              <ol className="demand-steps">
                <li>Upload historical data</li>
                <li>Map date, sales, product, store, and price columns</li>
                <li>Preview before running AI models</li>
              </ol>
            </div>
          </div>

          <div className="forecast-workspace">
            <section className="forecast-section">
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
                disabled={!columns.length}
              >
                Confirm Mapping
              </button>
            </section>

            <section className="forecast-section">
              <div className="forecast-section-header">
                <div>
                  <h3>Data preview</h3>
                </div>
                <div className="preview-meta">
                  <span>{previewRows.length} sample rows</span>
                  <span>{columns.length} detected columns</span>
                  {cleanedRows.length ? (
                    <span>{cleanedRows.length} cleaned rows ready</span>
                  ) : null}
                </div>
              </div>
              <p className="forecast-section-subtitle">
                Preview the rows fed into the model. Use this view to double-check formatting before continuing.
              </p>
              <div className="preview-table">
                {columns.length ? (
                  <>
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
                  </>
                ) : (
                  <div className="preview-table-empty">
                    Start by uploading a CSV to unlock the preview.
                  </div>
                )}
              </div>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}

export default CreateForecast;
