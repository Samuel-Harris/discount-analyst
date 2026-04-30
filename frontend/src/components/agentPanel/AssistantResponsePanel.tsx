import { useCallback, useState } from "react";

import { JsonPretty } from "../JsonPretty";

export interface AssistantResponsePanelProps {
  assistantResponse: string;
}

export function AssistantResponsePanel({
  assistantResponse,
}: AssistantResponsePanelProps) {
  const [copyHint, setCopyHint] = useState("");

  const copyResponse = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(assistantResponse);
      setCopyHint("Copied");
      window.setTimeout(() => setCopyHint(""), 2000);
    } catch {
      setCopyHint("Copy failed");
      window.setTimeout(() => setCopyHint(""), 2500);
    }
  }, [assistantResponse]);

  return (
    <div className="assistant-response-panel">
      <div className="assistant-response-toolbar">
        <button
          type="button"
          className="assistant-response-copy"
          onClick={copyResponse}
        >
          Copy response
        </button>
      </div>
      <span className="sr-only" aria-live="polite">
        {copyHint}
      </span>
      <div className="assistant-response-json agent-panel-scroll-comfortable">
        <JsonPretty raw={assistantResponse} />
      </div>
    </div>
  );
}
