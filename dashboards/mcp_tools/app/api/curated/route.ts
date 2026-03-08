import { NextRequest, NextResponse } from "next/server";
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
    const curatedPath = path.join(dataDir, "curated_tool_list.json");
    if (!fs.existsSync(curatedPath)) {
      return NextResponse.json({});
    }
    const content = fs.readFileSync(curatedPath, "utf-8");
    const data = JSON.parse(content);
    if (typeof data !== "object" || data === null) {
      return NextResponse.json({});
    }
    const normalized: Record<string, string[]> = {};
    for (const [k, v] of Object.entries(data)) {
      normalized[k] = Array.isArray(v) ? v : [];
    }
    return NextResponse.json(normalized);
  } catch {
    return NextResponse.json({});
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    if (typeof body !== "object" || body === null) {
      return NextResponse.json(
        { error: "Body must be a JSON object." },
        { status: 400 }
      );
    }
    const normalized: Record<string, string[]> = {};
    for (const [k, v] of Object.entries(body)) {
      if (typeof k !== "string") continue;
      normalized[k] = Array.isArray(v)
        ? (v as unknown[]).filter((x): x is string => typeof x === "string")
        : [];
    }
    const dataDir = getMcpDataDir();
    const curatedPath = path.join(dataDir, "curated_tool_list.json");
    fs.writeFileSync(curatedPath, JSON.stringify(normalized, null, 2), "utf-8");
    return NextResponse.json({ success: true });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
