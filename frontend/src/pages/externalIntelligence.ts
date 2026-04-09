/**
 * externalIntelligence.ts
 *
 * External Intelligence Layer for Demand Forecasting.
 * Provides weather and trend signals to enhance forecast explainability.
 *
 * Usage:
 *   const insights = await generateInsights(productName, category, forecastDates);
 *   // insights: string[] - store internally, surface in explainable-insights UI later
 */

// ---------------------------------------------------------------------------
// SECTION 1: CONSTANTS
// ---------------------------------------------------------------------------

/** Month indices (0-based) mapped to meteorological seasons */
const SEASON_MAP: Record<number, "summer" | "monsoon" | "winter" | "spring"> = {
  0: "winter",
  1: "winter",
  2: "spring",
  3: "spring",
  4: "summer",
  5: "summer",
  6: "monsoon",
  7: "monsoon",
  8: "monsoon",
  9: "spring",
  10: "winter",
  11: "winter",
};

/** Product keyword groups - matched via case-insensitive substring */
const PRODUCT_WEATHER_MAP = {
  rain: [
    "umbrella", "raincoat", "rain jacket", "waterproof", "rain boot",
    "poncho", "rain gear", "gumboot", "mackintosh", "windcheater",
  ],
  summer: [
    "ac", "air conditioner", "air conditioning", "cooler", "fan",
    "sunscreen", "sunblock", "spf", "cooling", "refrigerator", "fridge",
    "summer dress", "shorts", "tank top", "swimwear",
  ],
  winter: [
    "heater", "room heater", "blanket", "quilt", "jacket", "coat",
    "sweater", "hoodie", "thermal", "gloves", "muffler", "scarf",
    "woollen", "fleece", "down jacket",
  ],
} as const;

type WeatherCategory = keyof typeof PRODUCT_WEATHER_MAP;

/** Category-level trend baseline */
const CATEGORY_TREND_BASELINE: Record<string, "increasing" | "stable" | "decreasing" | "volatile"> = {
  electronics: "stable",
  mobile: "increasing",
  smartphone: "increasing",
  laptop: "stable",
  appliance: "stable",
  fashion: "volatile",
  apparel: "volatile",
  clothing: "volatile",
  grocery: "stable",
  food: "stable",
  beverage: "stable",
  fmcg: "stable",
  beauty: "increasing",
  skincare: "increasing",
  personal_care: "stable",
  health: "increasing",
  wellness: "increasing",
  fitness: "increasing",
  furniture: "stable",
  home: "stable",
  decor: "stable",
  sports: "increasing",
  outdoor: "stable",
  toys: "volatile",
  books: "decreasing",
  automotive: "stable",
  travel: "increasing",
};

// ---------------------------------------------------------------------------
// SECTION 2: TYPE DEFINITIONS
// ---------------------------------------------------------------------------

interface WeatherAPIResponse {
  temperature: number;
  rain: boolean;
  rainProbability: number;
  condition: "sunny" | "cloudy" | "rainy" | "stormy";
  season: "summer" | "monsoon" | "winter" | "spring";
}

interface TrendAPIResponse {
  direction: "increasing" | "stable" | "decreasing";
  score: number;
  momentum: "accelerating" | "steady" | "slowing";
}

// ---------------------------------------------------------------------------
// SECTION 3: HELPERS
// ---------------------------------------------------------------------------

const normalize = (text: string) => text.toLowerCase().trim();

const matchesKeywords = (productName: string, keywords: readonly string[]): boolean => {
  const normalizedProduct = normalize(productName);
  return keywords.some((keyword) => normalizedProduct.includes(normalize(keyword)));
};

const detectWeatherCategory = (productName: string): WeatherCategory | null => {
  for (const [category, keywords] of Object.entries(PRODUCT_WEATHER_MAP)) {
    if (matchesKeywords(productName, keywords)) {
      return category as WeatherCategory;
    }
  }
  return null;
};

