/**
 * forecastEngine.ts
 *
 * Drop-in enhancement for CreateForecast.tsx.
 *
 * Re-used types (copy from CreateForecast.tsx or import from shared types)
 * ---------------------------------------------------------------------------
 */
type CsvRow = Record<string, string>;
type DemandType = "Smooth" | "Erratic" | "Intermittent" | "Seasonal" | "New";

interface ForecastConfig {
  windowSize: number;
  forecastDurationDays: number;
}

interface DataMapping {
  dateColumn: string;
  salesColumn: string;
  productColumn: string;
  storeColumn: string;
}

// ---------------------------------------------------------------------------
// Legacy ForecastSection shape — kept so nothing in the existing UI breaks
// ---------------------------------------------------------------------------
export interface ForecastSection {
  sectionName: string;
  chart: {
    history: { date: string; value: number }[];
    forecast: { date: string; p10: number; p50: number; p90: number }[];
  };
  metrics: {
    totalForecast: number;
    avgDailyForecast: number;
    minForecast: number;
    maxForecast: number;
  };
  table: {
    date: string;
    forecast: number;
    lowerBound: number;
    upperBound: number;
  }[];
  /** NEW — richer output attached alongside the legacy shape */
  smart: SmartForecastOutput;
}

// ---------------------------------------------------------------------------
// New rich output type (as specified)
// ---------------------------------------------------------------------------
export interface SmartForecastOutput {
  summary: {
    forecastTotal: number;
    avgDailyDemand: number;
    trend: "increasing" | "decreasing" | "stable";
    demandType: DemandType;
    confidence: "High" | "Medium" | "Low";
  };
  model: {
    name: string;
    reason: string;
  };
  historical: { date: string; value: number }[];
  forecast: {
    date: string;
    value: number;
    p10: number;
    p90: number;
    festivalName?: string;
    festivalImpact?: number;
  }[];
  meta: {
    appliedFestivalDays: number;
    dataPointsUsed: number;
  };
}

// ---------------------------------------------------------------------------
// Festival data — embedded from festival_demand_dataset.xlsx
// ---------------------------------------------------------------------------
export interface FestivalEntry {
  date: string;
  name: string;
  country: string;
  region: string | null;
  type: string;
  impact: string;
  baseWeight: number;
  onlineMult: number;
  offlineMult: number;
  preHaloDays: number;
  postHaloDays: number;
}

