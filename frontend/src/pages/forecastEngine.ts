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

export function getDemandTypes(): DemandType[] {
  return ["Smooth", "Erratic", "Intermittent", "Seasonal", "New"];
}

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
    forecast: number;
    lowerBound: number;
    upperBound: number;
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
// Prophet-only forecasting — single model for ALL demand types
// ---------------------------------------------------------------------------
// Demand classification (classifyDemand) is KEPT above for UI badges/insights
// but does NOT influence forecasting logic below.
// ---------------------------------------------------------------------------

const PROPHET_MODEL_META = {
  name: "Prophet (Adaptive)",
  reason: "Statistical decomposition — trend + seasonality + holiday effects",
};

/**
 * Derive confidence from data length (NOT from demand type).
 * Mirrors the backend data-quality-tier logic.
 */
const deriveConfidence = (dataPoints: number): "High" | "Medium" | "Low" => {
  if (dataPoints >= 180) return "High";   // ~6 months daily
  if (dataPoints >= 60) return "Medium";  // ~2 months daily
  return "Low";
};

// ---------------------------------------------------------------------------
// Data Preprocessing Pipeline
// ---------------------------------------------------------------------------

/**
 * Cap outliers using the IQR method.
 * Values above Q3 + 1.5*IQR are capped; values below Q1 - 1.5*IQR are floored.
 */
const capOutliersIQR = (data: number[]): number[] => {
  if (data.length < 4) return [...data];
  const sorted = [...data].sort((a, b) => a - b);
  const q1 = sorted[Math.floor(sorted.length * 0.25)];
  const q3 = sorted[Math.floor(sorted.length * 0.75)];
  const iqr = q3 - q1;
  const lower = Math.max(0, q1 - 1.5 * iqr);
  const upper = q3 + 1.5 * iqr;
  return data.map((v) => Math.min(Math.max(v, lower), upper));
};

/**
 * Apply centered rolling average to smooth noisy daily data.
 */
const rollingSmooth = (data: number[], window = 7): number[] => {
  if (data.length <= window) return [...data];
  const half = Math.floor(window / 2);
  return data.map((_, i) => {
    const start = Math.max(0, i - half);
    const end = Math.min(data.length, i + half + 1);
    const slice = data.slice(start, end);
    return slice.reduce((s, v) => s + v, 0) / slice.length;
  });
};

/**
 * Full preprocessing: outlier cap → rolling smooth.
 */
const preprocessSeries = (raw: number[]): number[] => {
  const capped = capOutliersIQR(raw);
  return rollingSmooth(capped, 7);
};

// ---------------------------------------------------------------------------
// Trend & Seasonality Decomposition
// ---------------------------------------------------------------------------

/**
 * Extract linear trend via least-squares regression.
 * Returns { slope, intercept } so trend(t) = intercept + slope * t
 */
const extractLinearTrend = (series: number[]): { slope: number; intercept: number } => {
  const n = series.length;
  if (n < 2) return { slope: 0, intercept: series[0] ?? 0 };

  let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
  for (let i = 0; i < n; i++) {
    sumX += i;
    sumY += series[i];
    sumXY += i * series[i];
    sumX2 += i * i;
  }
  const denom = n * sumX2 - sumX * sumX;
  const slope = denom !== 0 ? (n * sumXY - sumX * sumY) / denom : 0;
  const intercept = (sumY - slope * sumX) / n;
  return { slope, intercept };
};

/**
 * Extract weekly seasonality pattern (7-day cycle).
 * Returns an array of 7 additive offsets (Mon=0 … Sun=6).
 */
const extractWeeklySeasonality = (series: number[], trend: { slope: number; intercept: number }): number[] => {
  if (series.length < 14) return new Array(7).fill(0); // need ≥2 weeks

  // Detrend
  const detrended = series.map((v, i) => v - (trend.intercept + trend.slope * i));

  // Average by day-of-week position
  const buckets: number[][] = Array.from({ length: 7 }, () => []);
  detrended.forEach((v, i) => buckets[i % 7].push(v));

  const pattern = buckets.map((b) =>
    b.length ? b.reduce((s, v) => s + v, 0) / b.length : 0
  );

  // Center the pattern (subtract mean so it's purely additive)
  const mean = pattern.reduce((s, v) => s + v, 0) / 7;
  return pattern.map((v) => v - mean);
};

