import React from "react";
import { BarChart3, RefreshCcw } from "lucide-react";
import type { MeetingAgent, MeetingSummary, MeetingTurn } from "../../lib/meetingDashboard";
import { BrandMark } from "./BrandMark";
import { DashboardViewTabs, type DashboardView } from "./DashboardViewTabs";
import { MeetingDetailPanel } from "./MeetingDetailPanel";
import { MeetingFlowMiniChart } from "./MeetingFlowMiniChart";
import { cn } from "./ui/utils";

export function MeetingTimelinePage({
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
  const selectedTurn =
    selectedTurnId === null ? null : turns.find((turn) => turn.turnId === selectedTurnId) ?? null;
  const selectedAgent =
    selectedAgentId === null ? null : agents.find((agent) => agent.id === selectedAgentId) ?? null;
  const visibleTurns =
    selectedAgentId === null ? turns : turns.filter((turn) => turn.agentId === selectedAgentId);

  return (
    <div className="min-h-screen bg-[#050507] px-4 py-4 md:px-5 md:py-5 xl:px-7 xl:py-7">
      <div
        className="mx-auto flex min-h-[calc(100vh-2rem)] max-w-[1700px] flex-col gap-4 rounded-[36px] border border-white/10 bg-[#09090c] p-4 shadow-[0_40px_120px_-60px_rgba(0,0,0,0.9)] md:p-6"
        data-testid="timeline-page-root"
      >
        <section className="rounded-[28px] border border-white/10 bg-[#141416]/85 p-5 shadow-[0_24px_80px_-40px_rgba(15,23,42,0.85)] backdrop-blur-xl">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
            <div>
              <BrandMark
                className="mb-4"
                size="sm"
                subtitle="회의 감정 흐름을 읽는 timeline intelligence surface"
                testId="brand-mark-timeline"
                tone="light"
              />
              <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.28em] text-violet-200/70">
                <BarChart3 size={13} />
                Timeline explorer
              </div>
              <h1 className="mt-2 text-3xl font-medium tracking-tight text-white">
                {summary?.title ?? "Meeting timeline"}
              </h1>
              <p className="mt-2 max-w-3xl text-sm leading-7 text-slate-300">
                감정, 회의 시그널, 종합 시그널의 흐름을 메인 화면으로 분리했습니다. Flow 보드는 관계 탐색에, Timeline은 시계열 분석에 집중합니다.
              </p>
              <div className="mt-4">
                <DashboardViewTabs view={view} onChangeView={onChangeView} />
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-white/10 bg-white/8 px-3 py-1 text-xs font-medium text-slate-200">
                {visibleTurns.length} visible turns
              </span>
              <span className="rounded-full border border-white/10 bg-white/8 px-3 py-1 text-xs font-medium text-slate-200">
                {agents.length} agent lanes
              </span>
              <button
                type="button"
                onClick={onReset}
                className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/8 px-3 py-2 text-xs font-semibold text-slate-100 transition hover:bg-white/14"
              >
                <RefreshCcw size={14} />
                다른 회의 열기
              </button>
            </div>
          </div>
        </section>

        <section className="grid flex-1 gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
          <div className="flex min-h-0 flex-col gap-4">
            <div className="rounded-[28px] border border-white/10 bg-[#141416]/85 p-4 shadow-[0_24px_80px_-40px_rgba(15,23,42,0.85)] backdrop-blur-xl">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-400">
                    Agent filter
                  </p>
                  <p className="mt-1 text-sm text-slate-300">
                    timeline은 현재 선택된 agent lane 기준으로 좁혀서 볼 수 있습니다.
                  </p>
                </div>
                {errorMessages.length > 0 && (
                  <p className="rounded-2xl border border-rose-400/20 bg-rose-500/10 px-3 py-2 text-sm text-rose-100">
                    {errorMessages.join(" / ")}
                  </p>
                )}
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
            </div>

            <MeetingFlowMiniChart
              turns={visibleTurns}
              selectedTurnId={selectedTurnId}
              selectedAgentLabel={selectedAgent?.label}
              isLoading={isLoading}
              onSelectTurn={onSelectTurn}
              variant="page"
              testId="timeline-page-chart"
            />
          </div>

          <aside className="min-h-0">
            <MeetingDetailPanel
              summary={summary}
              turns={turns}
              selectedTurn={selectedTurn}
              selectedAgent={selectedAgent}
              mode="timeline"
            />
          </aside>
        </section>
      </div>
    </div>
  );
}
