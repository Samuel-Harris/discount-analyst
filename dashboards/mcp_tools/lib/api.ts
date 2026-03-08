import type { ToolListByServer, CuratedByServer } from "./types";

export async function fetchTools(): Promise<ToolListByServer> {
  const res = await fetch("/api/tools");
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error ?? `Failed to fetch tools: ${res.status}`);
  }
  return res.json();
}

export async function fetchCurated(): Promise<CuratedByServer> {
  const res = await fetch("/api/curated");
  if (!res.ok) {
    throw new Error(`Failed to fetch curated: ${res.status}`);
  }
  const data = await res.json();
  if (typeof data !== "object" || data === null) return {};
  const normalized: CuratedByServer = {};
  for (const [k, v] of Object.entries(data)) {
    normalized[k] = Array.isArray(v) ? (v as string[]) : [];
  }
  return normalized;
}

export async function saveCurated(data: CuratedByServer): Promise<void> {
  const res = await fetch("/api/curated", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error ?? `Failed to save: ${res.status}`);
  }
}
