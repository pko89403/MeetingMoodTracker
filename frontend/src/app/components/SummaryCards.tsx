import React from "react";
import { MessageSquareText } from "lucide-react";
import { MeetingSummary } from "../../mockData";

export function SummaryCards({ summary }: { summary: MeetingSummary }) {
  return (
    <div className="flex flex-col lg:flex-row gap-4 border border-slate-200 bg-white p-4 rounded-sm">
      {/* AI Summary Banner */}
      <div className="flex-1 flex flex-col justify-center lg:pr-6 lg:border-r border-slate-200">
        <div className="flex items-center gap-1.5 mb-1.5 text-slate-500">
          <MessageSquareText size={14}/>
          <h3 className="text-[10px] font-bold uppercase tracking-wider">AI Summary</h3>
        </div>
        <p className="text-sm font-medium text-slate-800 leading-snug">
          {summary.oneLineSummary}
        </p>
      </div>

      {/* Core Stats Row */}
      <div className="flex flex-wrap lg:flex-nowrap gap-6 lg:gap-8 items-center lg:pl-2">
        {/* Turns */}
        <div className="flex flex-col">
          <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Total Turns</h3>
          <span className="text-lg font-mono font-bold text-slate-700">{summary.totalTurns}</span>
        </div>

        {/* Sentiment Row */}
        <div className="flex flex-col w-32">
          <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Sentiment</h3>
          <div className="w-full flex h-2 rounded-sm overflow-hidden mb-1">
            <div style={{ width: `${summary.sentimentDist.pos}%` }} className="bg-emerald-400" />
            <div style={{ width: `${summary.sentimentDist.neu}%` }} className="bg-slate-300" />
            <div style={{ width: `${summary.sentimentDist.neg}%` }} className="bg-rose-400" />
          </div>
          <div className="flex justify-between text-[9px] font-bold text-slate-500 uppercase tracking-wider">
            <span>+{summary.sentimentDist.pos}%</span>
            <span>-{summary.sentimentDist.neg}%</span>
          </div>
        </div>

        {/* Dominant Signals */}
        <div className="flex gap-4">
          <div className="flex flex-col">
            <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Dom Emotion</h3>
            <span className="text-sm font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded-sm border border-slate-200">{summary.dominantEmotion}</span>
          </div>
          <div className="flex flex-col">
            <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Dom Signal</h3>
            <span className="text-sm font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-sm border border-indigo-200">{summary.dominantSignal}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
