import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

const frontendDir = path.dirname(fileURLToPath(import.meta.url));

function normaliseDeployEnv(raw: string | undefined): "DEV" | "PROD" {
  const v = (raw ?? "DEV").trim().toUpperCase();
  return v === "PROD" ? "PROD" : "DEV";
}

export default defineConfig(({ mode }) => {
  const fromFiles = loadEnv(mode, frontendDir, "");
  const proxyTarget =
    process.env.VITE_DEV_PROXY_TARGET?.trim() ||
    fromFiles.VITE_DEV_PROXY_TARGET?.trim() ||
    "http://127.0.0.1:8000";
  const deployEnv = normaliseDeployEnv(process.env.ENV);

  return {
    define: {
      "import.meta.env.VITE_DEPLOY_ENV": JSON.stringify(deployEnv),
    },
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        "/api": {
          target: proxyTarget,
          changeOrigin: true,
        },
      },
    },
  };
});
