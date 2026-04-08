import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  Panel,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
} from "@xyflow/react";
import type { EdgeTypes, NodeTypes } from "@xyflow/react";
import { Search, Sparkles, Target, Waypoints } from "lucide-react";
import type { MeetingAgent, MeetingSummary, MeetingTurn } from "../../lib/meetingDashboard";
import { formatSentimentLabel } from "../../lib/meetingDashboard";
import { BrandMark } from "./BrandMark";
import { DashboardViewTabs, type DashboardView } from "./DashboardViewTabs";
import { MeetingDetailPanel } from "./MeetingDetailPanel";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
} from "./ui/command";
import { cn } from "./ui/utils";
import {
  AgentLaneBackdropNode,
  AgentLaneNode,
  GradientFlowEdge,
  MeetingHubNode,
  MetricSummaryNode,
  TurnInsightNode,
} from "./MeetingFlowNodes";
import { buildMeetingFlowGraph, turnNodeId } from "./meetingFlowGraph";

const nodeTypes = {
  meetingHub: MeetingHubNode,
  metricSummary: MetricSummaryNode,
  agentLaneBackdrop: AgentLaneBackdropNode,
  agentLane: AgentLaneNode,
  turnInsight: TurnInsightNode,
} satisfies NodeTypes;

const edgeTypes = {
  flowEdge: GradientFlowEdge,
} satisfies EdgeTypes;

function InfoCard({
  className,
  children,
  "data-testid": testId,
}: {
  className?: string;
  children: React.ReactNode;
  "data-testid"?: string;
}) {
  return (
    <div
      data-testid={testId}
      className={cn(
        "pointer-events-auto rounded-[24px] border border-white/10 bg-[#141416]/85 p-4 text-white shadow-[0_24px_80px_-40px_rgba(15,23,42,0.85)] backdrop-blur-xl",
        className,
      )}
    >
      {children}
    </div>
  );
}

