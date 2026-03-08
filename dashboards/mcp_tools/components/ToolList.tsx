"use client";

import type { Tool } from "@/lib/types";
import { ToolRow } from "./ToolRow";

interface ToolListProps {
  tools: Tool[];
  selected: Set<string>;
  onToggle: (name: string) => void;
}

export function ToolList({ tools, selected, onToggle }: ToolListProps) {
  if (tools.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-[var(--text-muted)]">
        No tools match the search.
      </p>
    );
  }

  return (
    <ul className="space-y-1">
      {tools.map((tool) => (
        <li key={tool.name}>
          <ToolRow
            tool={tool}
            selected={selected.has(tool.name)}
            onToggle={() => onToggle(tool.name)}
          />
        </li>
      ))}
    </ul>
  );
}
