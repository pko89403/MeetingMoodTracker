import React, { useEffect, useState } from "react";
import { Dashboard } from "./components/Dashboard";

type MeetingSelection = {
  projectId: string;
  meetingId: string;
};

function readSelectionFromUrl(): MeetingSelection {
  const params = new URLSearchParams(window.location.search);
  return {
    projectId: params.get("project_id")?.trim() ?? "",
    meetingId: params.get("meeting_id")?.trim() ?? "",
  };
}

function writeSelectionToUrl(selection: MeetingSelection) {
  const url = new URL(window.location.href);

  if (selection.projectId) {
    url.searchParams.set("project_id", selection.projectId);
  } else {
    url.searchParams.delete("project_id");
  }

  if (selection.meetingId) {
    url.searchParams.set("meeting_id", selection.meetingId);
  } else {
    url.searchParams.delete("meeting_id");
  }

  window.history.pushState({}, "", url.toString());
}

function MeetingInput({
  initialSelection,
  onEnter,
}: {
  initialSelection: MeetingSelection;
  onEnter: (selection: MeetingSelection) => void;
}) {
  const [projectId, setProjectId] = useState(initialSelection.projectId);
  const [meetingId, setMeetingId] = useState(initialSelection.meetingId);

  useEffect(() => {
    setProjectId(initialSelection.projectId);
    setMeetingId(initialSelection.meetingId);
  }, [initialSelection.meetingId, initialSelection.projectId]);

  const isDisabled = projectId.trim() === "" || meetingId.trim() === "";

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(99,102,241,0.18),_transparent_32%),linear-gradient(180deg,_#f8fafc_0%,_#eef2ff_100%)] px-4 py-10">
      <div className="mx-auto flex min-h-[calc(100vh-5rem)] w-full max-w-6xl items-center justify-center">
      <form
        className="w-full max-w-xl rounded-[28px] border border-white/70 bg-white/90 p-8 shadow-[0_24px_80px_-28px_rgba(15,23,42,0.28)] backdrop-blur"
        onSubmit={(event) => {
          event.preventDefault();
          if (isDisabled) {
            return;
          }

          onEnter({
            projectId: projectId.trim(),
            meetingId: meetingId.trim(),
          });
        }}
      >
        <div className="mb-8">
          <span className="inline-flex items-center rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-[11px] font-semibold text-indigo-700">
            Project-aware meeting dashboard
          </span>
          <h1 className="mt-4 text-3xl font-bold tracking-tight text-slate-900">
            Meeting Mood Tracker
          </h1>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            저장된 회의 데이터를 불러와 감정 타임라인, 회의 요약, 에이전트 리포트를 한 화면에서 확인합니다.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {["Emotion timeline", "Topic summary", "Agent report"].map((item) => (
              <span
                key={item}
                className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-600"
              >
                {item}
              </span>
            ))}
          </div>
        </div>

        <label className="mb-2 block text-sm font-semibold text-slate-700">
          Project ID
        </label>
        <input
          type="text"
          placeholder="예: project-frontend-demo"
          value={projectId}
          onChange={(event) => setProjectId(event.target.value)}
          className="mb-4 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-800 shadow-inner outline-none transition focus:border-indigo-300 focus:bg-white focus:ring-4 focus:ring-indigo-100"
        />

        <label className="mb-2 block text-sm font-semibold text-slate-700">
          Meeting ID
        </label>
        <input
          type="text"
          placeholder="예: meeting-issue27-short-live"
          value={meetingId}
          onChange={(event) => setMeetingId(event.target.value)}
          className="mb-3 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-800 shadow-inner outline-none transition focus:border-indigo-300 focus:bg-white focus:ring-4 focus:ring-indigo-100"
        />

        <p className="mb-6 text-xs leading-6 text-slate-500">
          URL query params도 지원합니다: <span className="font-mono">?project_id=...&meeting_id=...</span>
        </p>

        <button
          type="submit"
          disabled={isDisabled}
          className="w-full rounded-2xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white shadow-[0_16px_36px_-18px_rgba(15,23,42,0.9)] transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none"
        >
          회의 대시보드 보기
        </button>
      </form>
      </div>
    </div>
  );
}

export default function App() {
  const [selection, setSelection] = useState<MeetingSelection>(() => readSelectionFromUrl());

  useEffect(() => {
    const handlePopState = () => {
      setSelection(readSelectionFromUrl());
    };

    window.addEventListener("popstate", handlePopState);
    return () => {
      window.removeEventListener("popstate", handlePopState);
    };
  }, []);

  const handleEnter = (nextSelection: MeetingSelection) => {
    writeSelectionToUrl(nextSelection);
    setSelection(nextSelection);
  };

  const handleReset = () => {
    const nextSelection = { projectId: "", meetingId: "" };
    writeSelectionToUrl(nextSelection);
    setSelection(nextSelection);
  };

  if (!selection.projectId || !selection.meetingId) {
    return <MeetingInput initialSelection={selection} onEnter={handleEnter} />;
  }

  return (
    <div className="antialiased text-slate-900 bg-slate-50 min-h-screen">
      <Dashboard
        projectId={selection.projectId}
        meetingId={selection.meetingId}
        onReset={handleReset}
      />
    </div>
  );
}
