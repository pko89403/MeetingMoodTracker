import React from "react";
import {
  BaseEdge,
  type EdgeProps,
  Handle,
  type NodeProps,
  Position,
  getBezierPath,
  getSmoothStepPath,
} from "@xyflow/react";
import {
  formatSentimentLabel,
  type MeetingAgent,
  type MeetingSummary,
  type MeetingTurn,
} from "../../lib/meetingDashboard";
import { cn } from "./ui/utils";

export type FlowEdgeVariant = "relationship" | "timeline";

export type MeetingHubNodeData = {
  projectId: string;
  meetingId: string;
  summary: MeetingSummary | null;
  onReset: () => void;
  testId: string;
};

export type MetricSummaryNodeData = {
  eyebrow: string;
  title: string;
  value: string;
  detail: string;
  accent?: "violet" | "emerald" | "amber";
  testId: string;
};

export type AgentLaneBackdropNodeData = {
  agent: MeetingAgent;
  laneIndex: number;
  visibleTurnCount: number;
  width: number;
  active: boolean;
  testId: string;
};

export type AgentLaneNodeData = {
  agent: MeetingAgent;
  active: boolean;
  onSelectAgent: (agentId: string | null) => void;
  testId: string;
};

export type TurnInsightNodeData = {
  turn: MeetingTurn;
  active: boolean;
  dimmed: boolean;
  onSelectTurn: (turnId: string) => void;
  testId: string;
};

export type FlowEdgeData = {
  variant?: FlowEdgeVariant;
};

function NodeShell({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-[28px] border border-white/10 bg-white/[0.05] shadow-[0_24px_80px_-40px_rgba(15,23,42,0.85)] backdrop-blur-xl",
        className,
      )}
    >
      {children}
    </div>
  );
}

function NodeHandle({ type, position }: { type: "source" | "target"; position: Position }) {
  return (
    <Handle
      type={type}
      position={position}
      className="!size-3 !border !border-white/20 !bg-violet-400/90"
    />
  );
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-[11px] font-medium text-slate-300">
        <span>{label}</span>
        <span>{value}</span>
      </div>
      <div className="h-1.5 rounded-full bg-white/8">
        <div
          className="h-full rounded-full bg-[linear-gradient(90deg,_#5e5ce6_0%,_#c64aff_100%)]"
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

export function MeetingHubNode({ data }: NodeProps<MeetingHubNodeData>) {
  return (
    <NodeShell className="w-[300px] p-5">
      <NodeHandle type="source" position={Position.Right} />
      <div data-testid={data.testId}>
        <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-violet-200/70">
          Meeting flow canvas
        </p>
        <h2 className="mt-3 text-[26px] font-medium tracking-tight text-white">
          {data.summary?.title ?? `Meeting ${data.meetingId}`}
        </h2>
        <p className="mt-3 text-sm leading-6 text-slate-300">
          {data.summary?.oneLineSummary ?? "회의 요약이 아직 생성되지 않았습니다."}
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <span className="rounded-full border border-white/10 bg-white/8 px-3 py-1 text-xs font-medium text-slate-200">
            {data.projectId}
          </span>
          <span className="rounded-full border border-white/10 bg-white/8 px-3 py-1 text-xs font-medium text-slate-200">
            {data.meetingId}
          </span>
        </div>
        <button
          type="button"
          onClick={data.onReset}
          className="nodrag nopan pointer-events-auto mt-5 inline-flex items-center rounded-full border border-white/12 bg-white/8 px-4 py-2 text-xs font-semibold text-white transition hover:bg-white/14"
        >
          다른 회의 열기
        </button>
      </div>
    </NodeShell>
  );
}

export function AgentLaneBackdropNode({ data }: NodeProps<AgentLaneBackdropNodeData>) {
  return (
    <div
      data-testid={data.testId}
      style={{ width: data.width }}
      className={cn(
        "pointer-events-none relative min-h-[286px] overflow-hidden rounded-[34px] border px-6 py-5 shadow-[0_30px_90px_-55px_rgba(15,23,42,0.85)]",
        data.active
          ? "border-violet-400/28 bg-[linear-gradient(90deg,_rgba(94,92,230,0.14)_0%,_rgba(15,23,42,0.18)_34%,_rgba(198,74,255,0.08)_100%)]"
          : "border-white/8 bg-[linear-gradient(90deg,_rgba(255,255,255,0.05)_0%,_rgba(15,23,42,0.12)_34%,_rgba(255,255,255,0.03)_100%)]",
      )}
    >
      <div className="absolute inset-y-0 left-[286px] w-px bg-white/8" />
      <div className="absolute inset-x-0 top-[68px] h-px bg-white/8" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_left,_rgba(255,255,255,0.08),_transparent_42%)] opacity-60" />
      <div className="relative flex items-start justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-400">
            Lane {String(data.laneIndex + 1).padStart(2, "0")}
          </p>
          <h3 className="mt-2 text-xl font-medium text-white">{data.agent.label}</h3>
        </div>
        <div className="rounded-full border border-white/10 bg-white/8 px-3 py-1 text-[11px] font-semibold text-slate-200">
          {data.visibleTurnCount} visible turns
        </div>
      </div>
      <div className="relative mt-6 flex items-center justify-between gap-4 text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">
        <span>Agent context</span>
        <span>Turn chronology</span>
      </div>
    </div>
  );
}

