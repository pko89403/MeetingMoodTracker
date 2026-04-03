import React from "react";
import type { MeetingTurn } from "../../lib/meetingDashboard";

interface TurnTranscriptListProps {
  turns: MeetingTurn[];
  selectedTurnId: string | null;
  onSelectTurn: (turnId: string) => void;
  compact?: boolean;
  className?: string;
}

function previewText(text: string, maxLength = 96): string {
  if (text.length <= maxLength) {
    return text;
  }

  return `${text.slice(0, maxLength)}...`;
}

export function TurnTranscriptList({
  turns,
  selectedTurnId,
  onSelectTurn,
  compact = false,
  className = "",
}: TurnTranscriptListProps) {
  if (turns.length === 0) {
    return null;
  }

  return (
    <div
      className={`rounded-[24px] border border-slate-200 bg-white p-4 ${compact ? "flex min-h-0 flex-col" : ""} ${className}`.trim()}
    >
      <div className="mb-3">
        <p className="text-xs font-semibold tracking-wide text-indigo-600">Turn transcript timeline</p>
        <h3 className="mt-1 text-base font-semibold text-slate-900">턴별 대화 내용과 감정 흐름</h3>
        <p className="mt-1 text-sm text-slate-500">
          Turn, Agent, Text preview만 보여주며 클릭 시 상세 패널과 연동됩니다.
        </p>
      </div>

      <div
        className={
          compact
            ? "flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto pr-1"
            : "grid gap-3 lg:grid-cols-2"
        }
      >
        {turns.map((turn) => {
          const isSelected = turn.turnId === selectedTurnId;

          return (
            <button
              key={turn.turnId}
              type="button"
              onClick={() => onSelectTurn(turn.turnId)}
              className={`text-left transition ${
                compact ? "rounded-xl px-3 py-2.5" : "rounded-2xl px-4 py-4"
              } ${
                isSelected
                  ? "border-indigo-300 bg-indigo-50/70 shadow-[0_14px_30px_-22px_rgba(79,70,229,0.55)]"
                  : "border-slate-200 bg-slate-50/70 hover:border-slate-300 hover:bg-white"
              }`}
            >
              <div
                className={`flex items-center gap-2 ${
                  compact ? "text-[11px]" : "flex-wrap text-xs"
                } font-medium`}
              >
                {compact ? (
                  <>
                    <span className="font-semibold text-slate-900">Turn {turn.order}</span>
                    <span className="text-slate-300">/</span>
                    <span className="text-slate-600">{turn.agentLabel}</span>
                  </>
                ) : (
                  <>
                    <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-slate-700">
                      Turn {turn.order}
                    </span>
                    <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-slate-700">
                      {turn.agentLabel}
                    </span>
                  </>
                )}
              </div>

              <p
                className={`text-slate-800 ${compact ? "mt-1.5 text-xs leading-5" : "mt-3 text-sm leading-6"}`}
              >
                {previewText(turn.text, compact ? 72 : 96)}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
