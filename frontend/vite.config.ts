import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  resolve: {
    // Use the official ESM entry so Vite can bundle xlsx correctly
    alias: {
      xlsx: "xlsx/xlsx.mjs",
    },
  },
  server: {
    port: 5173,
  },
});