export const FESTIVAL_DATA: FestivalEntry[] = [
  {
    date: "2024-01-01",
    name: "New Year's Day",
    country: "Global",
    region: null,
    type: "Cultural",
    impact: "Very High",
    baseWeight: 90,
    onlineMult: 2.5,
    offlineMult: 1.8,
    preHaloDays: 7,
    postHaloDays: 2,
  },
  {
    date: "2024-02-14",
    name: "Valentine's Day",
    country: "Global",
    region: null,
    type: "Cultural",
    impact: "High",
    baseWeight: 72,
    onlineMult: 3.2,
    offlineMult: 2.4,
    preHaloDays: 10,
    postHaloDays: 1,
  },
  {
    date: "2024-03-29",
    name: "Good Friday",
    country: "Global",
    region: null,
    type: "Religious",
    impact: "Low",
    baseWeight: 20,
    onlineMult: 0.9,
    offlineMult: 0.6,
    preHaloDays: 2,
    postHaloDays: 0,
  },
  {
    date: "2024-03-31",
    name: "Easter Sunday",
    country: "Global",
    region: null,
    type: "Religious",
    impact: "Medium",
    baseWeight: 45,
    onlineMult: 1.4,
    offlineMult: 1.5,
    preHaloDays: 5,
    postHaloDays: 1,
  },
  {
    date: "2024-05-12",
    name: "Mother's Day",
    country: "Global",
    region: null,
    type: "Cultural",
    impact: "High",
    baseWeight: 68,
    onlineMult: 2.8,
    offlineMult: 2.1,
    preHaloDays: 14,
    postHaloDays: 1,
  },
  {
    date: "2024-06-16",
    name: "Father's Day",
    country: "Global",
    region: null,
    type: "Cultural",
    impact: "Medium",
    baseWeight: 50,
    onlineMult: 2.2,
    offlineMult: 1.7,
    preHaloDays: 10,
    postHaloDays: 1,
  },
  {
    date: "2024-10-31",
    name: "Halloween",
    country: "Global",
    region: null,
    type: "Cultural",
    impact: "Medium",
    baseWeight: 55,
    onlineMult: 2,
    offlineMult: 2.5,
    preHaloDays: 14,
    postHaloDays: 2,
  },
  {
    date: "2024-11-29",
    name: "Black Friday",
    country: "Global",
    region: null,
    type: "Shopping",
    impact: "Very High",
    baseWeight: 100,
    onlineMult: 4.5,
    offlineMult: 3.8,
    preHaloDays: 7,
    postHaloDays: 3,
  },
  {
    date: "2024-12-02",
    name: "Cyber Monday",
    country: "Global",
    region: null,
    type: "Shopping",
    impact: "Very High",
    baseWeight: 95,
    onlineMult: 5,
    offlineMult: 1.2,
    preHaloDays: 2,
    postHaloDays: 2,
  },
  {
    date: "2024-11-11",
    name: "Singles' Day (11.11)",
    country: "Global",
    region: null,
    type: "Shopping",
    impact: "Very High",
    baseWeight: 98,
    onlineMult: 5.5,
    offlineMult: 1.5,
    preHaloDays: 14,
    postHaloDays: 3,
  },
  {
    date: "2024-12-25",
    name: "Christmas Day",
    country: "Global",
    region: null,
    type: "Religious",
    impact: "Very High",
    baseWeight: 97,
    onlineMult: 3.8,
    offlineMult: 4.2,
    preHaloDays: 30,
    postHaloDays: 5,
  },
  {
    date: "2024-12-26",
    name: "Boxing Day",
    country: "Global",
    region: "UK / Australia / Canada",
    type: "Shopping",
    impact: "High",
    baseWeight: 75,
    onlineMult: 3,
    offlineMult: 4,
    preHaloDays: 1,
    postHaloDays: 3,
  },
  {
    date: "2024-12-31",
    name: "New Year's Eve",
    country: "Global",
    region: null,
    type: "Cultural",
    impact: "High",
    baseWeight: 70,
    onlineMult: 2.2,
    offlineMult: 2.8,
    preHaloDays: 5,
    postHaloDays: 1,
  },
  {
    date: "2024-01-15",
    name: "Martin Luther King Jr. Day",
    country: "USA",
    region: null,
    type: "Cultural",
    impact: "Low",
    baseWeight: 18,
    onlineMult: 1.1,
    offlineMult: 1,
    preHaloDays: 1,
    postHaloDays: 0,
  },
  {
    date: "2024-02-19",
    name: "Presidents' Day",
    country: "USA",
    region: null,
    type: "Cultural",
    impact: "Medium",
    baseWeight: 42,
    onlineMult: 1.8,
    offlineMult: 2.2,
    preHaloDays: 3,
    postHaloDays: 1,
  },
  {
    date: "2024-05-27",
    name: "Memorial Day",
    country: "USA",
    region: null,
    type: "Cultural",
    impact: "High",
    baseWeight: 60,
    onlineMult: 2,
    offlineMult: 2.8,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2024-07-04",
    name: "Independence Day",
    country: "USA",
    region: null,
    type: "Cultural",
    impact: "High",
    baseWeight: 65,
    onlineMult: 1.7,
    offlineMult: 3,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2024-09-02",
    name: "Labor Day",
    country: "USA",
    region: null,
    type: "Cultural",
    impact: "High",
    baseWeight: 62,
    onlineMult: 2.1,
    offlineMult: 2.6,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2024-10-14",
    name: "Columbus Day",
    country: "USA",
    region: null,
    type: "Cultural",
    impact: "Low",
    baseWeight: 20,
    onlineMult: 1.3,
    offlineMult: 1.1,
    preHaloDays: 1,
    postHaloDays: 0,
  },
  {
    date: "2024-11-28",
    name: "Thanksgiving",
    country: "USA",
    region: null,
    type: "Cultural",
    impact: "Very High",
    baseWeight: 88,
    onlineMult: 3.5,
    offlineMult: 3.2,
    preHaloDays: 14,
    postHaloDays: 1,
  },
  {
    date: "2024-12-07",
    name: "Hanukkah (Start)",
    country: "USA",
    region: null,
    type: "Religious",
    impact: "Medium",
    baseWeight: 40,
    onlineMult: 1.8,
    offlineMult: 1.4,
    preHaloDays: 3,
    postHaloDays: 0,
  },
  {
    date: "2024-03-10",
    name: "Mother's Day UK",
    country: "UK",
    region: null,
    type: "Cultural",
    impact: "High",
    baseWeight: 65,
    onlineMult: 2.6,
    offlineMult: 2,
    preHaloDays: 10,
    postHaloDays: 1,
  },
  {
    date: "2024-08-26",
    name: "Late Summer Bank Holiday",
    country: "UK",
    region: null,
    type: "Cultural",
    impact: "Low",
    baseWeight: 25,
    onlineMult: 1.2,
    offlineMult: 1.5,
    preHaloDays: 2,
    postHaloDays: 1,
  },
  {
    date: "2024-02-13",
    name: "Carnival / Mardi Gras",
    country: "Europe",
    region: "France / Germany / Italy / Brazil",
    type: "Cultural",
    impact: "Medium",
    baseWeight: 45,
    onlineMult: 1.6,
    offlineMult: 2,
    preHaloDays: 7,
    postHaloDays: 1,
  },
  {
    date: "2024-05-01",
    name: "Labour Day",
    country: "Europe",
    region: null,
    type: "Cultural",
    impact: "Low",
    baseWeight: 22,
    onlineMult: 0.9,
    offlineMult: 0.8,
    preHaloDays: 1,
    postHaloDays: 0,
  },
  {
    date: "2024-12-06",
    name: "St. Nicholas Day",
    country: "Europe",
    region: "Germany / Netherlands / Belgium",
    type: "Cultural",
    impact: "Medium",
    baseWeight: 38,
    onlineMult: 1.5,
    offlineMult: 1.8,
    preHaloDays: 5,
    postHaloDays: 1,
  },
  {
    date: "2024-10-03",
    name: "German Unity Day",
    country: "Germany",
    region: null,
    type: "Cultural",
    impact: "Low",
    baseWeight: 20,
    onlineMult: 1,
    offlineMult: 1.1,
    preHaloDays: 1,
    postHaloDays: 0,
  },
  {
    date: "2024-02-10",
    name: "Chinese New Year (CNY)",
    country: "China",
    region: null,
    type: "Cultural",
    impact: "Very High",
    baseWeight: 96,
    onlineMult: 4.8,
    offlineMult: 4.5,
    preHaloDays: 15,
    postHaloDays: 7,
  },
  {
    date: "2024-06-10",
    name: "Dragon Boat Festival",
    country: "China",
    region: null,
    type: "Cultural",
    impact: "Medium",
    baseWeight: 40,
    onlineMult: 1.5,
    offlineMult: 1.8,
    preHaloDays: 3,
    postHaloDays: 1,
  },
  {
    date: "2024-09-17",
    name: "Mid-Autumn Festival",
    country: "China",
    region: null,
    type: "Cultural",
    impact: "High",
    baseWeight: 70,
    onlineMult: 2.8,
    offlineMult: 3,
    preHaloDays: 7,
    postHaloDays: 2,
  },
  {
    date: "2024-10-01",
    name: "Golden Week (National Day)",
    country: "China",
    region: null,
    type: "Cultural",
    impact: "Very High",
    baseWeight: 92,
    onlineMult: 3.5,
    offlineMult: 4.8,
    preHaloDays: 3,
    postHaloDays: 7,
  },
  {
    date: "2024-11-11",
    name: "Double 11 / Singles' Day",
    country: "China",
    region: null,
    type: "Shopping",
    impact: "Very High",
    baseWeight: 100,
    onlineMult: 6,
    offlineMult: 1.8,
    preHaloDays: 14,
    postHaloDays: 3,
  },
  {
    date: "2024-06-18",
    name: "618 Shopping Festival",
    country: "China",
    region: null,
    type: "Shopping",
    impact: "Very High",
    baseWeight: 88,
    onlineMult: 5.2,
    offlineMult: 1.5,
    preHaloDays: 14,
    postHaloDays: 3,
  },
  {
    date: "2024-01-01",
    name: "Oshogatsu / Japanese New Year",
    country: "Japan",
    region: null,
    type: "Cultural",
    impact: "Very High",
    baseWeight: 91,
    onlineMult: 2,
    offlineMult: 4.5,
    preHaloDays: 7,
    postHaloDays: 3,
  },
  {
    date: "2024-04-29",
    name: "Golden Week Start",
    country: "Japan",
    region: null,
    type: "Cultural",
    impact: "High",
    baseWeight: 72,
    onlineMult: 1.8,
    offlineMult: 3.5,
    preHaloDays: 5,
    postHaloDays: 7,
  },
  {
    date: "2024-12-25",
    name: "Christmas Japan",
    country: "Japan",
    region: null,
    type: "Cultural",
    impact: "High",
    baseWeight: 60,
    onlineMult: 2.5,
    offlineMult: 2.8,
    preHaloDays: 7,
    postHaloDays: 1,
  },
  {
    date: "2024-02-10",
    name: "Seollal (Korean New Year)",
    country: "South Korea",
    region: null,
    type: "Cultural",
    impact: "Very High",
    baseWeight: 90,
    onlineMult: 2.5,
    offlineMult: 4.2,
    preHaloDays: 7,
    postHaloDays: 3,
  },
  {
    date: "2024-09-17",
    name: "Chuseok (Korean Thanksgiving)",
    country: "South Korea",
    region: null,
    type: "Cultural",
    impact: "Very High",
    baseWeight: 92,
    onlineMult: 2.8,
    offlineMult: 4.5,
    preHaloDays: 7,
    postHaloDays: 3,
  },
  {
    date: "2024-11-11",
    name: "Pepero Day",
    country: "South Korea",
    region: null,
    type: "Cultural",
    impact: "Medium",
    baseWeight: 42,
    onlineMult: 2,
    offlineMult: 2.5,
    preHaloDays: 3,
    postHaloDays: 1,
  },
  {
    date: "2024-03-25",
    name: "Ramadan Start",
    country: "Middle East",
    region: null,
    type: "Religious",
    impact: "Very High",
    baseWeight: 93,
    onlineMult: 3.5,
    offlineMult: 3.8,
    preHaloDays: 7,
    postHaloDays: 0,
  },
  {
    date: "2024-04-09",
    name: "Eid ul-Fitr",
    country: "Middle East",
    region: null,
    type: "Religious",
    impact: "Very High",
    baseWeight: 97,
    onlineMult: 4.2,
    offlineMult: 4.5,
    preHaloDays: 7,
    postHaloDays: 5,
  },
  {
    date: "2024-06-17",
    name: "Eid ul-Adha",
    country: "Middle East",
    region: null,
    type: "Religious",
    impact: "Very High",
    baseWeight: 91,
    onlineMult: 3.8,
    offlineMult: 4,
    preHaloDays: 5,
    postHaloDays: 4,
  },
  {
    date: "2024-03-25",
    name: "Holi",
    country: "India",
    region: "National",
    type: "Religious",
    impact: "High",
    baseWeight: 78,
    onlineMult: 2.8,
    offlineMult: 3.5,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2024-10-29",
    name: "Dhanteras",
    country: "India",
    region: "National",
    type: "Religious",
    impact: "Very High",
    baseWeight: 96,
    onlineMult: 4,
    offlineMult: 5,
    preHaloDays: 7,
    postHaloDays: 1,
  },
  {
    date: "2024-10-31",
    name: "Diwali",
    country: "India",
    region: "National",
    type: "Religious",
    impact: "Very High",
    baseWeight: 100,
    onlineMult: 4.8,
    offlineMult: 5.5,
    preHaloDays: 21,
    postHaloDays: 7,
  },
  {
    date: "2024-11-01",
    name: "Govardhan Puja",
    country: "India",
    region: "National",
    type: "Religious",
    impact: "Medium",
    baseWeight: 38,
    onlineMult: 1.2,
    offlineMult: 1.5,
    preHaloDays: 1,
    postHaloDays: 1,
  },
  {
    date: "2024-11-02",
    name: "Bhai Dooj",
    country: "India",
    region: "National",
    type: "Cultural",
    impact: "Medium",
    baseWeight: 45,
    onlineMult: 1.4,
    offlineMult: 1.6,
    preHaloDays: 2,
    postHaloDays: 1,
  },
  {
    date: "2024-08-19",
    name: "Raksha Bandhan",
    country: "India",
    region: "National",
    type: "Cultural",
    impact: "High",
    baseWeight: 74,
    onlineMult: 3,
    offlineMult: 3.2,
    preHaloDays: 10,
    postHaloDays: 2,
  },
  {
    date: "2024-08-26",
    name: "Janmashtami",
    country: "India",
    region: "National",
    type: "Religious",
    impact: "High",
    baseWeight: 60,
    onlineMult: 1.8,
    offlineMult: 2.5,
    preHaloDays: 5,
    postHaloDays: 1,
  },
  {
    date: "2024-09-07",
    name: "Ganesh Chaturthi",
    country: "India",
    region: "Maharashtra / Goa / Karnataka",
    type: "Religious",
    impact: "High",
    baseWeight: 68,
    onlineMult: 2.2,
    offlineMult: 3.5,
    preHaloDays: 7,
    postHaloDays: 5,
  },
  {
    date: "2024-09-29",
    name: "Navratri Begin",
    country: "India",
    region: "Gujarat / Rajasthan / MP",
    type: "Religious",
    impact: "High",
    baseWeight: 70,
    onlineMult: 2.5,
    offlineMult: 3.2,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2024-10-14",
    name: "Dussehra / Vijayadasami",
    country: "India",
    region: "National",
    type: "Religious",
    impact: "High",
    baseWeight: 72,
    onlineMult: 2.6,
    offlineMult: 3,
    preHaloDays: 7,
    postHaloDays: 2,
  },
  {
    date: "2024-10-24",
    name: "Karwa Chauth",
    country: "India",
    region: "North India",
    type: "Cultural",
    impact: "High",
    baseWeight: 65,
    onlineMult: 3.5,
    offlineMult: 2.8,
    preHaloDays: 7,
    postHaloDays: 1,
  },
  {
    date: "2024-11-08",
    name: "Chhath Puja",
    country: "India",
    region: "Bihar / Jharkhand / UP / Delhi",
    type: "Religious",
    impact: "High",
    baseWeight: 62,
    onlineMult: 1.5,
    offlineMult: 2.8,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2024-11-15",
    name: "Guru Nanak Jayanti",
    country: "India",
    region: "Punjab / Haryana / Delhi",
    type: "Religious",
    impact: "Medium",
    baseWeight: 45,
    onlineMult: 1.4,
    offlineMult: 1.8,
    preHaloDays: 3,
    postHaloDays: 1,
  },
  {
    date: "2024-08-15",
    name: "Independence Day",
    country: "India",
    region: "National",
    type: "Cultural",
    impact: "Medium",
    baseWeight: 40,
    onlineMult: 1.8,
    offlineMult: 1.5,
    preHaloDays: 3,
    postHaloDays: 1,
  },
  {
    date: "2024-01-26",
    name: "Republic Day",
    country: "India",
    region: "National",
    type: "Cultural",
    impact: "Low",
    baseWeight: 22,
    onlineMult: 1.3,
    offlineMult: 1.2,
    preHaloDays: 2,
    postHaloDays: 1,
  },
  {
    date: "2024-04-14",
    name: "Ambedkar Jayanti",
    country: "India",
    region: "National",
    type: "Cultural",
    impact: "Low",
    baseWeight: 15,
    onlineMult: 1,
    offlineMult: 1,
    preHaloDays: 0,
    postHaloDays: 0,
  },
  {
    date: "2024-10-02",
    name: "Gandhi Jayanti",
    country: "India",
    region: "National",
    type: "Cultural",
    impact: "Low",
    baseWeight: 12,
    onlineMult: 0.9,
    offlineMult: 0.9,
    preHaloDays: 0,
    postHaloDays: 0,
  },
  {
    date: "2024-01-14",
    name: "Makar Sankranti",
    country: "India",
    region: "Gujarat / Maharashtra / Karnataka",
    type: "Religious",
    impact: "Medium",
    baseWeight: 48,
    onlineMult: 1.5,
    offlineMult: 2.2,
    preHaloDays: 3,
    postHaloDays: 1,
  },
  {
    date: "2024-01-14",
    name: "Pongal",
    country: "India",
    region: "Tamil Nadu",
    type: "Religious",
    impact: "High",
    baseWeight: 70,
    onlineMult: 2,
    offlineMult: 3,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2024-04-06",
    name: "Ugadi",
    country: "India",
    region: "Telangana / Andhra Pradesh / Karnataka",
    type: "Religious",
    impact: "High",
    baseWeight: 68,
    onlineMult: 2.2,
    offlineMult: 2.8,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2024-04-06",
    name: "Gudi Padwa",
    country: "India",
    region: "Maharashtra",
    type: "Religious",
    impact: "High",
    baseWeight: 65,
    onlineMult: 2,
    offlineMult: 2.8,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2024-04-13",
    name: "Baisakhi",
    country: "India",
    region: "Punjab / Haryana",
    type: "Religious",
    impact: "High",
    baseWeight: 68,
    onlineMult: 2,
    offlineMult: 3,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2024-04-14",
    name: "Tamil New Year (Puthandu)",
    country: "India",
    region: "Tamil Nadu",
    type: "Cultural",
    impact: "High",
    baseWeight: 65,
    onlineMult: 2,
    offlineMult: 2.8,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2024-04-14",
    name: "Bihu (Rongali)",
    country: "India",
    region: "Assam",
    type: "Cultural",
    impact: "High",
    baseWeight: 65,
    onlineMult: 1.8,
    offlineMult: 2.8,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2024-09-01",
    name: "Onam",
    country: "India",
    region: "Kerala",
    type: "Cultural",
    impact: "Very High",
    baseWeight: 88,
    onlineMult: 3,
    offlineMult: 4.2,
    preHaloDays: 10,
    postHaloDays: 3,
  },
  {
    date: "2024-10-12",
    name: "Durga Puja",
    country: "India",
    region: "West Bengal / Odisha / Bihar",
    type: "Religious",
    impact: "Very High",
    baseWeight: 92,
    onlineMult: 3.5,
    offlineMult: 5,
    preHaloDays: 10,
    postHaloDays: 5,
  },
  {
    date: "2024-04-17",
    name: "Vishu",
    country: "India",
    region: "Kerala",
    type: "Religious",
    impact: "High",
    baseWeight: 62,
    onlineMult: 2,
    offlineMult: 2.5,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2024-09-06",
    name: "Hartalika Teej",
    country: "India",
    region: "Rajasthan / UP / Bihar / MP",
    type: "Religious",
    impact: "High",
    baseWeight: 58,
    onlineMult: 2.2,
    offlineMult: 2.5,
    preHaloDays: 5,
    postHaloDays: 1,
  },
  {
    date: "2024-11-14",
    name: "Children's Day",
    country: "India",
    region: "National",
    type: "Cultural",
    impact: "Low",
    baseWeight: 28,
    onlineMult: 1.5,
    offlineMult: 1.3,
    preHaloDays: 3,
    postHaloDays: 1,
  },
  {
    date: "2024-10-07",
    name: "Flipkart Big Billion Days",
    country: "India",
    region: null,
    type: "Shopping",
    impact: "Very High",
    baseWeight: 97,
    onlineMult: 5.8,
    offlineMult: 1.2,
    preHaloDays: 7,
    postHaloDays: 3,
  },
  {
    date: "2024-10-07",
    name: "Amazon Great Indian Festival",
    country: "India",
    region: null,
    type: "Shopping",
    impact: "Very High",
    baseWeight: 96,
    onlineMult: 5.5,
    offlineMult: 1.2,
    preHaloDays: 7,
    postHaloDays: 3,
  },
  {
    date: "2024-01-26",
    name: "Australia Day",
    country: "Australia",
    region: null,
    type: "Cultural",
    impact: "Medium",
    baseWeight: 42,
    onlineMult: 1.5,
    offlineMult: 2,
    preHaloDays: 3,
    postHaloDays: 1,
  },
  {
    date: "2024-06-10",
    name: "Queen's Birthday Weekend",
    country: "Australia",
    region: "VIC / SA / WA",
    type: "Cultural",
    impact: "Low",
    baseWeight: 25,
    onlineMult: 1.2,
    offlineMult: 1.5,
    preHaloDays: 2,
    postHaloDays: 1,
  },
  {
    date: "2024-10-14",
    name: "Canadian Thanksgiving",
    country: "Canada",
    region: null,
    type: "Cultural",
    impact: "High",
    baseWeight: 62,
    onlineMult: 2,
    offlineMult: 2.8,
    preHaloDays: 7,
    postHaloDays: 1,
  },
  {
    date: "2024-07-01",
    name: "Canada Day",
    country: "Canada",
    region: null,
    type: "Cultural",
    impact: "Medium",
    baseWeight: 40,
    onlineMult: 1.5,
    offlineMult: 2,
    preHaloDays: 3,
    postHaloDays: 1,
  },
  {
    date: "2024-02-13",
    name: "Carnival Brazil",
    country: "Brazil",
    region: null,
    type: "Cultural",
    impact: "Very High",
    baseWeight: 90,
    onlineMult: 1.5,
    offlineMult: 4.8,
    preHaloDays: 14,
    postHaloDays: 3,
  },
  {
    date: "2024-06-13",
    name: "Festa Junina Start",
    country: "Brazil",
    region: null,
    type: "Cultural",
    impact: "Medium",
    baseWeight: 42,
    onlineMult: 1.3,
    offlineMult: 2,
    preHaloDays: 5,
    postHaloDays: 5,
  },
  {
    date: "2024-11-15",
    name: "Dia da Proclamação",
    country: "Brazil",
    region: null,
    type: "Cultural",
    impact: "Low",
    baseWeight: 18,
    onlineMult: 1,
    offlineMult: 1,
    preHaloDays: 0,
    postHaloDays: 0,
  },
  {
    date: "2024-11-02",
    name: "Dia de los Muertos",
    country: "Mexico",
    region: null,
    type: "Cultural",
    impact: "High",
    baseWeight: 65,
    onlineMult: 1.8,
    offlineMult: 3.5,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2024-09-16",
    name: "Mexican Independence Day",
    country: "Mexico",
    region: null,
    type: "Cultural",
    impact: "Medium",
    baseWeight: 40,
    onlineMult: 1.4,
    offlineMult: 2.2,
    preHaloDays: 3,
    postHaloDays: 1,
  },
  {
    date: "2024-01-07",
    name: "Orthodox Christmas",
    country: "Russia / Eastern Europe",
    region: null,
    type: "Religious",
    impact: "High",
    baseWeight: 68,
    onlineMult: 2,
    offlineMult: 2.8,
    preHaloDays: 7,
    postHaloDays: 2,
  },
  {
    date: "2024-03-08",
    name: "International Women's Day",
    country: "Russia / Eastern Europe",
    region: null,
    type: "Cultural",
    impact: "High",
    baseWeight: 65,
    onlineMult: 3.5,
    offlineMult: 2.5,
    preHaloDays: 5,
    postHaloDays: 1,
  },
  {
    date: "2024-04-09",
    name: "Eid ul-Fitr",
    country: "Pakistan / Bangladesh",
    region: null,
    type: "Religious",
    impact: "Very High",
    baseWeight: 95,
    onlineMult: 3.8,
    offlineMult: 5,
    preHaloDays: 10,
    postHaloDays: 5,
  },
  {
    date: "2024-12-25",
    name: "Christmas",
    country: "Nigeria / Kenya / South Africa",
    region: null,
    type: "Religious",
    impact: "High",
    baseWeight: 70,
    onlineMult: 2.5,
    offlineMult: 3.8,
    preHaloDays: 14,
    postHaloDays: 3,
  },
  {
    date: "2024-04-27",
    name: "Freedom Day",
    country: "South Africa",
    region: null,
    type: "Cultural",
    impact: "Low",
    baseWeight: 20,
    onlineMult: 1.1,
    offlineMult: 1.2,
    preHaloDays: 1,
    postHaloDays: 0,
  },
  // 2025 entries
  {
    date: "2025-01-01",
    name: "New Year's Day",
    country: "Global",
    region: null,
    type: "Cultural",
    impact: "Very High",
    baseWeight: 90,
    onlineMult: 2.5,
    offlineMult: 1.8,
    preHaloDays: 7,
    postHaloDays: 2,
  },
  {
    date: "2025-01-29",
    name: "Chinese New Year (CNY)",
    country: "China",
    region: null,
    type: "Cultural",
    impact: "Very High",
    baseWeight: 96,
    onlineMult: 4.8,
    offlineMult: 4.5,
    preHaloDays: 15,
    postHaloDays: 7,
  },
  {
    date: "2025-01-14",
    name: "Makar Sankranti",
    country: "India",
    region: "Gujarat / Maharashtra / Karnataka",
    type: "Religious",
    impact: "Medium",
    baseWeight: 48,
    onlineMult: 1.5,
    offlineMult: 2.2,
    preHaloDays: 3,
    postHaloDays: 1,
  },
  {
    date: "2025-01-14",
    name: "Pongal",
    country: "India",
    region: "Tamil Nadu",
    type: "Religious",
    impact: "High",
    baseWeight: 70,
    onlineMult: 2,
    offlineMult: 3,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2025-02-14",
    name: "Valentine's Day",
    country: "Global",
    region: null,
    type: "Cultural",
    impact: "High",
    baseWeight: 72,
    onlineMult: 3.2,
    offlineMult: 2.4,
    preHaloDays: 10,
    postHaloDays: 1,
  },
  {
    date: "2025-02-26",
    name: "Maha Shivratri",
    country: "India",
    region: "National",
    type: "Religious",
    impact: "Medium",
    baseWeight: 42,
    onlineMult: 1.4,
    offlineMult: 2,
    preHaloDays: 5,
    postHaloDays: 1,
  },
  {
    date: "2025-03-01",
    name: "Ramadan Start",
    country: "Middle East",
    region: null,
    type: "Religious",
    impact: "Very High",
    baseWeight: 93,
    onlineMult: 3.5,
    offlineMult: 3.8,
    preHaloDays: 7,
    postHaloDays: 0,
  },
  {
    date: "2025-03-14",
    name: "Holi",
    country: "India",
    region: "National",
    type: "Religious",
    impact: "High",
    baseWeight: 78,
    onlineMult: 2.8,
    offlineMult: 3.5,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2025-03-30",
    name: "Ugadi",
    country: "India",
    region: "Telangana / Andhra Pradesh / Karnataka",
    type: "Religious",
    impact: "High",
    baseWeight: 68,
    onlineMult: 2.2,
    offlineMult: 2.8,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2025-03-30",
    name: "Gudi Padwa",
    country: "India",
    region: "Maharashtra",
    type: "Religious",
    impact: "High",
    baseWeight: 65,
    onlineMult: 2,
    offlineMult: 2.8,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2025-03-31",
    name: "Eid ul-Fitr",
    country: "Global",
    region: null,
    type: "Religious",
    impact: "Very High",
    baseWeight: 97,
    onlineMult: 4.2,
    offlineMult: 4.5,
    preHaloDays: 7,
    postHaloDays: 5,
  },
  {
    date: "2025-04-13",
    name: "Baisakhi",
    country: "India",
    region: "Punjab / Haryana",
    type: "Religious",
    impact: "High",
    baseWeight: 68,
    onlineMult: 2,
    offlineMult: 3,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2025-04-14",
    name: "Tamil New Year (Puthandu)",
    country: "India",
    region: "Tamil Nadu",
    type: "Cultural",
    impact: "High",
    baseWeight: 65,
    onlineMult: 2,
    offlineMult: 2.8,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2025-04-14",
    name: "Bihu (Rongali)",
    country: "India",
    region: "Assam",
    type: "Cultural",
    impact: "High",
    baseWeight: 65,
    onlineMult: 1.8,
    offlineMult: 2.8,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2025-04-18",
    name: "Good Friday",
    country: "Global",
    region: null,
    type: "Religious",
    impact: "Low",
    baseWeight: 20,
    onlineMult: 0.9,
    offlineMult: 0.6,
    preHaloDays: 2,
    postHaloDays: 0,
  },
  {
    date: "2025-04-20",
    name: "Easter Sunday",
    country: "Global",
    region: null,
    type: "Religious",
    impact: "Medium",
    baseWeight: 45,
    onlineMult: 1.4,
    offlineMult: 1.5,
    preHaloDays: 5,
    postHaloDays: 1,
  },
  {
    date: "2025-05-11",
    name: "Mother's Day",
    country: "Global",
    region: null,
    type: "Cultural",
    impact: "High",
    baseWeight: 68,
    onlineMult: 2.8,
    offlineMult: 2.1,
    preHaloDays: 14,
    postHaloDays: 1,
  },
  {
    date: "2025-05-26",
    name: "Memorial Day",
    country: "USA",
    region: null,
    type: "Cultural",
    impact: "High",
    baseWeight: 60,
    onlineMult: 2,
    offlineMult: 2.8,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2025-06-06",
    name: "Eid ul-Adha",
    country: "Global",
    region: null,
    type: "Religious",
    impact: "Very High",
    baseWeight: 91,
    onlineMult: 3.8,
    offlineMult: 4,
    preHaloDays: 5,
    postHaloDays: 4,
  },
  {
    date: "2025-06-15",
    name: "Father's Day",
    country: "Global",
    region: null,
    type: "Cultural",
    impact: "Medium",
    baseWeight: 50,
    onlineMult: 2.2,
    offlineMult: 1.7,
    preHaloDays: 10,
    postHaloDays: 1,
  },
  {
    date: "2025-06-18",
    name: "618 Shopping Festival",
    country: "China",
    region: null,
    type: "Shopping",
    impact: "Very High",
    baseWeight: 88,
    onlineMult: 5.2,
    offlineMult: 1.5,
    preHaloDays: 14,
    postHaloDays: 3,
  },
  {
    date: "2025-07-04",
    name: "Independence Day",
    country: "USA",
    region: null,
    type: "Cultural",
    impact: "High",
    baseWeight: 65,
    onlineMult: 1.7,
    offlineMult: 3,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2025-08-05",
    name: "Friendship Day",
    country: "Global",
    region: null,
    type: "Cultural",
    impact: "Low",
    baseWeight: 28,
    onlineMult: 1.5,
    offlineMult: 1.3,
    preHaloDays: 5,
    postHaloDays: 1,
  },
  {
    date: "2025-08-09",
    name: "Raksha Bandhan",
    country: "India",
    region: "National",
    type: "Cultural",
    impact: "High",
    baseWeight: 74,
    onlineMult: 3,
    offlineMult: 3.2,
    preHaloDays: 10,
    postHaloDays: 2,
  },
  {
    date: "2025-08-15",
    name: "Independence Day",
    country: "India",
    region: "National",
    type: "Cultural",
    impact: "Medium",
    baseWeight: 40,
    onlineMult: 1.8,
    offlineMult: 1.5,
    preHaloDays: 3,
    postHaloDays: 1,
  },
  {
    date: "2025-08-16",
    name: "Janmashtami",
    country: "India",
    region: "National",
    type: "Religious",
    impact: "High",
    baseWeight: 60,
    onlineMult: 1.8,
    offlineMult: 2.5,
    preHaloDays: 5,
    postHaloDays: 1,
  },
  {
    date: "2025-08-27",
    name: "Ganesh Chaturthi",
    country: "India",
    region: "Maharashtra / Goa / Karnataka",
    type: "Religious",
    impact: "High",
    baseWeight: 68,
    onlineMult: 2.2,
    offlineMult: 3.5,
    preHaloDays: 7,
    postHaloDays: 5,
  },
  {
    date: "2025-08-27",
    name: "Onam",
    country: "India",
    region: "Kerala",
    type: "Cultural",
    impact: "Very High",
    baseWeight: 88,
    onlineMult: 3,
    offlineMult: 4.2,
    preHaloDays: 10,
    postHaloDays: 3,
  },
  {
    date: "2025-09-17",
    name: "Chuseok (Korean Thanksgiving)",
    country: "South Korea",
    region: null,
    type: "Cultural",
    impact: "Very High",
    baseWeight: 92,
    onlineMult: 2.8,
    offlineMult: 4.5,
    preHaloDays: 7,
    postHaloDays: 3,
  },
  {
    date: "2025-09-22",
    name: "Navratri Begin",
    country: "India",
    region: "Gujarat / Rajasthan / MP",
    type: "Religious",
    impact: "High",
    baseWeight: 70,
    onlineMult: 2.5,
    offlineMult: 3.2,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2025-10-02",
    name: "Dussehra / Vijayadasami",
    country: "India",
    region: "National",
    type: "Religious",
    impact: "High",
    baseWeight: 72,
    onlineMult: 2.6,
    offlineMult: 3,
    preHaloDays: 7,
    postHaloDays: 2,
  },
  {
    date: "2025-10-06",
    name: "Flipkart Big Billion Days",
    country: "India",
    region: null,
    type: "Shopping",
    impact: "Very High",
    baseWeight: 97,
    onlineMult: 5.8,
    offlineMult: 1.2,
    preHaloDays: 7,
    postHaloDays: 3,
  },
  {
    date: "2025-10-06",
    name: "Amazon Great Indian Festival",
    country: "India",
    region: null,
    type: "Shopping",
    impact: "Very High",
    baseWeight: 96,
    onlineMult: 5.5,
    offlineMult: 1.2,
    preHaloDays: 7,
    postHaloDays: 3,
  },
  {
    date: "2025-10-13",
    name: "Karwa Chauth",
    country: "India",
    region: "North India",
    type: "Cultural",
    impact: "High",
    baseWeight: 65,
    onlineMult: 3.5,
    offlineMult: 2.8,
    preHaloDays: 7,
    postHaloDays: 1,
  },
  {
    date: "2025-10-13",
    name: "Canadian Thanksgiving",
    country: "Canada",
    region: null,
    type: "Cultural",
    impact: "High",
    baseWeight: 62,
    onlineMult: 2,
    offlineMult: 2.8,
    preHaloDays: 7,
    postHaloDays: 1,
  },
  {
    date: "2025-10-14",
    name: "Colombus Day",
    country: "USA",
    region: null,
    type: "Cultural",
    impact: "Low",
    baseWeight: 20,
    onlineMult: 1.3,
    offlineMult: 1.1,
    preHaloDays: 1,
    postHaloDays: 0,
  },
  {
    date: "2025-10-18",
    name: "Dhanteras",
    country: "India",
    region: "National",
    type: "Religious",
    impact: "Very High",
    baseWeight: 96,
    onlineMult: 4,
    offlineMult: 5,
    preHaloDays: 7,
    postHaloDays: 1,
  },
  {
    date: "2025-10-20",
    name: "Diwali",
    country: "India",
    region: "National",
    type: "Religious",
    impact: "Very High",
    baseWeight: 100,
    onlineMult: 4.8,
    offlineMult: 5.5,
    preHaloDays: 21,
    postHaloDays: 7,
  },
  {
    date: "2025-10-28",
    name: "Chhath Puja",
    country: "India",
    region: "Bihar / Jharkhand / UP / Delhi",
    type: "Religious",
    impact: "High",
    baseWeight: 62,
    onlineMult: 1.5,
    offlineMult: 2.8,
    preHaloDays: 5,
    postHaloDays: 2,
  },
  {
    date: "2025-10-31",
    name: "Halloween",
    country: "Global",
    region: null,
    type: "Cultural",
    impact: "Medium",
    baseWeight: 55,
    onlineMult: 2,
    offlineMult: 2.5,
    preHaloDays: 14,
    postHaloDays: 2,
  },
  {
    date: "2025-11-01",
    name: "Durga Puja",
    country: "India",
    region: "West Bengal / Odisha / Bihar",
    type: "Religious",
    impact: "Very High",
    baseWeight: 92,
    onlineMult: 3.5,
    offlineMult: 5,
    preHaloDays: 10,
    postHaloDays: 5,
  },
  {
    date: "2025-11-05",
    name: "Guru Nanak Jayanti",
    country: "India",
    region: "Punjab / Haryana / Delhi",
    type: "Religious",
    impact: "Medium",
    baseWeight: 45,
    onlineMult: 1.4,
    offlineMult: 1.8,
    preHaloDays: 3,
    postHaloDays: 1,
  },
  {
    date: "2025-11-11",
    name: "Singles' Day (11.11)",
    country: "Global",
    region: null,
    type: "Shopping",
    impact: "Very High",
    baseWeight: 98,
    onlineMult: 5.5,
    offlineMult: 1.5,
    preHaloDays: 14,
    postHaloDays: 3,
  },
  {
    date: "2025-11-11",
    name: "Double 11 / Singles' Day",
    country: "China",
    region: null,
    type: "Shopping",
    impact: "Very High",
    baseWeight: 100,
    onlineMult: 6,
    offlineMult: 1.8,
    preHaloDays: 14,
    postHaloDays: 3,
  },
  {
    date: "2025-11-27",
    name: "Thanksgiving",
    country: "USA",
    region: null,
    type: "Cultural",
    impact: "Very High",
    baseWeight: 88,
    onlineMult: 3.5,
    offlineMult: 3.2,
    preHaloDays: 14,
    postHaloDays: 1,
  },
  {
    date: "2025-11-28",
    name: "Black Friday",
    country: "Global",
    region: null,
    type: "Shopping",
    impact: "Very High",
    baseWeight: 100,
    onlineMult: 4.5,
    offlineMult: 3.8,
    preHaloDays: 7,
    postHaloDays: 3,
  },
  {
    date: "2025-12-01",
    name: "Cyber Monday",
    country: "Global",
    region: null,
    type: "Shopping",
    impact: "Very High",
    baseWeight: 95,
    onlineMult: 5,
    offlineMult: 1.2,
    preHaloDays: 2,
    postHaloDays: 2,
  },
  {
    date: "2025-12-25",
    name: "Christmas Day",
    country: "Global",
    region: null,
    type: "Religious",
    impact: "Very High",
    baseWeight: 97,
    onlineMult: 3.8,
    offlineMult: 4.2,
    preHaloDays: 30,
    postHaloDays: 5,
  },
  {
    date: "2025-12-26",
    name: "Boxing Day",
    country: "Global",
    region: "UK / Australia / Canada",
    type: "Shopping",
    impact: "High",
    baseWeight: 75,
    onlineMult: 3,
    offlineMult: 4,
    preHaloDays: 1,
    postHaloDays: 3,
  },
  {
    date: "2025-12-31",
    name: "New Year's Eve",
    country: "Global",
    region: null,
    type: "Cultural",
    impact: "High",
    baseWeight: 70,
    onlineMult: 2.2,
    offlineMult: 2.8,
    preHaloDays: 5,
    postHaloDays: 1,
  },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const roundTwo = (v: number) => Math.round(v * 100) / 100;

const parseSalesValue = (value: string | undefined): number | null => {
  if (!value) return null;
  const cleaned = value.replace(/[^0-9.\-]/g, "");
  if (!cleaned) return null;
  const parsed = Number(cleaned);
  return Number.isNaN(parsed) ? null : parsed;
};

const formatDate = (date: Date) => date.toISOString().split("T")[0];

// ---------------------------------------------------------------------------
// Festival lookup — build a map: dateStr → best festival for that date
// Expand each festival across its halo window so every affected forecast date
// knows its multiplier.
// ---------------------------------------------------------------------------
interface FestivalEffect {
  name: string;
  multiplier: number;
  impact: string;
}

const buildFestivalMap = (): Map<string, FestivalEffect> => {
  const map = new Map<string, FestivalEffect>();

  FESTIVAL_DATA.forEach((f) => {
    const peakDate = new Date(f.date);
    if (Number.isNaN(peakDate.getTime())) return;

    const rawMult = (f.onlineMult + f.offlineMult) / 2;
    const effectiveMult = 1 + ((rawMult - 1) * f.baseWeight) / 100;

    const start = new Date(peakDate);
    start.setDate(start.getDate() - f.preHaloDays);
    const end = new Date(peakDate);
    end.setDate(end.getDate() + f.postHaloDays);

    for (
      let cursor = new Date(start);
      cursor <= end;
      cursor.setDate(cursor.getDate() + 1)
    ) {
      const key = formatDate(new Date(cursor));
      const existing = map.get(key);
      if (!existing || effectiveMult > existing.multiplier) {
        map.set(key, { name: f.name, multiplier: effectiveMult, impact: f.impact });
      }
    }
  });

  return map;
};

const FESTIVAL_MAP = buildFestivalMap();

// ---------------------------------------------------------------------------
// Reuse existing classifyDemand / detectSeasonalPattern from CreateForecast
// (copy-pasted so this file is self-contained; tree-shake will remove dups)
// ---------------------------------------------------------------------------
const detectSeasonalPattern = (series: number[]): boolean => {
  if (series.length < 24) return false;
  const cycleLengths = [7, 14, 28, 30];
  const mean = series.reduce((s, v) => s + v, 0) / (series.length || 1);
  if (mean === 0) return false;

  for (const cycle of cycleLengths) {
    if (series.length < cycle * 2) continue;
    const sums = new Array(cycle).fill(0);
    const counts = new Array(cycle).fill(0);
    series.forEach((v, i) => {
      sums[i % cycle] += v;
      counts[i % cycle] += 1;
    });
    const avgs = sums.map((s, i) => (counts[i] ? s / counts[i] : 0));
    const rmse = Math.sqrt(
      series.reduce((acc, v, i) => acc + (v - avgs[i % cycle]) ** 2, 0) / series.length
    );
    if (rmse / Math.abs(mean) <= 0.15) return true;
  }
  return false;
};

export const classifyDemand = (series: number[]): DemandType => {
  const length = series.length;
  const mean = length ? series.reduce((s, v) => s + v, 0) / length : 0;
  const variance = length
    ? series.reduce((s, v) => s + (v - mean) ** 2, 0) / length
    : 0;
  const std = Math.sqrt(variance);
  const cv = mean !== 0 ? std / mean : 0;
  const zeroRatio = length
    ? series.filter((v) => v === 0).length / length
    : 0;

  if (length < 20) return "New";
  if (zeroRatio >= 0.4) return "Intermittent";
  if (detectSeasonalPattern(series)) return "Seasonal";
  if (cv <= 0.5) return "Smooth";
  return "Erratic";
};

// ---------------------------------------------------------------------------
// Model selector
// ---------------------------------------------------------------------------
type ModelKey = "moving_avg" | "weighted_avg" | "non_zero_avg" | "seasonal_repeat" | "naive";

const selectModel = (type: DemandType): ModelKey => {
  switch (type) {
    case "Smooth":
      return "moving_avg";
    case "Erratic":
      return "weighted_avg";
    case "Intermittent":
      return "non_zero_avg";
    case "Seasonal":
      return "seasonal_repeat";
    case "New":
      return "naive";
    default:
      return "moving_avg";
  }
};

const MODEL_META: Record<ModelKey, { name: string; reason: string }> = {
  moving_avg: {
    name: "Moving Average",
    reason: "Stable demand pattern detected",
  },
  weighted_avg: {
    name: "Weighted Moving Average",
    reason: "High variability — recent trends weighted more",
  },
  non_zero_avg: {
    name: "Non-Zero Average",
    reason: "Sparse demand — ignoring zero-sale periods",
  },
  seasonal_repeat: {
    name: "Seasonal Repeat",
    reason: "Repeating seasonal pattern detected",
  },
  naive: {
    name: "Naïve (Last Value)",
    reason: "Insufficient history — using most recent observation",
  },
};

// ---------------------------------------------------------------------------
// Confidence by demand type
// ---------------------------------------------------------------------------
const CONFIDENCE: Record<DemandType, "High" | "Medium" | "Low"> = {
  Smooth: "High",
  Seasonal: "Medium",
  Erratic: "Low",
  Intermittent: "Low",
  New: "Low",
};

// ---------------------------------------------------------------------------
// Model implementations — each returns a single base forecast value
// ---------------------------------------------------------------------------
const movingAverage = (series: number[], window = 7): number => {
  const slice = series.slice(-Math.min(window, series.length));
  return slice.reduce((s, v) => s + v, 0) / (slice.length || 1);
};

const weightedAverage = (series: number[], window = 7): number => {
  const slice = series.slice(-Math.min(window, series.length));
  let weightSum = 0;
  let totalWeight = 0;
  slice.forEach((v, i) => {
    const w = i + 1;
    weightSum += v * w;
    totalWeight += w;
  });
  return totalWeight ? weightSum / totalWeight : 0;
};

const nonZeroAverage = (series: number[]): number => {
  const nonZero = series.filter((v) => v !== 0);
  if (!nonZero.length) return 0;
  return nonZero.reduce((s, v) => s + v, 0) / nonZero.length;
};

const seasonalRepeat = (series: number[], cycle = 7): number => {
  if (series.length < cycle) return series[series.length - 1] ?? 0;
  return series[series.length - cycle];
};

const naiveForecast = (series: number[]): number =>
  series.length ? series[series.length - 1] : 0;

// ---------------------------------------------------------------------------
// Apply the correct model
// ---------------------------------------------------------------------------
const applyModel = (model: ModelKey, series: number[], step: number): number => {
  switch (model) {
    case "moving_avg":
      return movingAverage(series);
    case "weighted_avg":
      return weightedAverage(series);
    case "non_zero_avg":
      return nonZeroAverage(series);
    case "seasonal_repeat":
      return seasonalRepeat(series, 7);
    case "naive":
      return naiveForecast(series);
    default:
      return movingAverage(series);
  }
};

// ---------------------------------------------------------------------------
// Main export — generateSmartForecast
// ---------------------------------------------------------------------------
export const generateSmartForecast = (
  cleanedRows: CsvRow[],
  mapping: { dateColumn: string; salesColumn: string },
  config: ForecastConfig,
  fullMapping?: DataMapping,
): ForecastSection => {
  void fullMapping;
  const salesByDate: Record<string, number> = {};

  cleanedRows.forEach((row) => {
    const dateValue = row[mapping.dateColumn];
    const salesValue = parseSalesValue(row[mapping.salesColumn]);
    if (!dateValue || salesValue === null) return;
    const d = dateValue.slice(0, 10);
    salesByDate[d] = (salesByDate[d] ?? 0) + salesValue;
  });

  const sortedDates = Object.keys(salesByDate).sort(
    (a, b) => new Date(a).getTime() - new Date(b).getTime()
  );

  if (!sortedDates.length) {
    const emptyForecast = Array.from({ length: config.forecastDurationDays }, () => ({
      date: "",
      p10: 0,
      p50: 0,
      p90: 0,
    }));
    const emptySmart: SmartForecastOutput = {
      summary: {
        forecastTotal: 0,
        avgDailyDemand: 0,
        trend: "stable",
        demandType: "New",
        confidence: "Low",
      },
      model: MODEL_META.naive,
      historical: [],
      forecast: [],
      meta: {
        appliedFestivalDays: 0,
        dataPointsUsed: 0,
      },
    };
    return {
      sectionName: "Overall Demand Forecast",
      chart: { history: [], forecast: emptyForecast },
      metrics: {
        totalForecast: 0,
        avgDailyForecast: 0,
        minForecast: 0,
        maxForecast: 0,
      },
      table: emptyForecast.map((entry) => ({
        date: entry.date,
        forecast: entry.p50,
        lowerBound: entry.p10,
        upperBound: entry.p90,
      })),
      smart: emptySmart,
    };
  }

  const firstDate = new Date(sortedDates[0]);
  const lastDate = new Date(sortedDates[sortedDates.length - 1]);
  const allDates: string[] = [];

  for (
    let cursor = new Date(firstDate);
    cursor <= lastDate;
    cursor.setDate(cursor.getDate() + 1)
  ) {
    allDates.push(formatDate(new Date(cursor)));
  }

  const history = allDates.map((date) => ({
    date,
    value: roundTwo(salesByDate[date] ?? 0),
  }));

  const series = history.map((h) => h.value);

  const demandType = classifyDemand(series);
  const modelKey = selectModel(demandType);
  const modelMeta = MODEL_META[modelKey];

  const rolling = [...series];
  const lastHistoryDate = new Date(allDates[allDates.length - 1]);
  const forecastPoints: SmartForecastOutput["forecast"] = [];
  let appliedFestivalDays = 0;

  for (let i = 1; i <= config.forecastDurationDays; i++) {
    const base = roundTwo(applyModel(modelKey, rolling, i));

    const forecastDate = new Date(lastHistoryDate);
    forecastDate.setDate(forecastDate.getDate() + i);
    const dateStr = formatDate(forecastDate);

    const festival = FESTIVAL_MAP.get(dateStr);
    let finalValue = base;
    let festivalName: string | undefined;
    let festivalImpact: number | undefined;

    if (festival && base > 0) {
      finalValue = roundTwo(base * festival.multiplier);
      festivalName = festival.name;
      festivalImpact = roundTwo(festival.multiplier);
      appliedFestivalDays++;
    }

    const p10 = roundTwo(finalValue * 0.9);
    const p90 = roundTwo(finalValue * 1.1);

    forecastPoints.push({
      date: dateStr,
      value: finalValue,
      p10,
      p90,
      festivalName,
      festivalImpact,
    });

    rolling.push(base);
    if (rolling.length > Math.max(config.windowSize, 30)) rolling.shift();
  }

  const forecastValues = forecastPoints.map((f) => f.value);
  const forecastTotal = roundTwo(
    forecastValues.reduce((sum, value) => sum + value, 0)
  );
  const avgDailyDemand = roundTwo(
    forecastTotal / Math.max(1, config.forecastDurationDays)
  );
  const minForecast = roundTwo(Math.min(...forecastValues));
  const maxForecast = roundTwo(Math.max(...forecastValues));

  const firstForecast = forecastValues[0] ?? 0;
  const lastForecast = forecastValues[forecastValues.length - 1] ?? 0;
  const trend: "increasing" | "decreasing" | "stable" =
    lastForecast > firstForecast * 1.02
      ? "increasing"
      : lastForecast < firstForecast * 0.98
      ? "decreasing"
      : "stable";

  const legacyForecast = forecastPoints.map((f) => ({
    date: f.date,
    p10: f.p10,
    p50: f.value,
    p90: f.p90,
  }));

  const smart: SmartForecastOutput = {
    summary: {
      forecastTotal,
      avgDailyDemand,
      trend,
      demandType,
      confidence: CONFIDENCE[demandType],
    },
    model: modelMeta,
    historical: history,
    forecast: forecastPoints,
    meta: {
      appliedFestivalDays,
      dataPointsUsed: series.length,
    },
  };

  return {
    sectionName: "Overall Demand Forecast",
    chart: {
      history,
      forecast: legacyForecast,
    },
    metrics: {
      totalForecast: forecastTotal,
      avgDailyForecast: avgDailyDemand,
      minForecast,
      maxForecast,
    },
    table: forecastPoints.map((f) => ({
      date: f.date,
      forecast: f.value,
      lowerBound: f.p10,
      upperBound: f.p90,
    })),
    smart,
  };
};
