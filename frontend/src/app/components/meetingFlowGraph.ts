import { MarkerType, type Edge, type Node } from "@xyflow/react";
import {
  formatSentimentLabel,
  type MeetingAgent,
  type MeetingSummary,
  type MeetingTurn,
  toAgentFilterValue,
  UNASSIGNED_AGENT_FILTER,
} from "../../lib/meetingDashboard";
import type {
  AgentLaneBackdropNodeData,
  AgentLaneNodeData,
  FlowEdgeData,
  MeetingHubNodeData,
  MetricSummaryNodeData,
  TurnInsightNodeData,
} from "./MeetingFlowNodes";

type FlowNodeData =
  | MeetingHubNodeData
  | MetricSummaryNodeData
  | AgentLaneBackdropNodeData
  | AgentLaneNodeData
  | TurnInsightNodeData;

type FocusPosition = {
  x: number;
  y: number;
  width: number;
  height: number;
};

export type MeetingFlowGraph = {
  nodes: Node<FlowNodeData>[];
  edges: Edge<FlowEdgeData>[];
  focusPositions: Record<string, FocusPosition>;
};

const HUB_WIDTH = 300;
const HUB_HEIGHT = 250;
const METRIC_WIDTH = 230;
const METRIC_HEIGHT = 168;
const LANE_BAND_X = 820;
const LANE_BAND_PADDING = 120;
const AGENT_NODE_X = 860;
const AGENT_NODE_WIDTH = 238;
const AGENT_NODE_HEIGHT = 206;
const TURN_START_X = 1180;
const TURN_NODE_WIDTH = 252;
const TURN_NODE_HEIGHT = 258;
const TURN_GAP = 288;
const LANE_BASE_Y = 180;
const LANE_GAP = 320;

function agentNodeId(agentId: string | null | undefined) {
  return `agent:${agentId ?? UNASSIGNED_AGENT_FILTER}`;
}

function laneBackdropNodeId(agentId: string | null | undefined) {
  return `lane:${agentId ?? UNASSIGNED_AGENT_FILTER}`;
}

export function turnNodeId(turnId: string) {
  return `turn:${turnId}`;
}

function registerFocusPosition(
  focusPositions: Record<string, FocusPosition>,
  nodeId: string,
  x: number,
  y: number,
  width: number,
  height: number,
) {
  focusPositions[nodeId] = { x, y, width, height };
}

function buildTurnSentimentText(summary: MeetingSummary | null) {
  if (!summary) {
    return "긍정 0 · 중립 0 · 부정 0";
  }

  return `긍정 ${summary.sentimentDist.pos} · 중립 ${summary.sentimentDist.neu} · 부정 ${summary.sentimentDist.neg}`;
}

function buildRubricText(summary: MeetingSummary | null) {
  if (!summary) {
    return "Dominance 0 · Efficiency 0 · Cohesion 0";
  }

  return `Dominance ${summary.rubric.dominance} · Efficiency ${summary.rubric.efficiency} · Cohesion ${summary.rubric.cohesion}`;
}

