"use client";

interface ServerTabsProps {
  servers: string[];
  active: string;
  onSelect: (server: string) => void;
}

const SERVER_DOT_COLORS: Record<string, string> = {
  eodhd: "bg-[#38bdf8]",
  fmp: "bg-[#818cf8]",
};

function getDotColor(server: string): string {
  return SERVER_DOT_COLORS[server] ?? "bg-[var(--text-muted)]";
}

export function ServerTabs({ servers, active, onSelect }: ServerTabsProps) {
  return (
    <div className="flex gap-1 border-b border-[var(--border)]">
      {servers.map((server) => (
        <button
          key={server}
          type="button"
          onClick={() => onSelect(server)}
          className={`relative flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
            active === server
              ? "text-[var(--primary)]"
              : "text-[var(--text-muted)] hover:text-[var(--text)]"
          }`}
        >
          <span
            className={`h-1.5 w-1.5 shrink-0 rounded-full ${getDotColor(server)}`}
            aria-hidden
          />
          <span className="uppercase tracking-wide">{server}</span>
          {active === server && (
            <span
              className="absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--primary)]"
              aria-hidden
            />
          )}
        </button>
      ))}
    </div>
  );
}
