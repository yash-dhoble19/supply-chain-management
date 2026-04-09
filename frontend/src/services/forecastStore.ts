import type { ForecastSnapshot } from "../types/forecast.types";

type ForecastListener = () => void;

const STORAGE_KEY = "latest_forecast_snapshot";

// Initialize from localStorage if available
let latestForecast: ForecastSnapshot | null = (() => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : null;
  } catch {
    return null;
  }
})();

const listeners = new Set<ForecastListener>();

const notifyListeners = () => {
  listeners.forEach((listener) => listener());
};

export const setLatestForecastSnapshot = (snapshot: ForecastSnapshot) => {
  latestForecast = snapshot;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot));
  } catch (e) {
    console.error("Failed to save forecast to localStorage:", e);
  }
  notifyListeners();
};

export const getLatestForecastSnapshot = () => latestForecast;

export const clearLatestForecastSnapshot = () => {
  latestForecast = null;
  localStorage.removeItem(STORAGE_KEY);
  notifyListeners();
};

export const subscribeToForecastUpdates = (listener: ForecastListener) => {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
};
