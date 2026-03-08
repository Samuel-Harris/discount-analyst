<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-08 | Updated: 2026-03-08 -->

# dashboards

## Purpose

React-based web dashboards for the Discount Analyst project. The MCP Tool Dashboard lets users browse, search, and curate MCP tools from EODHD and FMP servers, saving selections to `curated_tool_list.json`.

## Key Files

| File | Description |
| ---- | ------------ |
| `package.json` | Dependencies and scripts (pnpm). |
| `app/page.tsx` | Main MCP Tool Dashboard page. |
| `app/api/tools/route.ts` | GET `tool_list.json` from `scripts/mcp/`. |
| `app/api/curated/route.ts` | GET/POST `curated_tool_list.json`. |
| `lib/api.ts` | Client for fetching tools and saving curated list. |
| `lib/types.ts` | `Tool`, `ToolListByServer`, `CuratedByServer` types. |

## Subdirectories

| Directory | Purpose |
| --------- | ------- |
| `app/` | Next.js App Router pages and API routes. |
| `components/` | SearchBar, ServerTabs, ToolList, ToolRow, SaveButton. |
| `lib/` | API client and shared types. |

## Run Commands

| Command | Description |
| ------- | ----------- |
| `pnpm dev` | Start dev server (run from `dashboards/`). |
| `pnpm build` | Production build. |
| `pnpm start` | Run production server. |

## Data Paths

API routes resolve `tool_list.json` and `curated_tool_list.json` relative to the project root `scripts/mcp/` directory. When running from `dashboards/`, the project root is one level up. Set `MCP_DATA_DIR` to override the data directory.

## For AI Agents

### Working In This Directory

- Use pnpm for dependency management.
- API routes perform file I/O; ensure `scripts/mcp/` exists and contains the JSON files.
- The dashboard reads `tool_list.json` (full tool definitions) and writes `curated_tool_list.json` (selected tool names by server) on Save.

## Dependencies

### External

- **Next.js 16**: App Router, API routes.
- **React 19**: UI components.
- **Tailwind CSS 4**: Styling.
- **TypeScript**: Type safety.
