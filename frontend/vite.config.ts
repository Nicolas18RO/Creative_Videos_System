import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/editorial-training": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/human-feedback": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/editorial-dataset": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
  },
});
