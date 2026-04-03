import React from "react";
import { Clock3, FolderKanban, RefreshCcw } from "lucide-react";
import { MeetingSummary } from "../../lib/meetingDashboard";

interface HeaderProps {
  projectId: string;
  meetingId: string;
  summary: MeetingSummary | null;
  onReset: () => void;
}

export function Header({ projectId, meetingId, summary, onReset }: HeaderProps) {
  return (
    <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/80 backdrop-blur">
      <div className="mx-auto max-w-[1400px] px-4 py-4 lg:px-6">
        <div className="overflow-hidden rounded-[28px] border border-slate-200/70 bg-[linear-gradient(135deg,_rgba(15,23,42,1)_0%,_rgba(49,46,129,0.95)_52%,_rgba(79,70,229,0.82)_100%)] px-6 py-6 text-white shadow-[0_24px_70px_-32px_rgba(30,41,59,0.75)]">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
            <div className="min-w-0">
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <span className="rounded-full border border-white/15 bg-white/10 px-3 py-1 text-[11px] font-semibold tracking-wide text-indigo-50">
                  Meeting mood dashboard
                </span>
                <span className="rounded-full border border-emerald-300/25 bg-emerald-400/10 px-3 py-1 text-[11px] font-semibold text-emerald-100">
                  Read API connected
                </span>
              </div>

              <h1 className="truncate text-2xl font-bold tracking-tight text-white lg:text-[2rem]">
                {summary?.title ?? `Meeting ${meetingId}`}
              </h1>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-indigo-100/85">
                프로젝트 단위 회의 데이터를 읽어 summary, turn timeline, agent pattern을 한 화면에서 탐색합니다.
              </p>

              <div className="mt-4 flex flex-wrap items-center gap-2 text-sm">
                <span className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-indigo-50">
                  <FolderKanban size={14} className="text-indigo-100" />
                  {projectId}
                </span>
                <span className="rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-indigo-50">
                  {meetingId}
                </span>
                {summary?.lastUpdated && (
                  <span className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-indigo-50">
                    <Clock3 size={14} className="text-indigo-100" />
                    {new Date(summary.lastUpdated).toLocaleString()}
                  </span>
                )}
              </div>
            </div>

            <button
              type="button"
              onClick={onReset}
              className="inline-flex items-center justify-center gap-2 self-start rounded-2xl border border-white/20 bg-white/10 px-4 py-3 text-sm font-semibold text-white transition hover:bg-white/15"
            >
              <RefreshCcw size={14} />
              다른 회의 열기
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
