import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  envDir: "../",
  plugins: [react()],
  optimizeDeps: {
    include: ["xlsx"],
  },
  resolve: {
    alias: {
      fs: "rollup-plugin-node-polyfills/polyfills/empty",
    },
  },
});

// anything
