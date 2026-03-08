"use client";

import { useState } from "react";
import type { Tool } from "@/lib/types";

interface ToolRowProps {
  tool: Tool;
  selected: boolean;
  onToggle: () => void;
}

export function ToolRow({ tool, selected, onToggle }: ToolRowProps) {
  const [expanded, setExpanded] = useState(false);
  const desc = tool.description ?? "";
  const isLong = desc.length > 120;

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onToggle}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onToggle();
        }
      }}
      className={`flex cursor-pointer items-start gap-3 rounded-lg border px-3 py-2 transition-colors ${
        selected
          ? "border-[var(--primary)]/50 bg-[var(--primary)]/15"
          : "border-transparent hover:border-[var(--border)] hover:bg-[var(--surface-hover)]"
      }`}
      aria-label={`${selected ? "Deselect" : "Select"} ${tool.name}`}
      aria-pressed={selected}
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="font-medium text-[var(--text)]">{tool.name}</span>
        </div>
        <p className="mt-0.5 text-sm text-[var(--text-muted)]">
          {isLong && !expanded ? (
            <>
              {desc.slice(0, 120)}…
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setExpanded(true);
                }}
                className="ml-1 text-[var(--primary)] hover:underline"
              >
                Show more
              </button>
            </>
          ) : (
            <>
              {desc}
              {isLong && expanded && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setExpanded(false);
                  }}
                  className="ml-1 text-[var(--primary)] hover:underline"
                >
                  Show less
                </button>
              )}
            </>
          )}
        </p>
      </div>
    </div>
  );
}
