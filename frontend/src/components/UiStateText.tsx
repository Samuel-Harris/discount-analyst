import type { ReactNode } from "react";

export type UiStateTone = "loading" | "error" | "muted";

const toneClass: Record<UiStateTone, string> = {
  loading: "ui-state-text--loading",
  error: "ui-state-text--error",
  muted: "ui-state-text--muted",
};

export interface UiStateTextProps {
  tone: UiStateTone;
  children: ReactNode;
  as?: "p" | "span" | "div";
  className?: string;
}

/** Inline or block status copy (loading, errors, empty hints) with consistent tone colours. */
export function UiStateText({
  tone,
  children,
  as: Component = "span",
  className = "",
}: UiStateTextProps) {
  return (
    <Component
      className={["ui-state-text", toneClass[tone], className]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </Component>
  );
}
