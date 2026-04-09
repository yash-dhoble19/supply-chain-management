import sys

with open('src/pages/CreateForecast.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. REMOVE the useEffect entirely
old_use_effect = """  useEffect(() => {
    if (!lastConfirmedData) {
      setOverallForecastSection(null);
      return;
    }
    const { cleaned, mapping } = lastConfirmedData;
    if (!mapping.dateColumn || !mapping.salesColumn || !cleaned.length) {
      setOverallForecastSection(null);
      return;
    }

    const dates = [];
    const sales = [];
    cleaned.forEach((row) => {
      const dateVal = row[mapping.dateColumn];
      const salesVal = parseFloat(row[mapping.salesColumn] || '');
      if (dateVal && !isNaN(salesVal)) {
        dates.push(String(dateVal).slice(0, 10));
        sales.push(salesVal);
      }
    });

    if (dates.length < 2) {
      setOverallForecastSection(null);
      return;
    }

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
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "success") {
          setOverallForecastSection(data);
        } else {
          setOverallForecastSection(null);
        }
      })
      .catch((err) => {
        console.error("Prophet backend error:", err);
        setOverallForecastSection(null);
      });
  }, [forecastDurationDays, forecastGranularity, lastConfirmedData]);"""


# 2. UPDATE handleGenerateForecast 
old_handle = """  const handleGenerateForecast = () => {
    setForecastRequested(true);
  };"""

new_handle = """  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerateForecast = () => {
    setForecastRequested(true);
    
    if (!lastConfirmedData) {
      setOverallForecastSection(null);
      return;
    }
    const { cleaned, mapping } = lastConfirmedData;
    if (!mapping.dateColumn || !mapping.salesColumn || !cleaned.length) {
      setOverallForecastSection(null);
      return;
    }

    const dates = [];
    const sales = [];
    cleaned.forEach((row) => {
      const dateVal = row[mapping.dateColumn];
      const salesVal = parseFloat(row[mapping.salesColumn] || '');
      if (dateVal && !isNaN(salesVal)) {
        dates.push(String(dateVal).slice(0, 10));
        sales.push(salesVal);
      }
    });

    if (dates.length < 2) {
      setOverallForecastSection(null);
      return;
    }

    setIsGenerating(true);
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
      .then((res) => res.json())
      .then((data) => {
        setIsGenerating(false);
        if (data.status === "success") {
          setOverallForecastSection(data);
          setStatusMessage("Prophet forecast generated successfully.");
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
  };"""

def norm(text): 
    return text.replace('\r\n', '\n')

if norm(old_use_effect) in norm(c) and norm(old_handle) in norm(c):
    c = norm(c).replace(norm(old_use_effect), "")
    c = c.replace(norm(old_handle), norm(new_handle))
    with open('src/pages/CreateForecast.tsx', 'w', encoding='utf-8', newline='\n') as f:
        f.write(c)
    print('SUCCESS')
else:
    print('FAILED TO FIND OLD CODE')
    if norm(old_use_effect) not in norm(c):
        print("Missing old_use_effect")
    if norm(old_handle) not in norm(c):
        print("Missing old_handle")