const detectDominantSeason = (forecastDates: string[]): "summer" | "monsoon" | "winter" | "spring" => {
  if (!forecastDates.length) return "spring";
  const counts: Record<string, number> = {};
  forecastDates.forEach((dateStr) => {
    const month = new Date(dateStr).getMonth();
    const season = SEASON_MAP[month] ?? "spring";
    counts[season] = (counts[season] ?? 0) + 1;
  });
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])[0][0] as ReturnType<typeof detectDominantSeason>;
};

const resolveCategoryTrend = (category: string): TrendAPIResponse["direction"] | "volatile" => {
  const normalizedCategory = normalize(category);
  for (const [key, trend] of Object.entries(CATEGORY_TREND_BASELINE)) {
    if (normalizedCategory.includes(key)) return trend;
  }
  return "stable";
};

// ---------------------------------------------------------------------------
// SECTION 4: SIMULATED API CALLS (Primary - replace with real SDK calls)
// ---------------------------------------------------------------------------

const fetchWeatherAPI = async (forecastDates: string[]): Promise<WeatherAPIResponse | null> => {
  try {
    // -- REAL INTEGRATION POINT ------------------------------------------------
    // const res = await fetch(`https://api.weather.com/...`);
    // const data = await res.json();
    // return parseOpenWeatherResponse(data);
    // --------------------------------------------------------------------------

    const season = detectDominantSeason(forecastDates);
    const isRainySeason = season === "monsoon";

    const simulatedResponse: WeatherAPIResponse = {
      temperature: season === "summer" ? 36 : season === "winter" ? 14 : season === "monsoon" ? 28 : 24,
      rain: isRainySeason,
      rainProbability: isRainySeason ? 0.72 : 0.18,
      condition: isRainySeason ? "rainy" : season === "summer" ? "sunny" : "cloudy",
      season,
    };

    return simulatedResponse;
  } catch {
    return null;
  }
};

const fetchTrendAPI = async (
  productName: string,
  category: string,
): Promise<TrendAPIResponse | null> => {
  try {
    // -- REAL INTEGRATION POINT ------------------------------------------------
    // const res = await fetch(`https://trends.example.com/api?q=${encodeURIComponent(productName)}`);
    // const data = await res.json();
    // return parseTrendResponse(data);
    // --------------------------------------------------------------------------

    const categoryTrend = resolveCategoryTrend(category);
    const normalizedProduct = normalize(productName);
    const isNewProduct = normalizedProduct.includes("new") || normalizedProduct.includes("launch");

    const simulatedResponse: TrendAPIResponse = {
      direction: isNewProduct
        ? "increasing"
        : categoryTrend === "volatile"
        ? "stable"
        : categoryTrend,
      score: categoryTrend === "increasing" ? 72 : categoryTrend === "decreasing" ? 35 : 55,
      momentum: isNewProduct ? "accelerating" : "steady",
    };

    return simulatedResponse;
  } catch {
    return null;
  }
};

// ---------------------------------------------------------------------------
// SECTION 5: FALLBACK LOGIC
// ---------------------------------------------------------------------------

const buildWeatherFallback = (forecastDates: string[]): WeatherAPIResponse => {
  const season = detectDominantSeason(forecastDates);
  return {
    temperature: season === "summer" ? 34 : season === "winter" ? 15 : 26,
    rain: season === "monsoon",
    rainProbability: season === "monsoon" ? 0.65 : 0.15,
    condition: season === "monsoon" ? "rainy" : season === "summer" ? "sunny" : "cloudy",
    season,
  };
};

const buildTrendFallback = (category: string): TrendAPIResponse => {
  const direction = resolveCategoryTrend(category);
  return {
    direction: direction === "volatile" ? "stable" : direction,
    score: 50,
    momentum: "steady",
  };
};

// ---------------------------------------------------------------------------
// SECTION 6: INSIGHT BUILDERS
// ---------------------------------------------------------------------------

