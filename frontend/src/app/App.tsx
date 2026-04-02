import React, { useState } from "react";
import { Dashboard } from "./components/Dashboard";

function MeetingInput({ onEnter }: { onEnter: (id: string) => void }) {
  const [value, setValue] = useState("");
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="bg-white border border-slate-200 rounded p-8 shadow-sm w-full max-w-sm">
        <h1 className="text-lg font-bold text-slate-800 mb-2">Meeting Mood Tracker</h1>
        <p className="text-sm text-slate-500 mb-6">회의 ID를 입력해 분석 결과를 확인하세요.</p>
        <input
          type="text"
          placeholder="예: MTG-2026-Q2-774A"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && value.trim() && onEnter(value.trim())}
          className="w-full border border-slate-300 rounded px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-1 focus:ring-indigo-400"
        />
        <button
          onClick={() => value.trim() && onEnter(value.trim())}
          className="w-full bg-indigo-600 text-white text-sm font-bold py-2 rounded hover:bg-indigo-700 transition-colors"
        >
          회의 분석 보기
        </button>
      </div>
    </div>
  );
}

export default function App() {
  const params = new URLSearchParams(window.location.search);
  const urlMeetingId = params.get("meeting_id");
  const [meetingId, setMeetingId] = useState<string | null>(urlMeetingId);

  const handleEnter = (id: string) => {
    const url = new URL(window.location.href);
    url.searchParams.set("meeting_id", id);
    window.history.pushState({}, "", url.toString());
    setMeetingId(id);
  };

  if (!meetingId) {
    return <MeetingInput onEnter={handleEnter} />;
  }

  return (
    <div className="antialiased text-slate-900 bg-slate-50 min-h-screen">
      <Dashboard meetingId={meetingId} />
    </div>
  );
}
