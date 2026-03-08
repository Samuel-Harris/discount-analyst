"use client";

export type DiffByServer = {
  added: Record<string, string[]>;
  removed: Record<string, string[]>;
  unchanged: Record<string, string[]>;
};

interface DiffPanelProps {
  diff: DiffByServer;
  servers: string[];
  totalTools: number;
  totalSelected: number;
  onRestore: (server: string, name: string) => void;
  onRemove: (server: string, name: string) => void;
  onClearAll: () => void;
}

function DiffSection({
  title,
  items,
  variant,
  onRestore,
  onRemove,
}: {
  title: string;
  items: { server: string; name: string }[];
  variant: "added" | "removed" | "unchanged";
  onRestore?: (server: string, name: string) => void;
  onRemove?: (server: string, name: string) => void;
}) {
  if (items.length === 0) return null;

  const variantStyles = {
    added: "border-green-500/30 bg-green-500/10 text-green-600 dark:text-green-400",
    removed: "border-red-500/30 bg-red-500/10 text-red-600 dark:text-red-400",
    unchanged: "border-[var(--border)] bg-[var(--surface-hover)] text-[var(--text-muted)]",
  };

  const icon = {
    added: "+",
    removed: "−",
    unchanged: "=",
  };

  return (
    <div className="mb-4">
      <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">
        {title} ({items.length})
      </h3>
      <ul className="space-y-1">
        {items.map(({ server, name }) => (
          <li
            key={`${server}:${name}`}
            className={`flex items-start justify-between gap-2 rounded border px-2 py-1.5 text-sm ${variantStyles[variant]}`}
          >
            <span className="flex min-w-0 flex-1 items-start gap-2">
              <span className="shrink-0 pt-0.5 font-mono text-xs opacity-70">{server}</span>
              <span className={`min-w-0 break-words ${variant === "removed" ? "line-through" : ""}`}>
                {name}
              </span>
            </span>
            {variant === "removed" && onRestore && (
              <button
                type="button"
                onClick={() => onRestore(server, name)}
                className="shrink-0 self-start rounded px-2 py-0.5 text-xs font-medium hover:bg-red-500/20"
              >
                Restore
              </button>
            )}
            {(variant === "added" || variant === "unchanged") && onRemove && (
              <button
                type="button"
                onClick={() => onRemove(server, name)}
                className="shrink-0 self-start rounded px-2 py-0.5 text-xs font-medium hover:bg-green-500/20"
                title="Remove from selection"
              >
                Remove
              </button>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function DiffPanel({
  diff,
  servers,
  totalTools,
  totalSelected,
  onRestore,
  onRemove,
  onClearAll,
}: DiffPanelProps) {
  const addedItems = servers.flatMap((server) =>
    (diff.added[server] ?? []).map((name) => ({ server, name }))
  );
  const removedItems = servers.flatMap((server) =>
    (diff.removed[server] ?? []).map((name) => ({ server, name }))
  );
  const unchangedItems = servers.flatMap((server) =>
    (diff.unchanged[server] ?? []).map((name) => ({ server, name }))
  );

  const hasChanges = addedItems.length > 0 || removedItems.length > 0;

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--surface)]">
      <div className="border-b border-[var(--border)] px-4 py-3">
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-sm font-semibold text-[var(--text)]">Changes</h2>
          {totalSelected > 0 && (
            <button
              type="button"
              onClick={onClearAll}
              className="rounded px-2 py-1 text-xs font-medium hover:bg-red-500/20"
            >
              Clear all
            </button>
          )}
        </div>
        <p className="mt-0.5 text-xs text-[var(--text-muted)]">
          {totalSelected} of {totalTools} tools selected
        </p>
        <p className="mt-0.5 text-xs text-[var(--text-muted)]">
          {hasChanges
            ? `${addedItems.length} added, ${removedItems.length} removed`
            : "No net changes"}
        </p>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-3">
        {!hasChanges && unchangedItems.length === 0 ? (
          <p className="text-sm text-[var(--text-muted)]">No tools selected.</p>
        ) : (
          <>
            <DiffSection
              title="Added"
              items={addedItems}
              variant="added"
              onRemove={onRemove}
            />
            <DiffSection
              title="Removed"
              items={removedItems}
              variant="removed"
              onRestore={onRestore}
            />
            <DiffSection
              title="Unchanged"
              items={unchangedItems}
              variant="unchanged"
              onRemove={onRemove}
            />
          </>
        )}
      </div>
    </div>
  );
}
