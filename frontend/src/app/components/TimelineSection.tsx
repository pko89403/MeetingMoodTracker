import React, { useMemo } from "react";
import {
  ALL_AGENTS_FILTER,
  type MeetingAgent,
  type MeetingTurn,
  toAgentFilterValue,
} from "../../lib/meetingDashboard";
import { SectionState } from "./SectionState";
import { SelectedTurnPanel } from "./SelectedTurnPanel";
import { TimelineChart } from "./TimelineChart";
import { TurnTranscriptList } from "./TurnTranscriptList";

export type ChartView = "signals" | "emotions" | "sentiment" | "rubric";

interface TimelineSectionProps {
  turns: MeetingTurn[];
  filteredTurns: MeetingTurn[];
  agents: MeetingAgent[];
  selectedTurn: MeetingTurn | null;
  selectedTurnId: string | null;
  chartView: ChartView;
  selectedAgentFilter: string;
  turnsLoading: boolean;
  turnsEmpty: boolean;
  onSelectTurn: (turnId: string) => void;
  onClearSelectedTurn: () => void;
  onSelectAgentFilter: (agentFilter: string) => void;
  onSelectChartView: (view: ChartView) => void;
}

const CHART_TABS: Array<{ value: ChartView; label: string }> = [
  { value: "sentiment", label: "긍부정" },
  { value: "emotions", label: "기본 감정" },
  { value: "signals", label: "회의 시그널" },
  { value: "rubric", label: "종합 시그널" },
];

export function TimelineSection({
  turns,
  filteredTurns,
  agents,
  selectedTurn,
  selectedTurnId,
  chartView,
  selectedAgentFilter,
  turnsLoading,
  turnsEmpty,
  onSelectTurn,
  onClearSelectedTurn,
  onSelectAgentFilter,
  onSelectChartView,
}: TimelineSectionProps) {
  const selectedAgentLabel = useMemo(() => {
    if (selectedAgentFilter === ALL_AGENTS_FILTER) {
      return "전체 에이전트";
    }

    return (
      agents.find((agent) => toAgentFilterValue(agent.id) === selectedAgentFilter)?.label ??
      "선택된 에이전트"
    );
  }, [agents, selectedAgentFilter]);

  return (
    <section className="flex min-h-[500px] flex-1 flex-col">
      <div className="rounded-[28px] border border-slate-200/80 bg-white/90 p-5 shadow-[0_20px_50px_-28px_rgba(15,23,42,0.24)]">
        <div className="mb-5 flex flex-col gap-4">
          <div>
            <p className="text-xs font-semibold tracking-wide text-indigo-600">
              긍부정 · 기본 감정 · 회의 시그널 · 종합 시그널 timeline
            </p>
            <h2 className="mt-1 text-xl font-semibold tracking-tight text-slate-900">
              회의 흐름 탐색
            </h2>
          </div>

          <div className="w-full rounded-[24px] border border-slate-200 bg-slate-50/80 p-3">
            <div className="flex flex-col gap-3">
              <div className="inline-flex rounded-full border border-slate-200 bg-slate-100 p-1">
                {CHART_TABS.map((tab) => (
                  <button
                    key={tab.value}
                    type="button"
                    onClick={() => onSelectChartView(tab.value)}
                    className={`rounded-full px-4 py-2 text-xs font-semibold transition ${
                      chartView === tab.value
                        ? "bg-white text-indigo-700 shadow-sm"
                        : "text-slate-500 hover:text-slate-700"
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              <div className="flex flex-col gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-3 shadow-sm sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <p className="text-[11px] font-semibold tracking-wide text-slate-500">
                    에이전트 필터
                  </p>
                  <p className="mt-1 text-sm font-medium text-slate-700">{selectedAgentLabel}</p>
                </div>

                <div className="sm:w-[220px]">
                  <label className="sr-only" htmlFor="timeline-agent-filter">
                    에이전트 필터
                  </label>
                  <select
                    id="timeline-agent-filter"
                    value={selectedAgentFilter}
                    onChange={(event) => onSelectAgentFilter(event.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm font-medium text-slate-700 outline-none transition focus:border-indigo-300 focus:bg-white focus:ring-4 focus:ring-indigo-100"
                    aria-label="Filter turns by agent"
                  >
                    <option value={ALL_AGENTS_FILTER}>전체 에이전트</option>
                    {agents.map((agent) => (
                      <option
                        key={toAgentFilterValue(agent.id)}
                        value={toAgentFilterValue(agent.id)}
                      >
                        {agent.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="min-h-[420px] rounded-[24px] border border-slate-200 bg-white p-4">
          {turnsLoading && turns.length === 0 ? (
            <SectionState title="타임라인" message="timeline 데이터를 불러오는 중입니다." />
          ) : filteredTurns.length > 0 ? (
            <TimelineChart
              turns={filteredTurns}
              view={chartView}
              onSelectTurn={onSelectTurn}
              selectedTurnId={selectedTurnId}
            />
          ) : turnsEmpty ? (
            <SectionState title="타임라인" message="저장된 turn 데이터가 아직 없습니다." />
          ) : (
            <SectionState title="타임라인" message="선택한 필터에 해당하는 turn이 없습니다." />
          )}
        </div>

        <div className="mt-3 mb-4 flex flex-wrap items-center gap-2 text-sm text-slate-500">
          <span>
            {filteredTurns.length} / {turns.length} turns 표시 중
          </span>
          <span className="text-slate-300">·</span>
          <span>{selectedAgentLabel}</span>
        </div>

        {selectedTurn && (
          <div className="mt-4 hidden xl:block">
            <SelectedTurnPanel turn={selectedTurn} variant="inline" />
          </div>
        )}

        <TurnTranscriptList
          turns={filteredTurns}
          selectedTurnId={selectedTurnId}
          onSelectTurn={onSelectTurn}
          className="mt-4 xl:hidden"
        />
      </div>

      <SelectedTurnPanel turn={selectedTurn} variant="drawer" onClose={onClearSelectedTurn} />
    </section>
  );
}
