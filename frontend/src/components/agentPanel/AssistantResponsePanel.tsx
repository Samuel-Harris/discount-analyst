import { useCallback, useState } from "react";

import type { AgentNameSlug } from "../../api";
import { JsonPretty } from "../JsonPretty";

import { AppraiserValuationPanel } from "./AppraiserValuationPanel";
import { parseAppraiserOutput } from "./parseAppraiserOutput";
import "./appraiserValuation.css";

export interface AssistantResponsePanelProps {
  assistantResponse: string;
  agentName?: AgentNameSlug | null;
}

export function AssistantResponsePanel({
  assistantResponse,
  agentName = null,
}: AssistantResponsePanelProps) {
  const [copyHint, setCopyHint] = useState("");
  const isAppraiser = agentName === "appraiser";
  const appraiserOutput = isAppraiser
    ? parseAppraiserOutput(assistantResponse)
    : null;

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
      {isAppraiser && appraiserOutput ? (
        <AppraiserValuationPanel output={appraiserOutput} />
      ) : null}
      {isAppraiser && !appraiserOutput ? (
        <p className="assistant-response-parse-notice">
          Could not parse Appraiser output; showing raw JSON.
        </p>
      ) : null}
      {isAppraiser && appraiserOutput ? (
        <div className="assistant-response-raw">
          <details>
            <summary>Raw JSON</summary>
            <div className="assistant-response-json agent-panel-scroll-comfortable">
              <JsonPretty raw={assistantResponse} />
            </div>
          </details>
        </div>
      ) : (
        <div className="assistant-response-json agent-panel-scroll-comfortable">
          <JsonPretty raw={assistantResponse} />
        </div>
      )}
    </div>
  );
}
