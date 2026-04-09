import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#f7f9fd",
        surface: "#f7f9fd",
        "surface-bright": "#f7f9fd",
        "surface-dim": "#d8dade",
        "surface-container-lowest": "#ffffff",
        "surface-container-low": "#f2f4f8",
        "surface-container": "#eceef2",
        "surface-container-high": "#e6e8ec",
        "surface-container-highest": "#e0e3e6",
        "surface-variant": "#e0e3e6",
        outline: "#737686",
        "outline-variant": "#c3c6d7",
        primary: "#004ac6",
        "primary-container": "#2563eb",
        "primary-fixed": "#dbe1ff",
        "primary-fixed-dim": "#b4c5ff",
        "on-primary-fixed": "#00174b",
        secondary: "#565e74",
        tertiary: "#943700",
        "tertiary-container": "#bc4800",
        error: "#ba1a1a",
        "error-container": "#ffdad6",
        "on-error-container": "#93000a",
        success: "#15803d",
        warning: "#d97706",
        "on-surface": "#181c1f",
        "on-surface-variant": "#434655",
        "on-secondary-container": "#5c647a",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      },
      boxShadow: {
        panel: "0 14px 36px rgba(15, 23, 42, 0.08)",
      },
      backgroundImage: {
        kinetic: "linear-gradient(135deg, #004ac6 0%, #2563eb 100%)",
      },
    },
  },
  plugins: [],
};

export default config;

// anything
