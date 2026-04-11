const apiPrefix = (import.meta.env.VITE_API_PREFIX ?? "/api").replace(/\/$/, "");

/** Map OpenAPI paths (``/api/...``) onto the configured dashboard API prefix. */
function resolveDashboardUrl(path: string): string {
  if (path.startsWith("/api")) {
    return `${apiPrefix}${path.slice(4)}`;
  }
  return `${apiPrefix}${path.startsWith("/") ? path : `/${path}`}`;
}

export async function dashboardMutator<T>(
  url: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(resolveDashboardUrl(url), init);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  if (res.status === 204 || res.status === 205) {
    return undefined as T;
  }
  if (res.status === 304) {
    return undefined as T;
  }
  const raw = await res.text();
  if (!raw) {
    return undefined as T;
  }
  return JSON.parse(raw) as T;
}
