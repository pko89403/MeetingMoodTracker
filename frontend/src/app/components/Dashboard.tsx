import React, { useEffect, useMemo, useState } from "react";
import {
  useMeetingAgents,
  useMeetingOverview,
  useMeetingTurns,
} from "../../hooks/useMeeting";
import { MeetingTurn } from "../../lib/meetingDashboard";
import { MeetingFlowCanvas } from "./MeetingFlowCanvas";
import { type DashboardView } from "./DashboardViewTabs";
import { MeetingTimelinePage } from "./MeetingTimelinePage";

interface DashboardProps {
  projectId: string;
  meetingId: string;
  onReset: () => void;
  view: DashboardView;
  onChangeView: (view: DashboardView) => void;
}

function filterTurns(turns: MeetingTurn[], selectedAgentId: string | null) {
  return turns.filter((turn) => {
    if (selectedAgentId !== null && turn.agentId !== selectedAgentId) {
      return false;
    }
    return true;
  });
}

export function Dashboard({
  projectId,
  meetingId,
  onReset,
  view,
  onChangeView,
}: DashboardProps) {
  const [selectedTurnId, setSelectedTurnId] = useState<string | null>(null);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);

  const summaryState = useMeetingOverview(projectId, meetingId);
  const turnsState = useMeetingTurns(projectId, meetingId);
  const agentsState = useMeetingAgents(projectId, meetingId);

  const summary = summaryState.data;
  const turns = turnsState.data ?? [];
  const agents = agentsState.data ?? [];

  const filteredTurns = useMemo(
    () => filterTurns(turns, selectedAgentId),
    [selectedAgentId, turns]
  );

  const errorMessages = [summaryState.error, turnsState.error, agentsState.error].filter(Boolean);
  const isLoading = summaryState.loading || turnsState.loading || agentsState.loading;

  useEffect(() => {
    if (filteredTurns.length === 0) {
      if (selectedTurnId !== null) {
        setSelectedTurnId(null);
      }
      return;
    }

    if (selectedTurnId && filteredTurns.some((turn) => turn.turnId === selectedTurnId)) {
      return;
    }

    setSelectedTurnId(filteredTurns[0].turnId);
  }, [filteredTurns, selectedTurnId]);

  const sharedPageProps = {
    summary,
    turns,
    agents,
    selectedTurnId,
    selectedAgentId,
    isLoading,
    errorMessages,
    onReset,
    onSelectTurn: setSelectedTurnId,
    onSelectAgent: (agentId: string | null) => {
      setSelectedAgentId(agentId);
      setSelectedTurnId(null);
    },
    view,
    onChangeView,
  };

  return (
    <div className="min-h-screen bg-[#0c0c0e] font-sans text-white">
      {view === "timeline" ? (
        <MeetingTimelinePage {...sharedPageProps} />
      ) : (
        <MeetingFlowCanvas
          projectId={projectId}
          meetingId={meetingId}
          {...sharedPageProps}
        />
      )}
    </div>
  );
}
