export interface Tool {
  name: string;
  title: string | null;
  description: string;
  inputSchema?: unknown;
  outputSchema?: unknown;
}

export type ToolListByServer = Record<string, Tool[]>;

export type CuratedByServer = Record<string, string[]>;
