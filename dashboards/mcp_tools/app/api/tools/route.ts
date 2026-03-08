import { NextResponse } from "next/server";
import path from "path";
import fs from "fs";

function getMcpDataDir(): string {
  const override = process.env.MCP_DATA_DIR;
  if (override) return override;
  const cwd = process.cwd();
  const basename = path.basename(cwd);
  const projectRoot =
    basename === "mcp_tools"
      ? path.resolve(cwd, "..", "..")
      : basename === "dashboards"
        ? path.resolve(cwd, "..")
        : cwd;
  return path.resolve(projectRoot, "scripts", "mcp");
}

export async function GET() {
  try {
    const dataDir = getMcpDataDir();
    const toolListPath = path.join(dataDir, "tool_list.json");
    const content = fs.readFileSync(toolListPath, "utf-8");
    const data = JSON.parse(content);
    if (typeof data !== "object" || data === null) {
      return NextResponse.json(
        { error: "tool_list.json must be a dict with server keys (eodhd, fmp)." },
        { status: 500 }
      );
    }
    return NextResponse.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    if (message.includes("ENOENT")) {
      return NextResponse.json(
        {
          error: `tool_list.json not found. Run: uv run python scripts/mcp/fetch_mcp_tool_list.py -o scripts/mcp/tool_list.json`,
        },
        { status: 404 }
      );
    }
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
