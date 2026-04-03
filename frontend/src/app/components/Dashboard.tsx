import React, { useEffect, useMemo, useState } from "react";
import { Header } from "./Header";
import { MeetingSummarySection } from "./MeetingSummarySection";
import { TimelineSection, type ChartView } from "./TimelineSection";
import { TurnTranscriptList } from "./TurnTranscriptList";
import {
  useMeetingAgents,
  useMeetingOverview,
  useMeetingTurns,
} from "../../hooks/useMeeting";
import {
  ALL_AGENTS_FILTER,
  MeetingTurn,
  toAgentFilterValue,
} from "../../lib/meetingDashboard";

interface DashboardProps {
  projectId: string;
  meetingId: string;
  onReset: () => void;
}

function filterTurns(turns: MeetingTurn[], selectedAgentFilter: string) {
  return turns.filter((turn) => {
    if (
      selectedAgentFilter !== ALL_AGENTS_FILTER &&
      toAgentFilterValue(turn.agentId) !== selectedAgentFilter
    ) {
      return false;
    }
    return true;
  });
}

export function Dashboard({ projectId, meetingId, onReset }: DashboardProps) {
  const [selectedTurnId, setSelectedTurnId] = useState<string | null>(null);
  const [chartView, setChartView] = useState<ChartView>("sentiment");
  const [selectedAgentFilter, setSelectedAgentFilter] = useState<string>(ALL_AGENTS_FILTER);

  const summaryState = useMeetingOverview(projectId, meetingId);
  const turnsState = useMeetingTurns(projectId, meetingId);
  const agentsState = useMeetingAgents(projectId, meetingId);

  const summary = summaryState.data;
  const turns = turnsState.data ?? [];
  const agents = agentsState.data ?? [];

  const filteredTurns = useMemo(
    () => filterTurns(turns, selectedAgentFilter),
    [selectedAgentFilter, turns]
  );

  const errorMessages = [summaryState.error, turnsState.error, agentsState.error].filter(Boolean);
  const isLoading = summaryState.loading || turnsState.loading || agentsState.loading;

  useEffect(() => {
    if (!selectedTurnId) {
      return;
    }

    const existsInFilteredTurns = filteredTurns.some((turn) => turn.turnId === selectedTurnId);
    if (!existsInFilteredTurns) {
      setSelectedTurnId(null);
    }
  }, [filteredTurns, selectedTurnId]);

  useEffect(() => {
    if (selectedTurnId || filteredTurns.length === 0) {
      return;
    }

    setSelectedTurnId(filteredTurns[0].turnId);
  }, [filteredTurns, selectedTurnId]);

  const selectedTurn = selectedTurnId
    ? turns.find((turn) => turn.turnId === selectedTurnId) ?? null
    : null;

  const summaryFallback = {
    totalTurns: turns.length,
    totalAgents: agents.length,
  };

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,_#f8fafc_0%,_#f1f5f9_100%)] text-slate-900 flex flex-col font-sans">
      <Header
        projectId={projectId}
        meetingId={meetingId}
        summary={summary}
        onReset={onReset}
      />

      <main className="mx-auto flex w-full max-w-[1400px] flex-1 gap-6 px-4 py-4 lg:px-6 lg:py-6">
        <div className="flex-1 overflow-y-auto pb-20">
          <div className="flex flex-col space-y-6 lg:space-y-8">
            {errorMessages.length > 0 && !isLoading && (
              <section
                className="rounded-[24px] border border-rose-200 bg-[linear-gradient(180deg,_rgba(255,241,242,1)_0%,_rgba(255,251,251,1)_100%)] px-5 py-4 text-rose-800 shadow-[0_16px_40px_-28px_rgba(225,29,72,0.5)]"
                role="alert"
              >
                <h2 className="text-sm font-semibold mb-1">일부 회의 데이터를 불러오지 못했습니다.</h2>
                <p className="text-sm leading-6">{errorMessages.join(" / ")}</p>
              </section>
            )}

            <MeetingSummarySection
              summary={summary}
              isLoading={isLoading}
              fallback={summaryFallback}
            />

            <TimelineSection
              turns={turns}
              filteredTurns={filteredTurns}
              agents={agents}
              selectedTurn={selectedTurn}
              selectedTurnId={selectedTurnId}
              chartView={chartView}
              selectedAgentFilter={selectedAgentFilter}
              turnsLoading={turnsState.loading}
              turnsEmpty={turnsState.empty}
              onSelectTurn={setSelectedTurnId}
              onClearSelectedTurn={() => setSelectedTurnId(null)}
              onSelectAgentFilter={setSelectedAgentFilter}
              onSelectChartView={setChartView}
            />

          </div>
        </div>

        <aside className="hidden w-[420px] flex-shrink-0 xl:block">
          <div className="sticky top-[138px] max-h-[calc(100vh-160px)]">
            <TurnTranscriptList
              turns={filteredTurns}
              selectedTurnId={selectedTurnId}
              onSelectTurn={setSelectedTurnId}
              compact
              className="h-[calc(100vh-160px)] shadow-[0_20px_50px_-28px_rgba(15,23,42,0.24)]"
            />
          </div>
        </aside>
      </main>
    </div>
  );
}