function MeetingFlowScene({
  projectId,
  meetingId,
  summary,
  turns,
  agents,
  selectedTurnId,
  selectedAgentId,
  isLoading,
  errorMessages,
  onReset,
  onSelectTurn,
  onSelectAgent,
  view,
  onChangeView,
}: {
  projectId: string;
  meetingId: string;
  summary: MeetingSummary | null;
  turns: MeetingTurn[];
  agents: MeetingAgent[];
  selectedTurnId: string | null;
  selectedAgentId: string | null;
  isLoading: boolean;
  errorMessages: string[];
  onReset: () => void;
  onSelectTurn: (turnId: string) => void;
  onSelectAgent: (agentId: string | null) => void;
  view: DashboardView;
  onChangeView: (view: DashboardView) => void;
}) {
  const reactFlow = useReactFlow();
  const [commandOpen, setCommandOpen] = useState(false);

  const graph = useMemo(
    () =>
      buildMeetingFlowGraph({
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
      }),
    [
      agents,
      meetingId,
      onReset,
      onSelectAgent,
      onSelectTurn,
      projectId,
      selectedAgentId,
      selectedTurnId,
      summary,
      turns,
    ],
  );

  const selectedTurn =
    selectedTurnId === null ? null : turns.find((turn) => turn.turnId === selectedTurnId) ?? null;
  const selectedAgent =
    selectedAgentId === null ? null : agents.find((agent) => agent.id === selectedAgentId) ?? null;

  const focusNode = useCallback(
    (nodeId: string) => {
      const focusPosition = graph.focusPositions[nodeId];
      if (!focusPosition) {
        return;
      }

      reactFlow.setCenter(
        focusPosition.x + focusPosition.width / 2,
        focusPosition.y + focusPosition.height / 2,
        { duration: 500, zoom: 0.96 },
      );
    },
    [graph.focusPositions, reactFlow],
  );

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      reactFlow.fitView({
        duration: 500,
        padding: 0.12,
        minZoom: 0.58,
        maxZoom: 1.16,
      });
    });
    return () => {
      window.cancelAnimationFrame(frame);
    };
  }, [graph.nodes.length, reactFlow, selectedAgentId]);

  useEffect(() => {
    const handleKeyboard = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandOpen((open) => !open);
      }
    };

    window.addEventListener("keydown", handleKeyboard);
    return () => {
      window.removeEventListener("keydown", handleKeyboard);
    };
  }, []);

  return (
    <>
      <div className="h-screen w-full bg-[#050507] p-4 md:p-5 xl:p-7">
        <div
          data-testid="flow-dashboard-root"
          className="meeting-flow-shell relative h-full overflow-hidden rounded-[36px] border border-white/10 bg-[#09090c] shadow-[0_40px_120px_-60px_rgba(0,0,0,0.9)]"
        >
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(94,92,230,0.16),_transparent_28%),linear-gradient(180deg,rgba(255,255,255,0.03),transparent_24%)]" />
          <div
            data-testid="flow-stage-board"
            className="meeting-flow-board pointer-events-none absolute inset-4 rounded-[32px] border border-white/[0.07] bg-[linear-gradient(180deg,rgba(255,255,255,0.03),rgba(255,255,255,0.015))] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),inset_0_-1px_0_rgba(255,255,255,0.03)] md:inset-6 xl:left-1/2 xl:w-[calc(100%_-_56px)] xl:max-w-[1700px] xl:-translate-x-1/2"
          >
            <div className="absolute inset-x-0 top-[110px] h-px bg-white/[0.07]" />
            <div className="absolute inset-y-[110px] left-[22%] w-px bg-white/6" />
            <div className="absolute inset-y-[110px] left-[38%] w-px bg-white/5" />
            <div className="absolute inset-x-0 bottom-[24%] h-px bg-white/5" />
          </div>
          <ReactFlow
            className="meeting-flow-stage"
            nodes={graph.nodes}
            edges={graph.edges}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            fitView
            colorMode="dark"
            minZoom={0.42}
            maxZoom={1.26}
            nodesDraggable={false}
            elementsSelectable={false}
            proOptions={{ hideAttribution: true }}
            panOnDrag
            panOnScroll
            selectionOnDrag={false}
          >
            <Background
              variant={BackgroundVariant.Lines}
              gap={160}
              size={1}
              color="rgba(255,255,255,0.04)"
            />
            <Background
              variant={BackgroundVariant.Dots}
              gap={24}
              size={1}
              color="rgba(255,255,255,0.14)"
            />
            <MiniMap
              pannable
              zoomable
              nodeColor={() => "#1f1f24"}
              nodeStrokeColor={() => "#4f46e5"}
              maskColor="rgba(12,12,14,0.72)"
            />
            <Controls showInteractive={false} />

            <Panel
              position="top-center"
              style={{ width: "min(1380px, calc(100vw - 88px))" }}
            >
              <div className="pointer-events-none flex w-full flex-col gap-3 xl:flex-row xl:items-start">
                <InfoCard className="w-full xl:w-[320px]">
                  <BrandMark
                    className="mb-4"
                    size="sm"
                    subtitle="회의 감정 흐름을 추적하는 conversation intelligence"
                    testId="brand-mark-flow"
                    tone="light"
                  />
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-violet-200/70">
                        Meeting flow dashboard
                      </p>
                      <h1 className="mt-2 text-2xl font-medium tracking-tight text-white">
                        Structured flow board
                      </h1>
                      <div className="mt-4">
                        <DashboardViewTabs view={view} onChangeView={onChangeView} />
                      </div>
                    </div>
                    <button
                      type="button"
                      data-testid="flow-search-button"
                      onClick={() => setCommandOpen(true)}
                      className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/8 px-3 py-2 text-xs font-semibold text-slate-100 transition hover:bg-white/14"
                    >
                      <Search size={14} />
                      노드 검색
                    </button>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <span className="rounded-full border border-white/10 bg-white/8 px-3 py-1 text-xs font-medium text-slate-200">
                      {turns.length} total turns
                    </span>
                    <span className="rounded-full border border-white/10 bg-white/8 px-3 py-1 text-xs font-medium text-slate-200">
                      {agents.length} agent lanes
                    </span>
                    <span className="rounded-full border border-white/10 bg-white/8 px-3 py-1 text-xs font-medium text-slate-200">
                      Cmd / Ctrl + K
                    </span>
                  </div>
                  {errorMessages.length > 0 && (
                    <p className="mt-4 rounded-2xl border border-rose-400/20 bg-rose-500/10 px-3 py-2 text-sm text-rose-100">
                      {errorMessages.join(" / ")}
                    </p>
                  )}
                </InfoCard>

                <InfoCard className="w-full xl:w-[360px]">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-400">
                        Agent filter
                      </p>
                      <p className="mt-1 text-sm text-slate-300">
                        lane 단위로 turn graph와 mini chart를 함께 축소해서 볼 수 있습니다.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        onSelectAgent(null);
                        reactFlow.fitView({ duration: 400, padding: 0.12 });
                      }}
                      className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/8 px-3 py-2 text-xs font-semibold text-slate-100 transition hover:bg-white/14"
                    >
                      <Target size={14} />
                      전체 보기
                    </button>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <button
                      type="button"
                      data-testid="agent-filter-all"
                      aria-pressed={selectedAgentId === null}
                      onClick={() => onSelectAgent(null)}
                      className={cn(
                        "rounded-full border px-3 py-1.5 text-xs font-semibold transition",
                        selectedAgentId === null
                          ? "border-violet-400/60 bg-violet-500/20 text-white"
                          : "border-white/10 bg-white/6 text-slate-300 hover:bg-white/12",
                      )}
                    >
                      전체
                    </button>
                    {agents.map((agent) => (
                      <button
                        key={agent.id ?? "unassigned"}
                        type="button"
                        data-testid={`agent-filter-${agent.id ?? "unassigned"}`}
                        aria-pressed={selectedAgentId === agent.id}
                        onClick={() => onSelectAgent(agent.id)}
                        className={cn(
                          "rounded-full border px-3 py-1.5 text-xs font-semibold transition",
                          selectedAgentId === agent.id
                            ? "border-violet-400/60 bg-violet-500/20 text-white"
                            : "border-white/10 bg-white/6 text-slate-300 hover:bg-white/12",
                        )}
                      >
                        {agent.label}
                      </button>
                    ))}
                  </div>
                </InfoCard>
              </div>
            </Panel>

            <Panel position="bottom-left">
              <InfoCard className="w-[320px]">
                <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-400">
                  Flow legend
                </p>
                <div className="mt-4 space-y-3 text-sm text-slate-300">
                  <div className="flex items-center gap-3">
                    <span className="h-px w-12 bg-[linear-gradient(90deg,_#334155_0%,_#64748b_100%)]" />
                    <span>structure link</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="h-px w-12 bg-[linear-gradient(90deg,_#7c7cff_0%,_#c64aff_100%)]" />
                    <span>turn chronology</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <Waypoints size={14} className="text-violet-200" />
                    <span>turn 노드를 클릭하면 우측 detail panel이 전환됩니다.</span>
                  </div>
                </div>
              </InfoCard>
            </Panel>

              <Panel position="bottom-right">
              <MeetingDetailPanel
                summary={summary}
                turns={turns}
                selectedTurn={selectedTurn}
                selectedAgent={selectedAgent}
              />
            </Panel>

            {isLoading && (
              <Panel position="bottom-center">
                <InfoCard>
                  <div className="flex items-center gap-2 text-sm text-slate-200">
                    <Sparkles size={14} className="text-violet-300" />
                    회의 그래프를 불러오는 중입니다.
                  </div>
                </InfoCard>
              </Panel>
            )}
          </ReactFlow>
        </div>
      </div>

      <CommandDialog
        open={commandOpen}
        onOpenChange={setCommandOpen}
        title="노드 검색"
        description="turn 또는 agent를 검색해 해당 노드로 이동합니다."
      >
        <CommandInput placeholder="Turn, agent, sentiment..." />
        <CommandList>
          <CommandEmpty>검색 결과가 없습니다.</CommandEmpty>
          <CommandGroup heading="Agent lanes">
            {agents.map((agent) => (
              <CommandItem
                key={agent.id ?? "unassigned"}
                onSelect={() => {
                  setCommandOpen(false);
                  onSelectAgent(agent.id);
                  focusNode(`agent:${agent.id ?? "__unassigned_agent__"}`);
                }}
              >
                <span>{agent.label}</span>
                <CommandShortcut>{agent.turnCount} turns</CommandShortcut>
              </CommandItem>
            ))}
          </CommandGroup>
          <CommandSeparator />
          <CommandGroup heading="Turns">
            {turns.map((turn) => (
              <CommandItem
                key={turn.turnId}
                onSelect={() => {
                  setCommandOpen(false);
                  onSelectTurn(turn.turnId);
                  focusNode(turnNodeId(turn.turnId));
                }}
              >
                <span>{`Turn ${turn.order} · ${turn.agentLabel}`}</span>
                <CommandShortcut>{formatSentimentLabel(turn.sentimentLabel)}</CommandShortcut>
              </CommandItem>
            ))}
          </CommandGroup>
        </CommandList>
      </CommandDialog>
    </>
  );
}

export function MeetingFlowCanvas(props: {
  projectId: string;
  meetingId: string;
  summary: MeetingSummary | null;
  turns: MeetingTurn[];
  agents: MeetingAgent[];
  selectedTurnId: string | null;
  selectedAgentId: string | null;
  isLoading: boolean;
  errorMessages: string[];
  onReset: () => void;
  onSelectTurn: (turnId: string) => void;
  onSelectAgent: (agentId: string | null) => void;
  view: DashboardView;
  onChangeView: (view: DashboardView) => void;
}) {
  return (
    <ReactFlowProvider>
      <MeetingFlowScene {...props} />
    </ReactFlowProvider>
  );
}
