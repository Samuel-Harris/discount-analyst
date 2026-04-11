/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_PREFIX?: string;
  /** Injected at build time from process.env.ENV (Compose: DEV / PROD). */
  readonly VITE_DEPLOY_ENV: "DEV" | "PROD";
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