export function MetricSummaryNode({ data }: NodeProps<MetricSummaryNodeData>) {
  const accentClasses =
    data.accent === "emerald"
      ? "from-emerald-400/20 to-emerald-300/0 text-emerald-100"
      : data.accent === "amber"
        ? "from-amber-400/20 to-amber-300/0 text-amber-100"
        : "from-violet-500/20 to-fuchsia-400/0 text-violet-100";

  return (
    <NodeShell className="w-[230px] overflow-hidden">
      <NodeHandle type="target" position={Position.Left} />
      <div
        data-testid={data.testId}
        className={cn("bg-gradient-to-br p-4", accentClasses)}
      >
        <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-current/70">
          {data.eyebrow}
        </p>
        <h3 className="mt-2 text-lg font-medium text-white">{data.title}</h3>
        <p className="mt-4 text-[24px] font-medium tracking-tight text-white">{data.value}</p>
        <p className="mt-2 text-sm leading-6 text-slate-300">{data.detail}</p>
      </div>
    </NodeShell>
  );
}

export function AgentLaneNode({ data }: NodeProps<AgentLaneNodeData>) {
  return (
    <button
      type="button"
      data-testid={data.testId}
      onClick={() => data.onSelectAgent(data.agent.id)}
      className={cn(
        "nodrag nopan pointer-events-auto block w-[238px] rounded-[28px] border p-4 text-left shadow-[0_24px_80px_-40px_rgba(15,23,42,0.8)] backdrop-blur-xl transition",
        data.active
          ? "border-violet-400/70 bg-[linear-gradient(180deg,_rgba(94,92,230,0.22)_0%,_rgba(22,22,24,0.96)_100%)]"
          : "border-white/10 bg-white/[0.04] hover:border-white/20 hover:bg-white/[0.06]",
      )}
    >
      <NodeHandle type="target" position={Position.Left} />
      <NodeHandle type="source" position={Position.Right} />
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">
            Agent lane
          </p>
          <h3 className="mt-2 text-lg font-medium text-white">{data.agent.label}</h3>
        </div>
        <span className="rounded-full border border-white/10 bg-white/8 px-3 py-1 text-[11px] font-semibold text-slate-200">
          {data.agent.turnCount} turns
        </span>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <span className="rounded-full border border-white/10 bg-white/8 px-2.5 py-1 text-xs text-slate-200">
          {data.agent.primaryEmotion}
        </span>
        <span className="rounded-full border border-white/10 bg-white/8 px-2.5 py-1 text-xs text-slate-200">
          {data.agent.primarySignal}
        </span>
      </div>
      <p className="mt-4 line-clamp-3 text-sm leading-6 text-slate-300">{data.agent.summary}</p>
    </button>
  );
}

