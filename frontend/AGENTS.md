<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-07-11 | Updated: 2026-07-11 (thin shell + ownership) -->

# frontend

## Purpose

Vite + React SPA for the local Discount Analyst dashboard. This directory owns the browser UI structure contract: compose features in `src/app/`, keep domain UI in coarse `src/features/*`, and keep shared API, polling, components, types, and utils free of feature or app imports.

## Key Files

| File               | Description                                                                                      |
| ------------------ | ------------------------------------------------------------------------------------------------ |
| `package.json`     | pnpm scripts (`dev`, `build`, `test`, `lint`, `generate:api`) and frontend dependencies.         |
| `eslint.config.js` | Flat ESLint config with `import/no-restricted-paths` zones for BPR unidirectional boundaries.    |
| `vite.config.ts`   | Vite + React; proxies `/api` to the FastAPI backend.                                             |
| `vitest.config.ts` | Vitest (jsdom); setup at `src/test/setup.ts`.                                                    |
| `orval.config.ts`  | Orval client generation from `openapi.json` into `src/api/generated.ts`.                         |
| `openapi.json`     | Committed OpenAPI snapshot for the dashboard API (regenerate via repo scripts; CI checks drift). |
| `tsconfig.json`    | TypeScript project for `src/` with `@/*` → `src/*` path aliases.                                 |
| `index.html`       | Vite HTML entry.                                                                                 |

## Subdirectories

| Directory                          | Purpose                                                                                                                           |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `src/app/`                         | Shell composition: thin `DashboardShell` wiring + `WorkflowRunMainPanel` (sorts ticker lanes once for graph and recommendations). |
| `src/features/workflow-runs/`      | Run list/sidebar, launch form, detail header, recommendations view, run hooks (`useWorkflowRunActions`, navigation/detail/list).  |
| `src/features/pipeline-graph/`     | React Flow pipeline graph, lane order (`tickerRunOrder`), and layout builders.                                                    |
| `src/features/agent-conversation/` | Agent conversation panel (`AgentPanel` + `agentPanel/**`), `useConversation`, and `useAgentConversationPanel`.                    |
| `src/components/`                  | Shared presentational pieces only (`UiStateText`, `JsonPretty`, `DeployEnvBadge`).                                                |
| `src/api/`                         | Orval-generated client, `orval-mutator.ts`, and thin `index.ts` facade (allowed shared API surface — not a feature barrel).       |
| `src/lib/server-state/`            | Custom polling + invalidation (`usePollingQuery`, `invalidation`, `queryKeys`). Import modules directly — no barrel `index.ts`.   |
| `src/utils/`                       | Pure helpers (`formatWhen`, `laneStatusDisplay`).                                                                                 |
| `src/types/`                       | Shared types such as `ConversationTarget` (so graph/app do not import the agent-conversation feature).                            |
| `src/test/`                        | Vitest setup (`setup.ts`). Do not rename to `testing/`.                                                                           |

Entry wiring stays at `src/main.tsx` and `src/App.tsx` (thin root that mounts `app/DashboardShell`).

## Structure contract (Bulletproof React–style)

```text
src/
  app/           # compose features only here
  features/      # workflow-runs | pipeline-graph | agent-conversation
  components/    # shared UI
  api/           # Orval client
  lib/           # server-state polling
  types/         # shared types
  utils/         # shared pure helpers
  test/          # Vitest setup
```

### Unidirectional import rules (documented + ESLint)

- `features/*` must not import from other `features/*`
- `features/*` and shared layers must not import from `app/`
- Shared (`components`, `lib`, `types`, `utils`, `api`) must not import from `features/` or `app/`
- Compose features only in `app/`
- No feature barrel files (`index.ts` re-exports per feature)
- Prefer `@/` imports for anything outside the current folder (maps to `src/`); keep `./` for co-located siblings
- Keep custom URL navigation (`useWorkflowRunNavigation`: `?run=` / `?view=recommendations`) and custom `lib/server-state` (not React Router / TanStack Query)

## For AI Agents

### Working In This Directory

- Use **pnpm** (see `packageManager` in `package.json`), not npm/yarn.
- After OpenAPI changes: regenerate from the repo root (`uv run python scripts/export_dashboard_openapi.py`) then `pnpm run generate:api`; commit `openapi.json` and `src/api/generated.ts` together.
- Prefer co-located `*.test.ts(x)` next to the module under test.
- British English applies to AGENTS.md prose; code identifiers stay as in the API/codebase.
- When moving files, update ESLint zones and any backend sync paths (e.g. `agentLaneOrder.ts`) in the same change.

### Testing Requirements

- `pnpm lint` — import-boundary enforcement
- `pnpm test` — Vitest suite
- `pnpm run build` — `tsc -b` + Vite production build
- CI frontend job runs lint, build, and test

### Common Patterns

- Feature modules import shared layers with `@/` aliases (`@/api`, `@/lib/server-state/...`).
- Cross-feature data shapes live in `src/types/` or `src/utils/`, not in another feature.
- `ReactFlowProvider` stays inside the pipeline-graph feature.

## Dependencies

### Internal

- Dashboard FastAPI under `backend/` (proxied `/api` in Vite).
- Lane-order contract mirrored with `backend/contracts/agent_lane_order.py` via `src/features/pipeline-graph/agentLaneOrder.ts`.

### External

- **React 19** + **Vite 6** — SPA toolchain
- **@xyflow/react** — pipeline graph
- **Orval** — typed API client from OpenAPI
- **Vitest** + Testing Library — unit/UI tests
- **ESLint** + **typescript-eslint** + **eslint-plugin-import** — boundary lint

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
