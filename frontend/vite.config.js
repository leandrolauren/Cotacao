import { defineConfig } from "vite";
import viteReact from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [viteReact()],
  server: {
    host: '0.0.0.0',
    headers: {
      'access-control-allow-origin': '*',
      'access-control-allow-methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'access-control-allow-headers': 'Content-Type, Authorization',
      'Cross-Origin-Opener-Policy': 'same-origin-allow-popups'
    },
    port: 3000,
    proxy: {

      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
  },
});
