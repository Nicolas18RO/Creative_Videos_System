import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/analyze": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/search": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/feedback": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/projects": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/gaps": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/library": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/playback": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/export": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/editorial-training": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/editorial-review": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/editorial-timeline": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/editorial-registry": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/editorial-category": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/editorial-semantic-intent": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/timeline-visualization": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/human-feedback": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/editorial-dataset": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
  },
});