export function buildMeetingFlowGraph(options: {
  projectId: string;
  meetingId: string;
  summary: MeetingSummary | null;
  turns: MeetingTurn[];
  agents: MeetingAgent[];
  selectedTurnId: string | null;
  selectedAgentId: string | null;
  onReset: () => void;
  onSelectAgent: (agentId: string | null) => void;
  onSelectTurn: (turnId: string) => void;
}): MeetingFlowGraph {
  const {
    projectId,
    meetingId,
    summary,
    turns,
    agents,
    selectedTurnId,
    selectedAgentId,
    onReset,
    onSelectAgent,
    onSelectTurn,
  } = options;

  const visibleTurns =
    selectedAgentId === null
      ? turns
      : turns.filter((turn) => toAgentFilterValue(turn.agentId) === selectedAgentId);

  const unassignedTurns = visibleTurns.filter((turn) => !turn.agentId);
  const visibleAgents =
    selectedAgentId === null
      ? [
          ...agents,
          ...(unassignedTurns.length > 0 && agents.every((agent) => agent.id !== null)
            ? [
                {
                  id: null,
                  label: "미배정 Agent",
                  turnCount: unassignedTurns.length,
                  turnIds: unassignedTurns.map((turn) => turn.turnId),
                  avgSentiment: { pos: 0, neu: 100, neg: 0 },
                  primaryEmotion: "N/A",
                  primarySignal: "N/A",
                  emergingEmotions: [],
                  summary: "아직 에이전트에 연결되지 않은 turn입니다.",
                } satisfies MeetingAgent,
              ]
            : []),
        ]
      : agents.filter((agent) => toAgentFilterValue(agent.id) === selectedAgentId);

  const nodes: Node<FlowNodeData>[] = [];
  const edges: Edge<FlowEdgeData>[] = [];
  const focusPositions: Record<string, FocusPosition> = {};
  const laneIndexByAgent = new Map<string, number>();

  const centerY = LANE_BASE_Y + Math.max(0, (visibleAgents.length - 1) * LANE_GAP * 0.5);
  const laneBandWidth =
    visibleTurns.length === 0
      ? 920
      : TURN_START_X + (visibleTurns.length - 1) * TURN_GAP + TURN_NODE_WIDTH - LANE_BAND_X + LANE_BAND_PADDING;
  const meetingNodeX = 160;
  const meetingNodeY = Math.max(160, centerY - 160);
  const metricX = 500;
  const metricNodes = [
    {
      id: "metric:overview",
      x: metricX,
      y: Math.max(96, centerY - 226),
      data: {
        eyebrow: "Overview",
        title: "Session density",
        value: `${summary?.totalTurns ?? turns.length} turns`,
        detail: `${summary?.totalAgents ?? agents.length} agents · ${summary?.topics.length ?? 0} topics`,
        accent: "violet",
        testId: "flow-metric-overview",
      } satisfies MetricSummaryNodeData,
    },
    {
      id: "metric:sentiment",
      x: metricX,
      y: Math.max(288, centerY - 22),
      data: {
        eyebrow: "Sentiment",
        title: "Conversation tone",
        value:
          summary?.dominantEmotion ??
          (visibleTurns[0] ? formatSentimentLabel(visibleTurns[0].sentimentLabel) : "N/A"),
        detail: buildTurnSentimentText(summary),
        accent: "emerald",
        testId: "flow-metric-sentiment",
      } satisfies MetricSummaryNodeData,
    },
    {
      id: "metric:rubric",
      x: metricX,
      y: Math.max(480, centerY + 182),
      data: {
        eyebrow: "Rubric",
        title: "Signal synthesis",
        value: summary?.dominantSignal ?? "N/A",
        detail: buildRubricText(summary),
        accent: "amber",
        testId: "flow-metric-rubric",
      } satisfies MetricSummaryNodeData,
    },
  ];

  nodes.push({
    id: "meeting:hub",
    type: "meetingHub",
    position: { x: meetingNodeX, y: meetingNodeY },
    data: {
      projectId,
      meetingId,
      summary,
      onReset,
      testId: "meeting-hub-node",
    },
  });
  registerFocusPosition(focusPositions, "meeting:hub", meetingNodeX, meetingNodeY, HUB_WIDTH, HUB_HEIGHT);

  for (const metricNode of metricNodes) {
    nodes.push({
      id: metricNode.id,
      type: "metricSummary",
      position: { x: metricNode.x, y: metricNode.y },
      data: metricNode.data,
    });
    registerFocusPosition(focusPositions, metricNode.id, metricNode.x, metricNode.y, METRIC_WIDTH, METRIC_HEIGHT);
    edges.push({
      id: `meeting:hub-${metricNode.id}`,
      source: "meeting:hub",
      target: metricNode.id,
      type: "flowEdge",
      data: { variant: "relationship" },
      markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16, color: "#64748b" },
    });
  }

  visibleAgents.forEach((agent, index) => {
    const laneKey = toAgentFilterValue(agent.id);
    const laneTurns = visibleTurns
      .filter((turn) => toAgentFilterValue(turn.agentId) === laneKey)
      .sort((left, right) => left.order - right.order);
    const laneY = LANE_BASE_Y + index * LANE_GAP;
    const laneNodeId = laneBackdropNodeId(agent.id);
    const agentNode = agentNodeId(agent.id);

    laneIndexByAgent.set(laneKey, index);

    nodes.push({
      id: laneNodeId,
      type: "agentLaneBackdrop",
      position: { x: LANE_BAND_X, y: laneY - 30 },
      selectable: false,
      draggable: false,
      deletable: false,
      focusable: false,
      zIndex: -5,
      data: {
        agent,
        laneIndex: index,
        visibleTurnCount: laneTurns.length,
        width: laneBandWidth,
        active: selectedAgentId !== null && laneKey === selectedAgentId,
        testId: `lane-band-${laneKey}`,
      },
    });

    nodes.push({
      id: agentNode,
      type: "agentLane",
      position: { x: AGENT_NODE_X, y: laneY + 26 },
      data: {
        agent,
        active: selectedAgentId !== null && laneKey === selectedAgentId,
        onSelectAgent,
        testId: `agent-node-${laneKey}`,
      },
    });

    registerFocusPosition(focusPositions, agentNode, AGENT_NODE_X, laneY + 26, AGENT_NODE_WIDTH, AGENT_NODE_HEIGHT);
    edges.push({
      id: `meeting:hub-${agentNode}`,
      source: "meeting:hub",
      target: agentNode,
      type: "flowEdge",
      data: { variant: "relationship" },
      markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16, color: "#64748b" },
    });
  });

  const sortedTurns = [...visibleTurns].sort((left, right) => left.order - right.order);
  sortedTurns.forEach((turn, index) => {
    const laneKey = toAgentFilterValue(turn.agentId);
    const laneIndex = laneIndexByAgent.get(laneKey) ?? 0;
    const x = TURN_START_X + index * TURN_GAP;
    const y = LANE_BASE_Y + laneIndex * LANE_GAP + 14;
    const nodeId = turnNodeId(turn.turnId);

    nodes.push({
      id: nodeId,
      type: "turnInsight",
      position: { x, y },
      data: {
        turn,
        active: selectedTurnId === turn.turnId,
        dimmed: selectedTurnId !== null && selectedTurnId !== turn.turnId,
        onSelectTurn,
        testId: `turn-node-${turn.order}`,
      },
    });
    registerFocusPosition(focusPositions, nodeId, x, y, TURN_NODE_WIDTH, TURN_NODE_HEIGHT);

    edges.push({
      id: `${agentNodeId(turn.agentId)}-${nodeId}`,
      source: agentNodeId(turn.agentId),
      target: nodeId,
      type: "flowEdge",
      data: { variant: "relationship" },
      markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16, color: "#64748b" },
    });

    if (index > 0) {
      edges.push({
        id: `${turnNodeId(sortedTurns[index - 1].turnId)}-${nodeId}`,
        source: turnNodeId(sortedTurns[index - 1].turnId),
        target: nodeId,
        type: "flowEdge",
        data: { variant: "timeline" },
        markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16, color: "#c64aff" },
      });
    }
  });

  return {
    nodes,
    edges,
    focusPositions,
  };
}
