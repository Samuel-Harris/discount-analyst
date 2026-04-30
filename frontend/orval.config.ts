import { defineConfig } from "orval";

export default defineConfig({
  dashboard: {
    input: "./openapi.json",
    output: {
      mode: "single",
      target: "./src/api/generated.ts",
      client: "fetch",
      override: {
        fetch: { includeHttpResponseReturnType: false },
        mutator: {
          path: "./src/api/orval-mutator.ts",
          name: "dashboardMutator",
        },
      },
    },
  },
});
