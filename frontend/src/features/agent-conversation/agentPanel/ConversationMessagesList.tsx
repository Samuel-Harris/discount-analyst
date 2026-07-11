import { JsonPretty } from "@/components/JsonPretty";
import { SafeMarkdown } from "./SafeMarkdown";

export interface ConversationMessagesListProps {
  messagesJson: string;
}

type MessageKind = "request" | "response";

interface MessagePart {
  part_kind: string;
  content?: string;
  tool_name?: string;
  tool_call_id?: string;
  args?: string;
}

interface ConversationMessage {
  kind: MessageKind;
  parts: MessagePart[];
}

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function isMessageKind(v: unknown): v is MessageKind {
  return v === "request" || v === "response";
}

function normaliseMessages(raw: unknown): ConversationMessage[] | null {
  if (!Array.isArray(raw)) return null;
  const out: ConversationMessage[] = [];
  for (const item of raw) {
    if (!isRecord(item)) return null;
    const kind = item.kind;
    const partsRaw = item.parts;
    if (!isMessageKind(kind) || !Array.isArray(partsRaw)) return null;
    const parts: MessagePart[] = [];
    for (const p of partsRaw) {
      if (!isRecord(p)) return null;
      const partKind = p.part_kind;
      if (typeof partKind !== "string") return null;
      const part: MessagePart = { part_kind: partKind };
      if (typeof p.content === "string") part.content = p.content;
      if (typeof p.tool_name === "string") part.tool_name = p.tool_name;
      if (typeof p.tool_call_id === "string")
        part.tool_call_id = p.tool_call_id;
      if (typeof p.args === "string") part.args = p.args;
      parts.push(part);
    }
    out.push({ kind, parts });
  }
  return out;
}

function truncateMiddle(s: string, max: number): string {
  if (s.length <= max) return s;
  const half = Math.floor((max - 1) / 2);
  return `${s.slice(0, half)}…${s.slice(s.length - half)}`;
}

function ToolArgsBody({ raw }: { raw: string }) {
  try {
    const parsed: unknown = JSON.parse(raw);
    return <JsonPretty raw={JSON.stringify(parsed, null, 2)} />;
  } catch {
    return (
      <pre className="conversation-part-pre agent-panel-scroll-sm">{raw}</pre>
    );
  }
}

function MessagePartBlock({
  part,
  messageIndex,
  partIndex,
}: {
  part: MessagePart;
  messageIndex: number;
  partIndex: number;
}) {
  const idPrefix = `msg${messageIndex}-p${partIndex}-`;
  const k = part.part_kind;

  if (k === "tool-call") {
    const label = part.tool_name ?? "tool";
    const args = part.args ?? "";
    const summary = `${label}(${truncateMiddle(args.replace(/\s+/g, " "), 48)})`;
    return (
      <div className="conversation-part conversation-part-tool">
        <details>
          <summary className="conversation-tool-summary">{summary}</summary>
          <div className="conversation-tool-body agent-panel-scroll-comfortable">
            <ToolArgsBody raw={args} />
          </div>
        </details>
      </div>
    );
  }

  if (k === "tool-return") {
    const label = part.tool_name ? `${part.tool_name} · return` : "tool return";
    const content = part.content ?? "";
    const summary = `${label}(${truncateMiddle(content.replace(/\s+/g, " "), 40)})`;
    return (
      <div className="conversation-part conversation-part-tool">
        <details>
          <summary className="conversation-tool-summary">{summary}</summary>
          <div className="conversation-tool-body agent-panel-scroll-comfortable">
            <ToolArgsBody raw={content} />
          </div>
        </details>
      </div>
    );
  }

  if (k === "unknown") {
    const content = part.content ?? "";
    return (
      <div className="conversation-part">
        <pre className="conversation-part-pre agent-panel-scroll-comfortable">
          {content}
        </pre>
      </div>
    );
  }

  const content = part.content ?? "";
  if (
    k === "text" ||
    k === "user-prompt" ||
    k === "system-prompt" ||
    k === "retry-prompt"
  ) {
    return (
      <div className="conversation-part conversation-part-prose">
        <SafeMarkdown
          markdown={content}
          headingIdPrefix={idPrefix}
          className="agent-panel-prose"
        />
      </div>
    );
  }

  return (
    <div className="conversation-part conversation-part-prose">
      <SafeMarkdown
        markdown={content}
        headingIdPrefix={idPrefix}
        className="agent-panel-prose"
      />
    </div>
  );
}

export function ConversationMessagesList({
  messagesJson,
}: ConversationMessagesListProps) {
  let parsed: unknown;
  try {
    parsed = JSON.parse(messagesJson) as unknown;
  } catch {
    return (
      <div className="conversation-messages-fallback">
        <p className="conversation-messages-parse-error">
          Could not parse messages JSON.
        </p>
        <JsonPretty raw={messagesJson} />
      </div>
    );
  }

  const messages = normaliseMessages(parsed);
  if (!messages) {
    return (
      <div className="conversation-messages-fallback">
        <p className="conversation-messages-parse-error">
          Unexpected messages shape.
        </p>
        <JsonPretty raw={messagesJson} />
      </div>
    );
  }

  return (
    <div className="conversation-messages-list">
      <ol className="conversation-messages-timeline">
        {messages.map((msg, mi) => (
          <li key={mi} className="conversation-message-row">
            <div className="conversation-message-meta">
              <span
                className={`message-kind-chip message-kind-chip--${msg.kind}`}
              >
                {msg.kind === "request" ? "Request" : "Response"}
              </span>
              <span className="conversation-message-index">
                Message {mi + 1}
              </span>
            </div>
            <div className="conversation-message-parts">
              {msg.parts.map((part, pi) => (
                <MessagePartBlock
                  key={pi}
                  part={part}
                  messageIndex={mi}
                  partIndex={pi}
                />
              ))}
            </div>
          </li>
        ))}
      </ol>
      <details className="conversation-messages-raw-details">
        <summary>Raw messages_json</summary>
        <div className="conversation-messages-raw agent-panel-scroll-comfortable">
          <JsonPretty raw={messagesJson} />
        </div>
      </details>
    </div>
  );
}
