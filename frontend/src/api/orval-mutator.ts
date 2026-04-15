const apiPrefix = (import.meta.env.VITE_API_PREFIX ?? "/api").replace(
  /\/$/,
  "",
);

/** Thrown when the dashboard HTTP API returns an error or an unreadable body. */
export class DashboardApiError extends Error {
  readonly status: number;
  readonly bodySnippet: string;

  constructor(
    message: string,
    status: number,
    bodySnippet: string,
    options?: { cause?: unknown },
  ) {
    super(message, options);
    this.name = "DashboardApiError";
    this.status = status;
    this.bodySnippet = bodySnippet;
  }
}

/** Map OpenAPI paths (``/api/...``) onto the configured dashboard API prefix. */
function resolveDashboardUrl(path: string): string {
  if (path.startsWith("/api")) {
    return `${apiPrefix}${path.slice(4)}`;
  }
  return `${apiPrefix}${path.startsWith("/") ? path : `/${path}`}`;
}

function snippet(text: string, max = 200): string {
  if (text.length <= max) return text;
  return `${text.slice(0, max)}…`;
}

export async function dashboardMutator<T>(
  url: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(resolveDashboardUrl(url), init);
  if (!res.ok) {
    const text = await res.text();
    throw new DashboardApiError(
      text || res.statusText || `Request failed with status ${res.status}`,
      res.status,
      snippet(text),
    );
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
  try {
    return JSON.parse(raw) as T;
  } catch (cause) {
    throw new DashboardApiError(
      "The dashboard API returned a response that could not be parsed as JSON.",
      res.status,
      snippet(raw),
      { cause },
    );
  }
}