/**
 * Prophet-style forecast: trend projection + seasonal overlay.
 * Produces a single forecast value for step `futureStep` (1-indexed)
 * given the preprocessed historical series.
 */
const prophetForecast = (
  preprocessed: number[],
  trend: { slope: number; intercept: number },
  seasonality: number[],
  futureStep: number,
): number => {
  const n = preprocessed.length;
  // Project trend
  const trendValue = trend.intercept + trend.slope * (n - 1 + futureStep);
  // Add seasonal component
  const dayIndex = (n - 1 + futureStep) % 7;
  const seasonalValue = seasonality[dayIndex];
  // Combine: trend + seasonality, floor at 0
  return Math.max(0, trendValue + seasonalValue);
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
      model: PROPHET_MODEL_META,
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

  const rawSeries = history.map((h) => h.value);

  // Classification is PURELY DESCRIPTIVE — used only for UI badges/insights
  const demandType = classifyDemand(rawSeries);

  // -----------------------------------------------------------------------
  // PREPROCESSING: clean the series before decomposition
  // -----------------------------------------------------------------------
  const series = preprocessSeries(rawSeries);

  // Update history values to show smoothed data on chart (cleaner visual)
  const smoothedHistory = allDates.map((date, i) => ({
    date,
    value: roundTwo(series[i]),
  }));

  // -----------------------------------------------------------------------
  // DECOMPOSITION: extract trend + weekly seasonality
  // -----------------------------------------------------------------------
  const trendLine = extractLinearTrend(series);
  const weeklyPattern = extractWeeklySeasonality(series, trendLine);

  const lastHistoryDate = new Date(allDates[allDates.length - 1]);
  const forecastPoints: SmartForecastOutput["forecast"] = [];
  let appliedFestivalDays = 0;

  // Confidence interval width based on data variability
  const stdDev = series.length > 1
    ? Math.sqrt(series.reduce((s, v) => s + (v - series.reduce((a, b) => a + b, 0) / series.length) ** 2, 0) / series.length)
    : 0;
  const intervalPct = series.length >= 180 ? 0.10 : series.length >= 60 ? 0.15 : 0.20;

  for (let i = 1; i <= config.forecastDurationDays; i++) {
    // Prophet-style: trend projection + seasonal overlay
    const base = roundTwo(prophetForecast(series, trendLine, weeklyPattern, i));

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

    // Confidence intervals widen slightly over horizon
    const horizonFactor = 1 + (i / config.forecastDurationDays) * 0.5;
    const spread = Math.max(stdDev * intervalPct * horizonFactor, finalValue * intervalPct);
    const p10 = roundTwo(Math.max(0, finalValue - spread));
    const p90 = roundTwo(finalValue + spread);

    forecastPoints.push({
      date: dateStr,
      forecast: finalValue,
      lowerBound: p10,
      upperBound: p90,
      festivalName,
      festivalImpact,
    });
  }

  const forecastValues = forecastPoints.map((f) => f.forecast);
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
  const trendDirection: "increasing" | "decreasing" | "stable" =
    lastForecast > firstForecast * 1.02
      ? "increasing"
      : lastForecast < firstForecast * 0.98
      ? "decreasing"
      : "stable";

  const legacyForecast = forecastPoints.map((f) => ({
    date: f.date,
    p10: f.lowerBound,
    p50: f.forecast,
    p90: f.upperBound,
  }));

  // Confidence derived from data length, NOT demand type
  const confidence = deriveConfidence(series.length);

  const smart: SmartForecastOutput = {
    summary: {
      forecastTotal,
      avgDailyDemand,
      trend: trendDirection,
      demandType,          // kept for UI badges — purely descriptive
      confidence,          // derived from data points, not demand classification
    },
    model: PROPHET_MODEL_META,   // always Prophet — no model selection
    historical: smoothedHistory,
    forecast: forecastPoints,
    meta: {
      appliedFestivalDays,
      dataPointsUsed: series.length,
    },
  };

  return {
    sectionName: "Overall Demand Forecast",
    chart: {
      history: smoothedHistory,
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
      forecast: f.forecast,
      lowerBound: f.lowerBound,
      upperBound: f.upperBound,
    })),
    smart,
  };
};

