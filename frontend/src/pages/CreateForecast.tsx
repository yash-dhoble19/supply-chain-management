import { useState, useRef } from "react";
import type { ChangeEvent, MouseEvent } from "react";
import { Header } from "../components/layout/Header";
import { Sidebar } from "../components/layout/Sidebar";
import type { AppPage } from "../types/app.types";
import * as XLSX from "xlsx";

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

const parseCsvPreview = (text: string, rowLimit = 5) => {
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

  const rows = parsed.slice(1, 1 + rowLimit).map((cells) => {
    const row: Record<string, string> = {};
    headers.forEach((header, index) => {
      row[header] = cells[index] ?? "";
    });
    return row;
  });

  return { headers, rows };
};

const pickColumn = (headers: string[], keywords: string[]) => {
  const normalized = headers.map((column) => column.toLowerCase());

  for (const keyword of keywords) {
    const matchIndex = normalized.findIndex((value) => value.includes(keyword));
    if (matchIndex !== -1) {
      return headers[matchIndex];
    }
  }

  return headers[0] ?? "";
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
  const [dateColumn, setDateColumn] = useState("");
  const [categoryColumn, setCategoryColumn] = useState("");
  const [unitsColumn, setUnitsColumn] = useState("");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [fileSizeLabel, setFileSizeLabel] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const clearUploadedFile = () => {
    setUploadedFileName(null);
    setFileSizeLabel(null);
    setColumns([]);
    setPreviewRows([]);
    setStatusMessage(null);
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

      setColumns(parsed.headers);
      setPreviewRows(parsed.rows);
      setDateColumn(pickColumn(parsed.headers, ["date", "month", "day", "time", "period"]));
      setCategoryColumn(pickColumn(parsed.headers, ["category", "product", "item", "segment", "name"]));
      setUnitsColumn(pickColumn(parsed.headers, ["units", "quantity", "qty", "sales", "volume", "demand"]));
      setUploadedFileName(file.name);
      setFileSizeLabel(formatFileSize(file.size));
      setStatusMessage("Parsed file successfully. Please confirm column mapping before previewing.");
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
                <li>Map date, product, and units columns</li>
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
                Drag or select your historical CSV. We look for date, product/category, and unit columns.
              </p>
              <label
                className={`upload-dropzone ${uploadedFileName ? "has-file" : ""}`}
                htmlFor="forecast-upload"
                onClick={handleDropzoneClick}
              >
                <input
                  id="forecast-upload"
                  type="file"
                  accept=".csv"
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
                      <p className="upload-secondary">[Supported formats: CSV (Recommended), XLSX]</p>
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
              <p className="forecast-section-subtitle">
                Confirm the headers that correspond to dates, product categories, and shipped units.
              </p>
              <div className="mapping-grid">
                <label className="mapping-column">
                  <span>Date column</span>
                  <select
                    value={dateColumn}
                    onChange={(event) => setDateColumn(event.target.value)}
                    disabled={!columns.length}
                  >
                    <option value="">Select column</option>
                    {columns.map((column) => (
                      <option key={column} value={column}>
                        {column}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="mapping-column">
                  <span>Category column</span>
                  <select
                    value={categoryColumn}
                    onChange={(event) => setCategoryColumn(event.target.value)}
                    disabled={!columns.length}
                  >
                    <option value="">Select column</option>
                    {columns.map((column) => (
                      <option key={column} value={column}>
                        {column}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="mapping-column">
                  <span>Units column</span>
                  <select
                    value={unitsColumn}
                    onChange={(event) => setUnitsColumn(event.target.value)}
                    disabled={!columns.length}
                  >
                    <option value="">Select column</option>
                    {columns.map((column) => (
                      <option key={column} value={column}>
                        {column}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            </section>

            <section className="forecast-section">
              <div className="forecast-section-header">
                <div>
                  <h3>Data preview</h3>
                </div>
                <div className="preview-meta">
                  <span>{previewRows.length} sample rows</span>
                  <span>{columns.length} detected columns</span>
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
