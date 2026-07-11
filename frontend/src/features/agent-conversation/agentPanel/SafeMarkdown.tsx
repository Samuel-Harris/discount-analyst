import ReactMarkdown from "react-markdown";
import rehypeSlug from "rehype-slug";
import remarkGfm from "remark-gfm";

export interface SafeMarkdownProps {
  markdown: string;
  /** Prepended to each generated heading `id` so multiple renders stay unique */
  headingIdPrefix: string;
  className?: string;
}

/**
 * GFM markdown without raw HTML (`rehype-raw` is intentionally omitted).
 */
export function SafeMarkdown({
  markdown,
  headingIdPrefix,
  className,
}: SafeMarkdownProps) {
  return (
    <div className={className}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[[rehypeSlug, { prefix: headingIdPrefix }]]}
        components={{
          a: ({ href, children, ...rest }) => {
            const external =
              typeof href === "string" && /^https?:\/\//i.test(href);
            return (
              <a
                {...rest}
                href={href}
                rel={external ? "noopener noreferrer" : undefined}
                target={external ? "_blank" : undefined}
              >
                {children}
              </a>
            );
          },
          table: ({ children, ...rest }) => (
            <div className="agent-panel-prose-table-wrap">
              <table {...rest}>{children}</table>
            </div>
          ),
        }}
      >
        {markdown}
      </ReactMarkdown>
    </div>
  );
}
