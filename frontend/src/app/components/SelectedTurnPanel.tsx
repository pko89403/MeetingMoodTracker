import React from "react";
import type { MeetingTurn } from "../../lib/meetingDashboard";
import { DetailPanel } from "./DetailPanel";

interface SelectedTurnPanelProps {
  turn: MeetingTurn | null;
  variant: "inline" | "drawer";
  onClose?: () => void;
}

export function SelectedTurnPanel({
  turn,
  variant,
  onClose,
}: SelectedTurnPanelProps) {
  if (!turn) {
    return null;
  }

  if (variant === "inline") {
    return (
      <div className="overflow-hidden rounded-[28px] border border-slate-200/80 bg-white/90 shadow-[0_20px_50px_-28px_rgba(15,23,42,0.24)]">
        <DetailPanel turn={turn} />
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/45 backdrop-blur-sm xl:hidden">
      <div className="flex h-full w-full max-w-sm flex-col overflow-y-auto border-l border-slate-200 bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-4 py-4">
          <h3 className="text-sm font-semibold text-slate-800">발화 상세 분석</h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 transition hover:bg-slate-50"
          >
            닫기
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">
          <DetailPanel turn={turn} />
        </div>
      </div>
    </div>
  );
}