export function TurnInsightNode({ data }: NodeProps<TurnInsightNodeData>) {
  return (
    <button
      type="button"
      data-testid={data.testId}
      onClick={() => data.onSelectTurn(data.turn.turnId)}
      className={cn(
        "nodrag nopan pointer-events-auto block w-[252px] rounded-[28px] border p-4 text-left shadow-[0_24px_80px_-40px_rgba(15,23,42,0.8)] backdrop-blur-xl transition",
        data.active
          ? "border-fuchsia-400/70 bg-[linear-gradient(180deg,_rgba(198,74,255,0.2)_0%,_rgba(17,24,39,0.96)_100%)]"
          : "border-white/10 bg-white/[0.04] hover:border-white/20 hover:bg-white/[0.06]",
        data.dimmed ? "opacity-65" : "opacity-100",
      )}
    >
      <NodeHandle type="target" position={Position.Left} />
      <NodeHandle type="source" position={Position.Right} />
      <div className="flex items-center justify-between gap-3">
        <span className="rounded-full border border-white/10 bg-white/8 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-200">
          Turn {data.turn.order}
        </span>
        <span className="text-xs font-medium text-slate-400">{data.turn.agentLabel}</span>
      </div>

      <p className="mt-4 line-clamp-3 text-[13px] leading-6 text-slate-100">{data.turn.text}</p>

      <div className="mt-4 flex flex-wrap gap-2 text-xs">
        <span className="rounded-full border border-white/10 bg-white/8 px-2.5 py-1 text-slate-200">
          {formatSentimentLabel(data.turn.sentimentLabel)} {Math.round(data.turn.sentimentConfidence * 100)}%
        </span>
        <span className="rounded-full border border-white/10 bg-white/8 px-2.5 py-1 text-slate-200">
          {data.turn.dominantSignal}
        </span>
        <span className="rounded-full border border-white/10 bg-white/8 px-2.5 py-1 text-slate-200">
          {data.turn.dominantEmotion}
        </span>
      </div>

      <div className="mt-4 space-y-3">
        <ScoreBar label="Dominance" value={data.turn.rubric.dominance} />
        <ScoreBar label="Efficiency" value={data.turn.rubric.efficiency} />
        <ScoreBar label="Cohesion" value={data.turn.rubric.cohesion} />
      </div>
    </button>
  );
}

export function GradientFlowEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
}: EdgeProps<FlowEdgeData>) {
  const variant = data?.variant ?? "relationship";
  const [edgePath] =
    variant === "timeline"
      ? getSmoothStepPath({
          sourceX,
          sourceY,
          targetX,
          targetY,
          sourcePosition,
          targetPosition,
          borderRadius: 22,
          offset: 24,
        })
      : getBezierPath({
          sourceX,
          sourceY,
          targetX,
          targetY,
          sourcePosition,
          targetPosition,
        });
  const gradientId = `flow-gradient-${id}`;
  const isTimeline = variant === "timeline";

  return (
    <>
      <defs>
        <linearGradient id={gradientId} gradientUnits="userSpaceOnUse" x1={sourceX} y1={sourceY} x2={targetX} y2={targetY}>
          <stop offset="0%" stopColor={isTimeline ? "#7c7cff" : "#334155"} />
          <stop offset="100%" stopColor={isTimeline ? "#c64aff" : "#64748b"} />
        </linearGradient>
      </defs>
      <BaseEdge
        path={edgePath}
        style={{
          stroke: `url(#${gradientId})`,
          strokeWidth: isTimeline ? 3.2 : 1.2,
          opacity: isTimeline ? 0.95 : 0.38,
          strokeDasharray: isTimeline ? "14 12" : "4 12",
          animation: isTimeline ? "flow-edge-dash 14s linear infinite" : undefined,
        }}
      />
    </>
  );
}
