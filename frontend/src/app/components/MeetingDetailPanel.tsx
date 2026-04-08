import React from "react";
import type { MeetingAgent, MeetingSummary, MeetingTurn } from "../../lib/meetingDashboard";
import { formatSentimentLabel } from "../../lib/meetingDashboard";

function ScorePill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/6 px-3 py-2">
      <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">{label}</p>
      <p className="mt-1 text-sm font-medium text-slate-100">{value}</p>
    </div>
  );
}

function ScoreMeter({ label, value }: { label: string; value: number }) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs font-medium text-slate-300">
        <span>{label}</span>
        <span>{value}</span>
      </div>
      <div className="h-2 rounded-full bg-white/8">
        <div
          className="h-full rounded-full bg-[linear-gradient(90deg,_#5e5ce6_0%,_#c64aff_100%)]"
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

export function MeetingDetailPanel({
  summary,
  turns,
  selectedTurn,
  selectedAgent,
  mode = "flow",
}: {
  summary: MeetingSummary | null;
  turns: MeetingTurn[];
  selectedTurn: MeetingTurn | null;
  selectedAgent: MeetingAgent | null;
  mode?: "flow" | "timeline";
}) {
  if (selectedTurn) {
    return (
      <div
        className="rounded-[24px] border border-white/10 bg-[#141416]/85 p-4 text-white shadow-[0_24px_80px_-40px_rgba(15,23,42,0.85)] backdrop-blur-xl"
        data-testid="flow-detail-panel"
      >
        <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-fuchsia-200/70">
          Selected turn
        </p>
        <div className="mt-3 flex items-start justify-between gap-3">
          <div>
            <h2 className="text-2xl font-medium tracking-tight text-white">Turn {selectedTurn.order}</h2>
            <p className="mt-1 text-sm text-slate-300">{selectedTurn.agentLabel}</p>
          </div>
          <span className="rounded-full border border-white/10 bg-white/8 px-3 py-1 text-xs font-semibold text-slate-200">
            {formatSentimentLabel(selectedTurn.sentimentLabel)}
          </span>
        </div>
        <p className="mt-4 text-sm leading-7 text-slate-100">{selectedTurn.text}</p>
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <ScorePill label="Dominant emotion" value={selectedTurn.dominantEmotion} />
          <ScorePill label="Dominant signal" value={selectedTurn.dominantSignal} />
          <ScorePill
            label="Sentiment confidence"
            value={`${Math.round(selectedTurn.sentimentConfidence * 100)}%`}
          />
          <ScorePill
            label="Emerging emotions"
            value={selectedTurn.emergingEmotions.slice(0, 2).join(", ") || "N/A"}
          />
        </div>
        <div className="mt-5 space-y-3">
          <ScoreMeter label="Dominance" value={selectedTurn.rubric.dominance} />
          <ScoreMeter label="Efficiency" value={selectedTurn.rubric.efficiency} />
          <ScoreMeter label="Cohesion" value={selectedTurn.rubric.cohesion} />
        </div>
      </div>
    );
  }

  if (selectedAgent) {
    return (
      <div
        className="rounded-[24px] border border-white/10 bg-[#141416]/85 p-4 text-white shadow-[0_24px_80px_-40px_rgba(15,23,42,0.85)] backdrop-blur-xl"
        data-testid="flow-detail-panel"
      >
        <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-violet-200/70">
          Agent focus
        </p>
        <h2 className="mt-3 text-2xl font-medium tracking-tight text-white">{selectedAgent.label}</h2>
        <p className="mt-3 text-sm leading-7 text-slate-300">{selectedAgent.summary}</p>
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <ScorePill label="Turn count" value={`${selectedAgent.turnCount}`} />
          <ScorePill label="Primary emotion" value={selectedAgent.primaryEmotion} />
          <ScorePill label="Primary signal" value={selectedAgent.primarySignal} />
          <ScorePill
            label="Emerging emotions"
            value={selectedAgent.emergingEmotions.slice(0, 2).join(", ") || "N/A"}
          />
        </div>
      </div>
    );
  }

  return (
    <div
      className="rounded-[24px] border border-white/10 bg-[#141416]/85 p-4 text-white shadow-[0_24px_80px_-40px_rgba(15,23,42,0.85)] backdrop-blur-xl"
      data-testid="flow-detail-panel"
    >
      <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-emerald-200/70">
        {mode === "timeline" ? "Timeline guide" : "Flow guide"}
      </p>
      <h2 className="mt-3 text-2xl font-medium tracking-tight text-white">
        {mode === "timeline" ? "회의 흐름을 시계열로 탐색" : "회의 흐름을 그래프로 탐색"}
      </h2>
      <p className="mt-3 text-sm leading-7 text-slate-300">
        {mode === "timeline"
          ? "탭을 전환하며 감정, 시그널, 루브릭 흐름을 비교하고 특정 turn을 선택하면 오른쪽 패널에서 상세 내용을 확인할 수 있습니다."
          : "에이전트 lane과 turn chronology를 동시에 보면서, 특정 발화를 선택하면 rubric과 signal을 오른쪽 패널에서 바로 확인할 수 있습니다."}
      </p>
      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        <ScorePill label="Turns" value={`${summary?.totalTurns ?? turns.length}`} />
        <ScorePill label="Agents" value={`${summary?.totalAgents ?? 0}`} />
        <ScorePill label="Topics" value={`${summary?.topics.length ?? 0}`} />
        <ScorePill label="Hint" value={mode === "timeline" ? "탭 + agent filter" : "Cmd / Ctrl + K"} />
      </div>
    </div>
  );
}
