import React from "react";
import { User, MessageSquare, AlertCircle, TrendingUp, BarChart, Heart, Hash } from "lucide-react";
import { Turn, Speaker } from "../../mockData";

interface DetailPanelProps {
  turn: Turn | null;
  speakers: Speaker[];
}

export function DetailPanel({ turn, speakers }: DetailPanelProps) {
  if (!turn) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center text-slate-400 bg-slate-50">
        <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4 border border-slate-200 shadow-sm">
          <BarChart size={24} className="text-slate-300" />
        </div>
        <h3 className="text-sm font-bold text-slate-600 mb-2">No Turn Selected</h3>
        <p className="text-xs font-medium text-slate-500 leading-relaxed max-w-[200px]">
          Select a point on the timeline chart to inspect detailed turn analysis.
        </p>
      </div>
    );
  }

  const speaker = speakers.find((s) => s.id === turn.speaker_id);

  return (
    <div className="flex flex-col h-full bg-white relative">
      {/* Sticky Header */}
      <div className="p-5 border-b border-slate-200 bg-slate-50 z-10 flex-shrink-0">
        <div className="flex justify-between items-start mb-3">
          <span className="bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-[2px] text-[10px] font-bold border border-indigo-100 flex items-center gap-1 uppercase tracking-wider">
            <Hash size={10} /> Turn {turn.order}
          </span>
          <span className="text-[10px] font-mono font-bold text-slate-400 border border-slate-200 px-1.5 py-0.5 rounded-[2px] bg-white">{turn.turn_id}</span>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-sm bg-indigo-100 flex items-center justify-center text-indigo-600 border border-indigo-200 font-bold text-sm">
            {speaker?.name.charAt(0) || "U"}
          </div>
          <div>
            <h3 className="font-bold text-slate-800 text-sm">{speaker?.name || "Unknown"}</h3>
            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{speaker?.role}</p>
          </div>
        </div>
      </div>

      <div className="p-5 space-y-6 flex-1 overflow-y-auto bg-slate-50">
        {/* Transcript */}
        <section>
          <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 mb-1.5">
            <MessageSquare size={12} /> Transcript
          </h4>
          <div className="bg-white border border-slate-200 rounded-[2px] p-3.5 text-xs text-slate-700 leading-relaxed relative">
             <div className="absolute top-0 left-0 w-0.5 h-full bg-indigo-400" />
            "{turn.text}"
          </div>
        </section>

        {/* Sentiment Analysis */}
        <section>
          <div className="flex justify-between items-center mb-1.5">
             <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
               <Heart size={12} /> Sentiment
             </h4>
             <span className="text-[10px] font-bold bg-white px-1.5 py-0.5 rounded-[2px] border border-slate-200 text-slate-600 font-mono">
                SCORE: {turn.sentiment.score.toFixed(2)}
             </span>
          </div>
          <div className="bg-white border border-slate-200 rounded-[2px] p-3">
             <div className="h-1.5 w-full bg-slate-100 rounded-[1px] overflow-hidden flex mb-2">
               <div className="bg-emerald-400" style={{ width: `${turn.sentiment.pos}%` }} />
               <div className="bg-slate-300" style={{ width: `${turn.sentiment.neu}%` }} />
               <div className="bg-rose-400" style={{ width: `${turn.sentiment.neg}%` }} />
             </div>
             <div className="flex justify-between text-[9px] font-bold text-slate-500 uppercase tracking-wider">
                <span className="flex items-center gap-1"><div className="w-1.5 h-1.5 bg-emerald-400"/> POS {turn.sentiment.pos}%</span>
                <span className="flex items-center gap-1"><div className="w-1.5 h-1.5 bg-slate-300"/> NEU {turn.sentiment.neu}%</span>
                <span className="flex items-center gap-1"><div className="w-1.5 h-1.5 bg-rose-400"/> NEG {turn.sentiment.neg}%</span>
             </div>
          </div>
        </section>

        {/* Core Metrics */}
        <section className="grid grid-cols-2 gap-3">
          <div className="bg-white border border-slate-200 rounded-[2px] p-3">
            <h4 className="text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">
              Dom Emotion
            </h4>
            <div className="text-sm font-bold text-slate-800">{turn.dominantEmotion}</div>
          </div>
          <div className="bg-white border border-slate-200 rounded-[2px] p-3">
            <h4 className="text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">
              Dom Signal
            </h4>
            <div className="text-sm font-bold text-indigo-700">{turn.dominantSignal}</div>
          </div>
        </section>

        {/* Meeting Signals Bars */}
        <section>
          <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 mb-2">
            <TrendingUp size={12} /> Signals
          </h4>
          <div className="space-y-3 bg-white border border-slate-200 rounded-[2px] p-3">
            {Object.entries(turn.meetingSignals).map(([key, val]) => (
              <div key={key}>
                <div className="flex justify-between text-[10px] font-bold text-slate-600 mb-1 uppercase tracking-wider">
                  <span>{key}</span>
                  <span className={val > 70 ? "text-rose-500" : "text-slate-400"}>{val}</span>
                </div>
                <div className="w-full bg-slate-100 h-1 overflow-hidden">
                  <div 
                    className={`h-1 ${
                      key === 'tension' && val > 70 ? 'bg-rose-500' :
                      key === 'urgency' && val > 70 ? 'bg-orange-500' :
                      'bg-indigo-400'
                    }`} 
                    style={{ width: `${val}%` }} 
                  />
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Emerging Emotions */}
        {turn.emergingEmotions.length > 0 && (
          <section>
            <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 mb-2">
              <AlertCircle size={12} /> Emerging
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {turn.emergingEmotions.map((em, i) => (
                <span key={i} className="bg-white border border-slate-200 px-2 py-0.5 text-[9px] font-bold text-slate-600 uppercase tracking-widest">
                  {em}
                </span>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
