import "@xyflow/react/dist/style.css";

import {
  memo,
  type KeyboardEvent,
  type MouseEvent,
  useCallback,
  useMemo,
} from "react";
import {
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  type Edge,
  type Node,
  type NodeProps,
  type NodeTypes,
  Position,
  ReactFlow,
  ReactFlowProvider,
} from "@xyflow/react";

import { buildGraphLayout, type LayoutNode } from "../graph/buildGraphLayout";
import type { ConversationTarget } from "../hooks/useConversation";
import type { WorkflowRunDetailResponse } from "../api";

type PipelineNodeData = {
  node: LayoutNode;
  onOpen: (target: ConversationTarget, title: string) => void;
};

type PipelineFlowNode = Node<PipelineNodeData, "pipeline">;

const CONVERSATION_AGENTS = new Set([
  "surveyor",
  "profiler",
  "researcher",
  "strategist",
  "sentinel",
  "appraiser",
  "arbiter",
]);

function conversationClickable(node: LayoutNode): boolean {
  if (node.status !== "completed") return false;
  return CONVERSATION_AGENTS.has(node.agentName);
}

/** Opens the conversation panel when the node is a valid transcript target. */
function emitConversationOpen(data: PipelineNodeData): void {
  const { node, onOpen } = data;
  if (!conversationClickable(node)) return;
  const title =
    node.kind === "workflow_surveyor"
      ? "surveyor · workflow"
      : `${node.agentName} · ${node.ticker ?? ""}`;
  if (node.kind === "workflow_surveyor") {
    onOpen({ kind: "surveyor", workflowRunId: node.workflowRunId }, title);
  } else if (node.runId) {
    onOpen(
      { kind: "run_agent", runId: node.runId, agentName: node.agentName },
      title,
    );
  }
}

const PipelineNode = memo(function PipelineNodeInner({
  data,
}: NodeProps<PipelineFlowNode>) {
  const { node } = data;
  const clickable = conversationClickable(node);
  const stClass = `status-${node.status}`;

  const onKeyDown = (e: KeyboardEvent) => {
    if (!clickable) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      emitConversationOpen(data);
    }
  };

  return (
    <div
      className={`pipeline-node nopan ${stClass}${clickable ? " clickable" : ""}`}
      onKeyDown={onKeyDown}
      role={clickable ? "button" : undefined}
      tabIndex={clickable ? 0 : undefined}
    >
      {node.handleTargetLeft ? (
        <Handle
          type="target"
          position={Position.Left}
          id="l"
          style={{ background: "var(--border)" }}
        />
      ) : null}
      {node.handleTargetTop ? (
        <Handle
          type="target"
          position={Position.Top}
          id="t"
          style={{ background: "var(--border)" }}
        />
      ) : null}
      <div>{node.label}</div>
      {node.kind === "lane_agent" && node.ticker ? (
        <div className="ticker-tag">{node.ticker}</div>
      ) : null}
      <div className="st">{node.status}</div>
      <Handle
        type="source"
        position={Position.Right}
        id="r"
        style={{ background: "var(--accent-dim)" }}
      />
    </div>
  );
});

const nodeTypes = { pipeline: PipelineNode } satisfies NodeTypes;

function graphHeight(detail: WorkflowRunDetailResponse): number {
  const lanes = Math.max(1, detail.runs.length);
  return 88 + 112 + lanes * 112 + 48;
}

function graphWidth(): number {
  return 32 + 150 * 6 + 140;
}

export interface PipelineGraphProps {
  detail: WorkflowRunDetailResponse;
  onOpenConversation: (target: ConversationTarget, title: string) => void;
}

function PipelineGraphInner({
  detail,
  onOpenConversation,
}: PipelineGraphProps) {
  const { nodes: layoutNodes, edges: layoutEdges } = useMemo(
    () => buildGraphLayout(detail),
    [detail],
  );

  const nodes: PipelineFlowNode[] = useMemo(
    () =>
      layoutNodes.map((n) => ({
        id: n.id,
        type: "pipeline" as const,
        position: n.position,
        data: { node: n, onOpen: onOpenConversation },
      })),
    [layoutNodes, onOpenConversation],
  );

  const edges: Edge[] = useMemo(
    () =>
      layoutEdges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle,
        targetHandle: e.targetHandle,
        style: { stroke: "var(--muted)", strokeWidth: 1.2 },
      })),
    [layoutEdges],
  );

  const onNodeClick = useCallback((_: MouseEvent, node: PipelineFlowNode) => {
    if (node.type !== "pipeline") return;
    emitConversationOpen(node.data);
  }, []);

  const h = graphHeight(detail);
  const w = graphWidth();

  return (
    <div className="graph-wrap" style={{ height: h, minHeight: 280 }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        onNodeClick={onNodeClick}
        panOnDrag={[1, 2]}
        panOnScroll
        zoomOnScroll
        fitView
        fitViewOptions={{ padding: 0.2, maxZoom: 1.1 }}
        minZoom={0.4}
        maxZoom={1.4}
        proOptions={{ hideAttribution: true }}
        style={{ width: w, height: "100%" }}
      >
        <Background
          color="rgba(57, 255, 122, 0.06)"
          gap={20}
          variant={BackgroundVariant.Dots}
        />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}

export function PipelineGraph(props: PipelineGraphProps) {
  return (
    <ReactFlowProvider>
      <PipelineGraphInner {...props} />
    </ReactFlowProvider>
  );
}
