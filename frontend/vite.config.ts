import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const alias = {
  xlsx: "xlsx/dist/xlsx.full.mjs",
};

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias,
  },
  server: {
    port: 5173,
  },
});
