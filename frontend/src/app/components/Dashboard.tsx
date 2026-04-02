import React, { useState } from "react";
import { Header } from "./Header";
import { SummaryCards } from "./SummaryCards";
import { TimelineChart } from "./TimelineChart";
import { SpeakerCards } from "./SpeakerCards";
import { DetailPanel } from "./DetailPanel";
import { MOCK_MEETING_SUMMARY, MOCK_SPEAKERS, MOCK_TURNS } from "../../mockData";

export function Dashboard() {
  const [selectedTurnId, setSelectedTurnId] = useState<string | null>(null);
  const [chartView, setChartView] = useState<"signals" | "emotions">("signals");

  const selectedTurn = selectedTurnId 
    ? MOCK_TURNS.find(t => t.turn_id === selectedTurnId) || null 
    : null;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      <Header summary={MOCK_MEETING_SUMMARY} />
      
      <main className="flex-1 flex overflow-hidden">
        {/* Left Content Area - Scrollable */}
        <div className="flex-1 overflow-y-auto px-4 py-4 lg:px-6 lg:py-6 pb-20">
          <div className="max-w-[1400px] mx-auto flex flex-col space-y-6 lg:space-y-8">
            
            {/* 1. Compact Summary Block */}
            <section>
              <SummaryCards summary={MOCK_MEETING_SUMMARY} />
            </section>

            {/* 2. Timeline - The Star of the Show */}
            <section className="flex flex-col flex-1 h-[600px] min-h-[500px]">
              <div className="flex items-center justify-between mb-3 border-b border-slate-200 pb-2">
                <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
                  <span className="w-1 h-3 bg-indigo-500 inline-block"></span>
                  Emotion & Signal Timeline
                </h2>
                <div className="flex bg-slate-100 p-0.5 border border-slate-200">
                  <button
                    onClick={() => setChartView("signals")}
                    className={`px-3 py-1 text-[10px] font-bold uppercase tracking-wider transition-colors ${
                      chartView === "signals" ? "bg-white shadow-sm text-indigo-700 border-b border-indigo-400" : "text-slate-500 hover:text-slate-700"
                    }`}
                  >
                    Meeting Signals
                  </button>
                  <button
                    onClick={() => setChartView("emotions")}
                    className={`px-3 py-1 text-[10px] font-bold uppercase tracking-wider transition-colors ${
                      chartView === "emotions" ? "bg-white shadow-sm text-indigo-700 border-b border-indigo-400" : "text-slate-500 hover:text-slate-700"
                    }`}
                  >
                    Base Emotions
                  </button>
                </div>
              </div>
              <div className="bg-white border border-slate-200 p-4 flex-1 shadow-sm">
                <TimelineChart 
                  turns={MOCK_TURNS} 
                  view={chartView} 
                  onSelectTurn={setSelectedTurnId}
                  selectedTurnId={selectedTurnId}
                />
              </div>
            </section>

            {/* 3. Speaker Analysis - Compact Rows */}
            <section>
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2 mb-3 border-b border-slate-200 pb-2">
                  <span className="w-1 h-3 bg-slate-400 inline-block"></span>
                  Speaker Analysis
              </h2>
              <SpeakerCards speakers={MOCK_SPEAKERS} />
            </section>
            
          </div>
        </div>

        {/* Right Side Drawer - Selected Turn Detail */}
        <aside className="w-[420px] flex-shrink-0 bg-white border-l border-slate-300 overflow-y-auto hidden xl:block shadow-[-4px_0_15px_-3px_rgba(0,0,0,0.05)]">
          <DetailPanel turn={selectedTurn} speakers={MOCK_SPEAKERS} />
        </aside>

        {/* Mobile Detail Panel Overlay */}
        {selectedTurn && (
          <div className="xl:hidden fixed inset-0 z-50 bg-slate-900/40 flex justify-end">
             <div className="w-full max-w-sm bg-white h-full overflow-y-auto shadow-2xl flex flex-col border-l border-slate-300">
                <div className="p-3 border-b border-slate-200 flex justify-between items-center bg-slate-50">
                   <h3 className="font-bold text-[10px] uppercase tracking-wider text-slate-500">Turn Details</h3>
                   <button onClick={() => setSelectedTurnId(null)} className="text-slate-500 p-2 text-[10px] font-bold uppercase tracking-wider hover:text-slate-800">Close</button>
                </div>
                <div className="flex-1 overflow-y-auto">
                   <DetailPanel turn={selectedTurn} speakers={MOCK_SPEAKERS} />
                </div>
             </div>
          </div>
        )}
      </main>
    </div>
  );
}
