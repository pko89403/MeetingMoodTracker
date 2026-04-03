import React from "react";
import { Hash, MessageSquareText, Tags, Users } from "lucide-react";
import { MeetingSummary } from "../../lib/meetingDashboard";

export function SummaryCards({ summary }: { summary: MeetingSummary }) {
  return (
    <div className="grid gap-4 xl:grid-cols-[1.25fr_0.95fr]">
      <section className="rounded-[28px] border border-slate-200/80 bg-white/90 p-6 shadow-[0_20px_50px_-28px_rgba(15,23,42,0.24)]">
        <div className="mb-5 flex items-center gap-2 text-slate-500">
          <span className="rounded-full bg-indigo-50 p-2 text-indigo-600">
            <MessageSquareText size={16} />
          </span>
          <div>
            <p className="text-xs font-semibold tracking-wide text-indigo-600">Overview</p>
            <h3 className="text-lg font-semibold text-slate-900">회의 핵심 요약</h3>
          </div>
        </div>

        <div className="rounded-3xl bg-[linear-gradient(135deg,_rgba(238,242,255,1)_0%,_rgba(248,250,252,1)_100%)] p-5">
          {summary.oneLineSummary ? (
            <p className="text-base font-semibold leading-7 text-slate-900">
              {summary.oneLineSummary}
            </p>
          ) : (
            <p className="text-base font-medium leading-7 text-slate-500">
              요약이 아직 생성되지 않았습니다.
            </p>
          )}

          <div className="mt-5 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="rounded-2xl border border-slate-200 bg-white/90 p-4">
              <div className="mb-3 flex items-center gap-2 text-slate-500">
                <Tags size={14} />
                <h3 className="text-sm font-semibold text-slate-800">토픽 집계</h3>
              </div>
              <div className="flex flex-wrap gap-2">
                {summary.topics.length > 0 ? (
                  summary.topics.map((topic) => (
                    <span
                      key={topic}
                      className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700"
                    >
                      <Hash size={12} className="text-slate-400" />
                      {topic}
                    </span>
                  ))
                ) : (
                  <p className="text-sm text-slate-500">추출된 topic aggregate가 아직 없습니다.</p>
                )}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white/90 p-4">
              <h3 className="text-sm font-semibold text-slate-800">
                회의 감정 분포
              </h3>
              <div className="mt-4 h-3 w-full overflow-hidden rounded-full bg-slate-100">
                <div className="flex h-full w-full">
                  <div style={{ width: `${summary.sentimentDist.pos}%` }} className="bg-emerald-400" />
                  <div style={{ width: `${summary.sentimentDist.neu}%` }} className="bg-slate-300" />
                  <div style={{ width: `${summary.sentimentDist.neg}%` }} className="bg-rose-400" />
                </div>
              </div>
              <div className="mt-4 grid grid-cols-3 gap-2 text-xs font-medium text-slate-600">
                <span className="rounded-xl bg-emerald-50 px-3 py-2 text-center text-emerald-700">
                  긍정 {summary.sentimentDist.pos}%
                </span>
                <span className="rounded-xl bg-slate-100 px-3 py-2 text-center">
                  중립 {summary.sentimentDist.neu}%
                </span>
                <span className="rounded-xl bg-rose-50 px-3 py-2 text-center text-rose-700">
                  부정 {summary.sentimentDist.neg}%
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-[24px] border border-slate-200/80 bg-white/90 p-5 shadow-[0_20px_50px_-28px_rgba(15,23,42,0.2)]">
          <p className="text-xs font-semibold tracking-wide text-slate-500">총 발화 수</p>
          <div className="mt-3 text-3xl font-bold tracking-tight text-slate-900">
            {summary.totalTurns}
          </div>
          <p className="mt-2 text-sm text-slate-500">timeline에 연결된 저장 발화</p>
        </div>

        <div className="rounded-[24px] border border-slate-200/80 bg-white/90 p-5 shadow-[0_20px_50px_-28px_rgba(15,23,42,0.2)]">
          <div className="flex items-center gap-2 text-slate-500">
            <Users size={15} />
            <p className="text-xs font-semibold tracking-wide">참여 에이전트</p>
          </div>
          <div className="mt-3 text-3xl font-bold tracking-tight text-slate-900">
            {summary.totalAgents}
          </div>
          <p className="mt-2 text-sm text-slate-500">agent report 집계 기준</p>
        </div>
      </section>
    </div>
  );
}
