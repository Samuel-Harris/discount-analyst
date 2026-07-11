import js from "@eslint/js";
import importPlugin from "eslint-plugin-import";
import tseslint from "typescript-eslint";

const sharedLayers = [
  "./src/components",
  "./src/lib",
  "./src/types",
  "./src/utils",
  "./src/api",
];

/** @type {import('eslint').Linter.Config[]} */
export default tseslint.config(
  {
    ignores: ["dist/**", "src/api/generated.ts"],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["src/**/*.{ts,tsx}"],
    plugins: {
      import: importPlugin,
    },
    settings: {
      "import/resolver": {
        typescript: {
          project: "./tsconfig.json",
          alwaysTryTypes: true,
        },
        node: {
          extensions: [".js", ".jsx", ".ts", ".tsx"],
        },
      },
    },
    rules: {
      // Structure contract only — leave other style to TypeScript / Vitest.
      "@typescript-eslint/no-unused-vars": "off",
      "@typescript-eslint/no-explicit-any": "off",
      "no-unused-vars": "off",
      "import/no-restricted-paths": [
        "error",
        {
          basePath: import.meta.dirname,
          zones: [
            {
              target: "./src/features/workflow-runs",
              from: [
                "./src/features/pipeline-graph",
                "./src/features/agent-conversation",
                "./src/app",
              ],
              message:
                "workflow-runs must not import other features or app/; compose in app/.",
            },
            {
              target: "./src/features/pipeline-graph",
              from: [
                "./src/features/workflow-runs",
                "./src/features/agent-conversation",
                "./src/app",
              ],
              message:
                "pipeline-graph must not import other features or app/; compose in app/.",
            },
            {
              target: "./src/features/agent-conversation",
              from: [
                "./src/features/workflow-runs",
                "./src/features/pipeline-graph",
                "./src/app",
              ],
              message:
                "agent-conversation must not import other features or app/; compose in app/.",
            },
            {
              target: sharedLayers,
              from: ["./src/features", "./src/app"],
              message: "Shared layers must not import from features/ or app/.",
            },
          ],
        },
      ],
    },
  },
);
