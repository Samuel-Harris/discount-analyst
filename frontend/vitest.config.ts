import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const frontendDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  define: {
    "import.meta.env.VITE_DEPLOY_ENV": JSON.stringify("DEV"),
    __VITE_API_PREFIX__: JSON.stringify("/api"),
  },
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(frontendDir, "src"),
    },
  },
  test: {
    environment: "jsdom",
    globals: false,
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