const buildWeatherInsights = (
  productName: string,
  weather: WeatherAPIResponse,
): string[] => {
  const insights: string[] = [];
  const weatherCategory = detectWeatherCategory(productName);

  insights.push("Weather signals integrated into demand analysis.");

  if (!weatherCategory) {
    insights.push("Product demand shows low dependency on weather conditions.");
    return insights;
  }

  const { season, rain, rainProbability, temperature } = weather;

  if (weatherCategory === "rain") {
    if (rain || rainProbability >= 0.5) {
      insights.push(
        `Rainy conditions expected (${Math.round(rainProbability * 100)}% probability) -> increased demand likely for rain-related products.`,
      );
    } else {
      insights.push(
        "Dry weather conditions forecast -> moderate demand expected for rain-related products.",
      );
    }
  }

  if (weatherCategory === "summer") {
    if (temperature >= 32 || season === "summer") {
      insights.push(
        `High temperatures detected (approx. ${temperature} degrees C) -> elevated demand expected for cooling products.`,
      );
    } else {
      insights.push(
        "Mild temperatures forecast -> reduced peak demand for summer/cooling products.",
      );
    }
  }

  if (weatherCategory === "winter") {
    if (temperature <= 18 || season === "winter") {
      insights.push(
        `Cold weather conditions detected (approx. ${temperature} degrees C) -> strong demand signals for winter products.`,
      );
    } else {
      insights.push(
        "Warmer-than-expected conditions forecast -> softened demand for winter products.",
      );
    }
  }

  return insights;
};

const buildTrendInsights = (
  productName: string,
  category: string,
  trend: TrendAPIResponse,
): string[] => {
  const insights: string[] = [];
  const categoryTrend = resolveCategoryTrend(category);
  const isVolatile = categoryTrend === "volatile";

  const directionLabel =
    trend.direction === "increasing"
      ? "increasing demand"
      : trend.direction === "decreasing"
      ? "declining demand"
      : "stable demand pattern";

  insights.push(`Market trend analysis indicates ${directionLabel}.`);

  if (trend.momentum === "accelerating" && trend.direction === "increasing") {
    insights.push("Trend momentum is accelerating - demand may exceed baseline projections.");
  }

  if (isVolatile) {
    insights.push(
      `${category || "Product"} category shows historically volatile trends - forecast confidence adjusted accordingly.`,
    );
  }

  if (trend.score >= 70) {
    insights.push("Elevated market interest detected - high search and purchase intent signals.");
  } else if (trend.score <= 30) {
    insights.push("Below-average market interest - conservative demand estimates applied.");
  }

  return insights;
};

const buildFestivalInsights = (forecastDates: string[]): string[] => {
  return [
    forecastDates.length > 0
      ? "Festival and seasonal event effects have been incorporated into the forecast."
      : "No festival adjustments applied - forecast window is empty.",
  ];
};

// ---------------------------------------------------------------------------
// SECTION 7: MAIN EXPORT
// ---------------------------------------------------------------------------

export const generateInsights = async (
  productName: string,
  category: string,
  forecastDates: string[],
): Promise<string[]> => {
  const allInsights: string[] = [];

  const weatherData =
    (await fetchWeatherAPI(forecastDates)) ?? buildWeatherFallback(forecastDates);
  const weatherInsights = buildWeatherInsights(productName, weatherData);
  allInsights.push(...weatherInsights);

  const trendData =
    (await fetchTrendAPI(productName, category)) ?? buildTrendFallback(category);
  const trendInsights = buildTrendInsights(productName, category, trendData);
  allInsights.push(...trendInsights);

  const festivalInsights = buildFestivalInsights(forecastDates);
  allInsights.push(...festivalInsights);

  return allInsights;
};

// ---------------------------------------------------------------------------
// SECTION 8: TYPES RE-EXPORT (for consumers)
// ---------------------------------------------------------------------------
export type { WeatherAPIResponse, TrendAPIResponse };
