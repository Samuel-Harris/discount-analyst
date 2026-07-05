export interface MarkdownSection {
  /** Label for the `<summary>` control */
  summaryLabel: string;
  /** Markdown source for this section, including its opening heading line when present */
  body: string;
}

function headingTitleFromFirstLine(firstLine: string): string | null {
  const m = firstLine.match(/^#{1,2}\s+(.+)$/);
  if (!m) return null;
  return m[1].trim();
}

/**
 * Split markdown on lines that start with `#` or `##` followed by whitespace (ATX headings depth 1-2 only).
 * Lines that look like headings inside fenced ``` blocks are ignored.
 */
export function splitMarkdownSections(source: string): MarkdownSection[] {
  const lines = source.split(/\r?\n/);
  const splitIndices: number[] = [];
  let inFence = false;

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trimStart();
    if (trimmed.startsWith("```")) {
      inFence = !inFence;
      continue;
    }
    if (inFence) continue;
    if (/^#{1,2}\s+/.test(line)) {
      splitIndices.push(i);
    }
  }

  if (splitIndices.length === 0) {
    const body = lines.join("\n");
    const first = lines[0] ?? "";
    const title = headingTitleFromFirstLine(first);
    return [
      {
        summaryLabel: title ?? "Introduction",
        body,
      },
    ];
  }

  const sections: MarkdownSection[] = [];
  const starts = [0, ...splitIndices];
  for (let s = 0; s < starts.length; s++) {
    const start = starts[s];
    const end = s + 1 < starts.length ? starts[s + 1] : lines.length;
    const chunkLines = lines.slice(start, end);
    const body = chunkLines.join("\n");
    const firstLine = chunkLines[0] ?? "";
    const title = headingTitleFromFirstLine(firstLine);
    sections.push({
      summaryLabel: title ?? "Introduction",
      body,
    });
  }

  return sections;
}
