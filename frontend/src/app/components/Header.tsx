import React from "react";
import { Clock, Hash, CheckCircle, Tag } from "lucide-react";
import { MeetingSummary } from "../../mockData";

interface HeaderProps {
  summary: MeetingSummary;
}

export function Header({ summary }: HeaderProps) {
  return (
    <header className="bg-white border-b border-slate-300 px-6 py-3 flex flex-col md:flex-row md:items-center justify-between sticky top-0 z-20">
      <div className="flex flex-col mb-2 md:mb-0">
        <div className="flex items-center space-x-3 mb-1">
          <h1 className="text-lg font-bold text-slate-800 flex items-center">
            {summary.title}
          </h1>
          <span className="px-2 py-0.5 rounded-sm text-[11px] font-bold bg-emerald-50 text-emerald-700 flex items-center gap-1 border border-emerald-200 uppercase tracking-wider">
            <CheckCircle size={10} />
            {summary.status}
          </span>
        </div>
        <div className="text-[11px] text-slate-500 font-medium font-mono flex items-center space-x-2 uppercase tracking-wide">
          <Hash size={12} className="text-slate-400" />
          <span>{summary.meetingId}</span>
          <span className="text-slate-300">|</span>
          <Clock size={12} className="text-slate-400" />
          <span>Updated: {new Date(summary.lastUpdated).toLocaleDateString()}</span>
        </div>
      </div>

      <div className="flex flex-col md:items-end space-y-2">
        <div className="flex flex-wrap gap-1.5 justify-end">
          {summary.topics.map((topic, i) => (
            <div
              key={i}
              className="flex items-center space-x-1 px-2 py-0.5 bg-slate-50 border border-slate-200 text-slate-600 rounded-sm text-[10px] font-bold uppercase tracking-wider"
            >
              <Tag size={10} className="text-slate-400" />
              <span>{topic}</span>
            </div>
          ))}
        </div>
      </div>
    </header>
  );
}
