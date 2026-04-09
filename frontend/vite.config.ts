import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig({
  envDir: resolve(__dirname, "../"),
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
