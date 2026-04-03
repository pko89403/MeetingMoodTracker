import React from "react";
import type { MeetingSummary } from "../../lib/meetingDashboard";
import { SectionState } from "./SectionState";
import { SummaryCards } from "./SummaryCards";

interface MeetingSummarySectionProps {
  summary: MeetingSummary | undefined;
  isLoading: boolean;
  fallback: {
    totalTurns: number;
    totalAgents: number;
  };
}

export function MeetingSummarySection({
  summary,
  isLoading,
  fallback,
}: MeetingSummarySectionProps) {
  if (summary) {
    return (
      <section>
        <SummaryCards summary={summary} />
      </section>
    );
  }

  if (isLoading) {
    return (
      <section>
        <SectionState title="회의 요약" message="회의 overview를 불러오는 중입니다." />
      </section>
    );
  }

  return (
    <section>
      <div className="grid gap-4 xl:grid-cols-[1.25fr_0.95fr]">
        <div className="rounded-[28px] border border-slate-200/80 bg-white/90 p-6 shadow-[0_20px_50px_-28px_rgba(15,23,42,0.24)]">
          <div className="rounded-3xl bg-[linear-gradient(135deg,_rgba(248,250,252,1)_0%,_rgba(238,242,255,1)_100%)] p-5">
            <p className="text-sm font-semibold text-slate-900">회의 요약을 아직 구성하지 못했습니다.</p>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              overview API가 실패해 topic/요약 문장을 채우지 못했습니다. 다만 아래 타임라인과
              agent report는 계속 탐색할 수 있습니다.
            </p>
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-[24px] border border-slate-200/80 bg-white/90 p-5 shadow-[0_20px_50px_-28px_rgba(15,23,42,0.2)]">
            <p className="text-xs font-semibold tracking-wide text-slate-500">확인된 발화 수</p>
            <div className="mt-3 text-3xl font-bold tracking-tight text-slate-900">
              {fallback.totalTurns}
            </div>
          </div>
          <div className="rounded-[24px] border border-slate-200/80 bg-white/90 p-5 shadow-[0_20px_50px_-28px_rgba(15,23,42,0.2)]">
            <p className="text-xs font-semibold tracking-wide text-slate-500">에이전트 수</p>
            <div className="mt-3 text-3xl font-bold tracking-tight text-slate-900">
              {fallback.totalAgents}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
