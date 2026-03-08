"use client";

import { use, useCallback, useEffect, useMemo, useState } from "react";
import { SearchBar } from "@/components/SearchBar";
import { ServerTabs } from "@/components/ServerTabs";
import { ToolList } from "@/components/ToolList";
import { SaveButton } from "@/components/SaveButton";
import { DiffPanel, type DiffByServer } from "@/components/DiffPanel";
import { fetchTools, fetchCurated, saveCurated } from "@/lib/api";
import type { Tool } from "@/lib/types";

function matchesSearch(tool: Tool, query: string): boolean {
  if (!query.trim()) return true;
  const q = query.toLowerCase();
  const name = (tool.name ?? "").toLowerCase();
  const desc = (tool.description ?? "").toLowerCase();
  return q.includes(name) || name.includes(q) || desc.includes(q);
}

type PageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default function Page(props: PageProps) {
  const _searchParams = props.searchParams ? use(props.searchParams) : {};
  const [toolsData, setToolsData] = useState<Record<string, Tool[]>>({});
  const [curated, setCurated] = useState<Record<string, string[]>>({});
  const [savedCurated, setSavedCurated] = useState<Record<string, string[]>>({});
  const [searchQuery, setSearchQuery] = useState("");
  const [activeServer, setActiveServer] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<"idle" | "success" | "error">("idle");
  const [saveMessage, setSaveMessage] = useState("");
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  const servers = useMemo(() => Object.keys(toolsData), [toolsData]);
  const curServer = activeServer || servers[0];

  const curServerTools = toolsData[curServer] ?? [];
  const curServerSelectedNames = useMemo(
    () => new Set(curated[curServer] ?? []),
    [curated, curServer]
  );

  const filteredTools = useMemo(() => {
    const tools = toolsData[curServer] ?? [];
    if (!searchQuery.trim()) return tools;
    return tools.filter((t) => matchesSearch(t, searchQuery));
  }, [curServer, toolsData, searchQuery]);

  const curServerSelectedCount = (curated[curServer] ?? []).length;

  const totalSelected = useMemo(() => {
    let n = 0;
    for (const [server, names] of Object.entries(curated)) {
      n += names.length;
    }
    return n;
  }, [curated]);

  const totalTools = useMemo(() => {
    return Object.values(toolsData).reduce((a, b) => a + b.length, 0);
  }, [toolsData]);

  const [dirty, setDirty] = useState(false);

  const diff = useMemo((): DiffByServer => {
    const added: Record<string, string[]> = {};
    const removed: Record<string, string[]> = {};
    const unchanged: Record<string, string[]> = {};
    for (const server of servers) {
      const saved = new Set(savedCurated[server] ?? []);
      const current = new Set(curated[server] ?? []);
      added[server] = [...current].filter((t) => !saved.has(t));
      removed[server] = [...saved].filter((t) => !current.has(t));
      unchanged[server] = [...current].filter((t) => saved.has(t));
    }
    return { added, removed, unchanged };
  }, [curated, savedCurated, servers]);

  const handleRestore = useCallback(
    (server: string, name: string) => {
      setCurated((prev) => {
        const list = prev[server] ?? [];
        if (list.includes(name)) return prev;
        return { ...prev, [server]: [...list, name] };
      });
      setDirty(true);
    },
    []
  );

  const handleRemove = useCallback(
    (server: string, name: string) => {
      setCurated((prev) => {
        const list = prev[server] ?? [];
        const next = list.filter((n) => n !== name);
        return { ...prev, [server]: next };
      });
      setDirty(true);
    },
    []
  );

  const handleClearAll = useCallback(() => {
    setCurated((prev) => {
      const next: Record<string, string[]> = {};
      for (const server of Object.keys(prev)) {
        next[server] = [];
      }
      return next;
    });
    setDirty(true);
  }, []);

  useEffect(() => {
    let mounted = true;
    Promise.all([fetchTools(), fetchCurated()])
      .then(([tools, cur]) => {
        if (!mounted) return;
        setToolsData(tools);
        setCurated(cur);
        setSavedCurated(cur);
        setActiveServer((s) => s || (Object.keys(tools)[0] ?? ""));
      })
      .catch((e) => {
        if (mounted) setError(e instanceof Error ? e.message : String(e));
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const handleSave = useCallback(async () => {
    try {
      await saveCurated(curated);
      setSaveStatus("success");
      setSaveMessage("Saved to curated_tool_list.json");
      setSavedCurated(curated);
      setDirty(false);
      setTimeout(() => setSaveStatus("idle"), 3000);
    } catch (e) {
      setSaveStatus("error");
      setSaveMessage(e instanceof Error ? e.message : String(e));
      setTimeout(() => setSaveStatus("idle"), 5000);
    }
  }, [curated]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "s") {
        e.preventDefault();
        handleSave();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [handleSave]);

  const handleBeforeUnload = useCallback((e: BeforeUnloadEvent) => {
    e.preventDefault();
  }, []);

  useEffect(() => {
    if (!dirty) return;
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [dirty, handleBeforeUnload]);

  const handleSelectAll = useCallback(() => {
    const server = curServer;
    const tools = toolsData[server] ?? [];
    const current = curated[server] ?? [];
    const allSelected = tools.length > 0 && current.length === tools.length;
    setCurated((prev) => {
      const next = { ...prev };
      next[server] = allSelected ? [] : tools.map((t) => t.name);
      return next;
    });
    setDirty(true);
  }, [curServer, toolsData, curated]);

  const handleToggle = useCallback(
    (name: string) => {
      setCurated((prev) => {
        const list = prev[curServer] ?? [];
        const set = new Set(list);
        if (set.has(name)) set.delete(name);
        else set.add(name);
        return { ...prev, [curServer]: [...set] };
      });
      setDirty(true);
    },
    [curServer]
  );

  const toggleTheme = useCallback(() => {
    setTheme((t) => {
      const next = t === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      return next;
    });
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-[var(--text-muted)]">Loading…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-8">
        <h1 className="text-xl font-semibold text-[var(--text)]">MCP Tool Dashboard</h1>
        <div className="mt-4 rounded-lg border border-red-500/50 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto flex min-h-dvh max-w-[1200px] flex-col px-6 py-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[var(--text)]">MCP Tool Dashboard</h1>
          <p className="mt-1 text-sm text-[var(--text-muted)]">
            Loaded {totalTools} tools from tool_list.json. {totalSelected} selected globally.
          </p>
        </div>
        <div className="flex items-center gap-4">
          {dirty && (
            <span className="text-sm text-[var(--accent)]">Unsaved changes</span>
          )}
          <button
            type="button"
            onClick={toggleTheme}
            className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-sm text-[var(--text-muted)] hover:text-[var(--text)]"
          >
            {theme === "dark" ? "Light" : "Dark"}
          </button>
          <span className="text-xs text-[var(--text-muted)]">⌘S to save</span>
          <SaveButton onSave={handleSave} />
        </div>
      </div>

      {saveStatus === "success" && (
        <div className="mb-4 rounded-lg border border-green-500/50 bg-green-500/10 px-4 py-2 text-sm text-green-400">
          {saveMessage}
        </div>
      )}
      {saveStatus === "error" && (
        <div className="mb-4 rounded-lg border border-red-500/50 bg-red-500/10 px-4 py-2 text-sm text-red-400">
          {saveMessage}
        </div>
      )}

      <div className="mb-4">
        <SearchBar value={searchQuery} onChange={setSearchQuery} />
      </div>

      {servers.length > 0 && (
        <div className="flex min-h-0 flex-1 items-start gap-4">
          <div className="flex min-h-0 min-w-0 flex-1 self-stretch flex-col">
            <ServerTabs
              servers={servers}
              active={curServer}
              onSelect={setActiveServer}
            />
            <div className="mt-4 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <span className="text-sm text-[var(--text-muted)]">
                  {curServerSelectedCount} of {curServerTools.length} selected
                </span>
                <button
                  type="button"
                  onClick={handleSelectAll}
                  className="text-sm text-[var(--primary)] hover:underline"
                >
                  {curServerSelectedCount === curServerTools.length
                    ? "Select none"
                    : "Select all"}
                </button>
              </div>
            </div>
            <div className="mt-4 min-h-0 flex-1 overflow-y-auto">
              <ToolList
                tools={filteredTools}
                selected={curServerSelectedNames}
                onToggle={handleToggle}
              />
            </div>
          </div>
          <div className="sticky top-6 flex h-[calc(100dvh-3rem)] min-h-0 w-80 shrink-0 self-start flex-col overflow-hidden">
            <DiffPanel
              diff={diff}
              servers={servers}
              totalTools={totalTools}
              totalSelected={totalSelected}
              onRestore={handleRestore}
              onRemove={handleRemove}
              onClearAll={handleClearAll}
            />
          </div>
        </div>
      )}
    </div>
  );
}
