const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, 'src', 'pages', 'CreateForecast.tsx');
let content = fs.readFileSync(filePath, 'utf8');

const oldCode = `  useEffect(() => {
    if (!lastConfirmedData) {
      setOverallForecastSection(null);
      return;
    }
    const section = generateSmartForecast(
      lastConfirmedData.cleaned,
      {
        dateColumn: lastConfirmedData.mapping.dateColumn,
        salesColumn: lastConfirmedData.mapping.salesColumn,
      },
      { windowSize: 7, forecastDurationDays },
      lastConfirmedData.mapping,
    );
    setOverallForecastSection(section);
  }, [forecastDurationDays, lastConfirmedData]);`;

const newCode = `  useEffect(() => {
    if (!lastConfirmedData) {
      setOverallForecastSection(null);
      return;
    }

    const { cleaned, mapping } = lastConfirmedData;
    if (!mapping.dateColumn || !mapping.salesColumn || !cleaned.length) {
      setOverallForecastSection(null);
      return;
    }

    // Build date + sales arrays from cleaned rows
    const dates: string[] = [];
    const sales: number[] = [];
    cleaned.forEach((row) => {
      const dateVal = row[mapping.dateColumn];
      const salesVal = parseFloat(row[mapping.salesColumn]);
      if (dateVal && !isNaN(salesVal)) {
        dates.push(String(dateVal).slice(0, 10));
        sales.push(salesVal);
      }
    });

    if (dates.length < 2) {
      setOverallForecastSection(null);
      return;
    }

    // Call backend Prophet endpoint
    const apiBase = (import.meta as any).env?.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
    setStatusMessage("Running Prophet model on backend...");

    fetch(\`\${apiBase}/forecast/predict\`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        dates,
        sales,
        forecastDays: forecastDurationDays,
        timeGrouping: forecastGranularity,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "success") {
          setOverallForecastSection(data as ForecastSection);
          setStatusMessage("Prophet forecast generated successfully.");
        } else {
          setStatusMessage(data.detail || data.message || "Forecast failed.");
          setOverallForecastSection(null);
        }
      })
      .catch((err) => {
        console.error("Prophet backend error:", err);
        setStatusMessage(\`Backend error: \${err.message}. Ensure backend is running.\`);
        setOverallForecastSection(null);
      });
  }, [forecastDurationDays, forecastGranularity, lastConfirmedData]);`;

// Normalize line endings for matching
const normalizedContent = content.replace(/\r\n/g, '\n');
const normalizedOld = oldCode.replace(/\r\n/g, '\n');

if (normalizedContent.includes(normalizedOld)) {
  // Replace in the normalized version, then restore original line ending style
  const result = normalizedContent.replace(normalizedOld, newCode.replace(/\r\n/g, '\n'));
  // Keep original line ending style (CRLF if original had it)
  const hasCRLF = content.includes('\r\n');
  const finalContent = hasCRLF ? result.replace(/(?<!\r)\n/g, '\r\n') : result;
  fs.writeFileSync(filePath, finalContent, 'utf8');
  console.log('SUCCESS: Replaced generateSmartForecast with backend /forecast/predict call');
} else {
  console.log('ERROR: Could not find the target code block');
  // Try to find partial match
  const lines = normalizedOld.split('\n');
  lines.forEach((line, i) => {
    if (line.trim() && !normalizedContent.includes(line.trim())) {
      console.log(`  Line ${i} NOT found: "${line.trim()}"`);
    }
  });
}
