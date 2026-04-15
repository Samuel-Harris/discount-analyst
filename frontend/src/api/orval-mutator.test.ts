import { afterEach, describe, expect, it, vi } from "vitest";

import { dashboardMutator, DashboardApiError } from "./orval-mutator";

describe("dashboardMutator", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("throws DashboardApiError with status and body snippet for non-OK responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response("not found", { status: 404, statusText: "Not Found" }),
        ),
    );
    await expect(dashboardMutator("/api/x")).rejects.toSatisfy((e: unknown) => {
      expect(e).toBeInstanceOf(DashboardApiError);
      const err = e as DashboardApiError;
      expect(err.status).toBe(404);
      expect(err.message).toBe("not found");
      expect(err.bodySnippet).toBe("not found");
      return true;
    });
  });

  it("throws DashboardApiError when the body is not valid JSON", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(new Response("<html>oops</html>", { status: 200 })),
    );
    try {
      await dashboardMutator("/api/x");
      expect.fail("expected rejection");
    } catch (e) {
      expect(e).toBeInstanceOf(DashboardApiError);
      const err = e as DashboardApiError;
      expect(err.status).toBe(200);
      expect(err.message).toContain("could not be parsed as JSON");
      expect(err.bodySnippet.startsWith("<html>")).toBe(true);
      expect(err.cause).toBeDefined();
    }
  });

  it("returns undefined for empty 200 bodies", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 200 })),
    );
    await expect(dashboardMutator("/api/x")).resolves.toBeUndefined();
  });

  it("parses JSON for successful responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response(JSON.stringify({ ok: true }), { status: 200 }),
        ),
    );
    await expect(dashboardMutator<{ ok: boolean }>("/api/x")).resolves.toEqual({
      ok: true,
    });
  });
});
