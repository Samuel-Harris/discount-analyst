import { Fragment, type ReactNode } from "react";

function renderJsonValue(value: unknown, indent: string): ReactNode {
  const next = `${indent}  `;
  if (value === null) return <span className="json-null">null</span>;
  if (typeof value === "boolean") {
    return <span className="json-bool">{value ? "true" : "false"}</span>;
  }
  if (typeof value === "number") {
    if (Number.isNaN(value) || !Number.isFinite(value)) {
      return <span className="json-null">null</span>;
    }
    return <span className="json-num">{String(value)}</span>;
  }
  if (typeof value === "string") {
    return <span className="json-str">{JSON.stringify(value)}</span>;
  }
  if (Array.isArray(value)) {
    if (value.length === 0) return <>[]</>;
    return (
      <>
        {"["}
        {"\n"}
        {value.map((item, i) => (
          <Fragment key={i}>
            {next}
            {renderJsonValue(item, next)}
            {i < value.length - 1 ? "," : ""}
            {"\n"}
          </Fragment>
        ))}
        {indent}
        {"]"}
      </>
    );
  }
  if (typeof value === "object") {
    const o = value as Record<string, unknown>;
    const keys = Object.keys(o);
    if (keys.length === 0) return <>{"{}"}</>;
    return (
      <>
        {"{"}
        {"\n"}
        {keys.map((k, i) => (
          <Fragment key={k}>
            {next}
            <span className="json-key">{JSON.stringify(k)}</span>
            {": "}
            {renderJsonValue(o[k], next)}
            {i < keys.length - 1 ? "," : ""}
            {"\n"}
          </Fragment>
        ))}
        {indent}
        {"}"}
      </>
    );
  }
  return <span className="json-null">null</span>;
}

/** Pretty-printed JSON with basic syntax colouring (keys, strings, numbers, booleans). */
export function JsonPretty({ raw }: { raw: string }) {
  try {
    const parsed: unknown = JSON.parse(raw);
    return (
      <pre className="json-syntax json-syntax-block" tabIndex={0}>
        {renderJsonValue(parsed, "")}
      </pre>
    );
  } catch {
    return <pre className="agent-json-fallback">{raw}</pre>;
  }
}
