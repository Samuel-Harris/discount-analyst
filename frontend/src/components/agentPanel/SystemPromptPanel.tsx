import { useCallback, useLayoutEffect, useMemo, useRef, useState } from "react";

import { SafeMarkdown } from "./SafeMarkdown";
import { splitMarkdownSections } from "./splitMarkdownSections";

export interface SystemPromptPanelProps {
  systemPrompt: string;
}

type ViewMode = "rendered" | "raw";

export function SystemPromptPanel({ systemPrompt }: SystemPromptPanelProps) {
  const [mode, setMode] = useState<ViewMode>("rendered");
  const [copyHint, setCopyHint] = useState("");
  const sections = useMemo(
    () => splitMarkdownSections(systemPrompt),
    [systemPrompt],
  );
  const outlineRootRef = useRef<HTMLDivElement>(null);
  const [outline, setOutline] = useState<{ id: string; text: string }[]>([]);

  useLayoutEffect(() => {
    if (mode !== "rendered") {
      setOutline([]);
      return;
    }
    const root = outlineRootRef.current;
    if (!root) {
      setOutline([]);
      return;
    }
    const nodes = root.querySelectorAll(
      ".system-prompt-section-body .agent-panel-prose h2, .system-prompt-section-body .agent-panel-prose h3",
    );
    const next: { id: string; text: string }[] = [];
    nodes.forEach((el) => {
      const id = el.id;
      if (!id) return;
      const text = el.textContent?.trim() ?? "";
      if (!text) return;
      next.push({ id, text });
    });
    setOutline(next);
  }, [mode, systemPrompt, sections]);

  const copyPrompt = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(systemPrompt);
      setCopyHint("Copied");
      window.setTimeout(() => setCopyHint(""), 2000);
    } catch {
      setCopyHint("Copy failed");
      window.setTimeout(() => setCopyHint(""), 2500);
    }
  }, [systemPrompt]);

  return (
    <div className="system-prompt-panel">
      <div
        className="system-prompt-toolbar"
        role="group"
        aria-label="System prompt view"
      >
        <div className="system-prompt-view-toggle">
          <button
            type="button"
            className={mode === "rendered" ? "is-active" : ""}
            aria-pressed={mode === "rendered"}
            onClick={() => setMode("rendered")}
          >
            Rendered
          </button>
          <button
            type="button"
            className={mode === "raw" ? "is-active" : ""}
            aria-pressed={mode === "raw"}
            onClick={() => setMode("raw")}
          >
            Raw
          </button>
        </div>
        <button
          type="button"
          className="system-prompt-copy"
          onClick={copyPrompt}
        >
          Copy prompt
        </button>
      </div>
      <span className="sr-only" aria-live="polite">
        {copyHint}
      </span>
      {mode === "raw" ? (
        <pre className="system-prompt-raw agent-panel-scroll-comfortable">
          {systemPrompt}
        </pre>
      ) : (
        <>
          {outline.length > 0 ? (
            <nav className="system-prompt-outline" aria-label="Prompt sections">
              {outline.map((item) => (
                <a
                  key={item.id}
                  href={`#${item.id}`}
                  className="system-prompt-outline-link"
                >
                  {item.text}
                </a>
              ))}
            </nav>
          ) : null}
          <div ref={outlineRootRef} className="system-prompt-sections">
            {sections.map((section, index) => (
              <details
                key={`${section.summaryLabel}-${index}`}
                className="system-prompt-details"
                open={index < 2}
              >
                <summary className="system-prompt-details-summary">
                  {section.summaryLabel}
                </summary>
                <div className="system-prompt-section-body agent-panel-scroll-comfortable">
                  <SafeMarkdown
                    markdown={section.body}
                    headingIdPrefix={`s${index}-`}
                    className="agent-panel-prose"
                  />
                </div>
              </details>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
