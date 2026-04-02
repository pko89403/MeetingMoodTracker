import React from "react";
import { MessageCircle, Brain, Zap, Sparkles, TrendingUp } from "lucide-react";
import { Speaker } from "../../mockData";

const EMOTION_COLORS: Record<string, string> = {
  Anticipation: "text-sky-600 bg-sky-50 border-sky-200",
  Joy: "text-emerald-600 bg-emerald-50 border-emerald-200",
  Frustration: "text-rose-600 bg-rose-50 border-rose-200",
  Anger: "text-red-600 bg-red-50 border-red-200",
  Fear: "text-purple-600 bg-purple-50 border-purple-200",
  Surprise: "text-amber-600 bg-amber-50 border-amber-200",
};

const SIGNAL_COLORS: Record<string, string> = {
  Clarity: "text-sky-600 bg-sky-50 border-sky-200",
  Engagement: "text-violet-600 bg-violet-50 border-violet-200",
  Urgency: "text-orange-600 bg-orange-50 border-orange-200",
  Tension: "text-rose-600 bg-rose-50 border-rose-200",
  Alignment: "text-emerald-600 bg-emerald-50 border-emerald-200",
};

export function SpeakerCards({ speakers }: { speakers: Speaker[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {speakers.map((speaker) => {
        const initials = speaker.name.split(' ').map(n => n[0]).join('');
        const emoColor = EMOTION_COLORS[speaker.primaryEmotion] || "text-slate-600 bg-slate-50 border-slate-200";
        const sigColor = SIGNAL_COLORS[speaker.primarySignal] || "text-indigo-600 bg-indigo-50 border-indigo-200";

        return (
          <div key={speaker.id} className="bg-white border border-slate-200 rounded-[4px] flex flex-col hover:border-indigo-300 transition-colors shadow-sm group">
            
            {/* Header: Identity & Turns */}
            <div className="p-4 border-b border-slate-100 flex items-start justify-between bg-slate-50/50 rounded-t-[4px]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold shadow-inner flex-shrink-0">
                  {initials}
                </div>
                <div>
                  <h3 className="font-bold text-slate-800 text-sm tracking-tight">{speaker.name}</h3>
                  <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">{speaker.role}</p>
                </div>
              </div>
              <div className="bg-white border border-slate-200 rounded-[4px] px-2 py-1 flex flex-col items-center shadow-sm">
                <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-0.5">Turns</span>
                <div className="flex items-center gap-1 text-xs font-bold text-indigo-700">
                  <MessageCircle size={12} className="text-indigo-400" />
                  {speaker.turnCount}
                </div>
              </div>
            </div>

            {/* Metrics Section */}
            <div className="p-4 flex flex-col gap-5 flex-1">
              
              {/* Sentiment Bar */}
              <div>
                <div className="flex justify-between text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                  <span className="flex items-center gap-1"><TrendingUp size={10} /> Average Sentiment</span>
                  <span className="text-slate-500">
                    <span className="text-emerald-600">+{speaker.avgSentiment.pos}</span> / <span className="text-rose-600">-{speaker.avgSentiment.neg}</span>
                  </span>
                </div>
                <div className="w-full h-2 rounded-[2px] overflow-hidden flex bg-slate-100 border border-slate-200 shadow-inner">
                  <div style={{ width: `${speaker.avgSentiment.pos}%` }} className="bg-emerald-400 border-r border-emerald-500/30" title={`Positive: ${speaker.avgSentiment.pos}%`} />
                  <div style={{ width: `${speaker.avgSentiment.neu}%` }} className="bg-slate-300" title={`Neutral: ${speaker.avgSentiment.neu}%`} />
                  <div style={{ width: `${speaker.avgSentiment.neg}%` }} className="bg-rose-400 border-l border-rose-500/30" title={`Negative: ${speaker.avgSentiment.neg}%`} />
                </div>
              </div>

              {/* Dominant Pattern (Emotion & Signal) */}
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1.5">
                  <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                    <Brain size={10} /> Primary Emotion
                  </span>
                  <div className={`px-2 py-1 text-[11px] font-bold rounded-[3px] border inline-flex items-center justify-center text-center ${emoColor}`}>
                    {speaker.primaryEmotion}
                  </div>
                </div>
                <div className="flex flex-col gap-1.5">
                  <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                    <Zap size={10} /> Primary Signal
                  </span>
                  <div className={`px-2 py-1 text-[11px] font-bold rounded-[3px] border inline-flex items-center justify-center text-center ${sigColor}`}>
                    {speaker.primarySignal}
                  </div>
                </div>
              </div>

              {/* Emerging Emotions */}
              <div className="flex flex-col gap-1.5">
                <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                  <Sparkles size={10} /> Emerging Sub-Emotions
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {speaker.emergingEmotions.map((emotion, idx) => (
                    <span key={idx} className="px-2 py-0.5 text-[10px] font-bold text-slate-600 bg-white border border-slate-200 shadow-sm rounded-[2px] uppercase tracking-wide">
                      {emotion}
                    </span>
                  ))}
                </div>
              </div>

            </div>

            {/* AI Analytical Summary */}
            <div className="p-4 bg-slate-50 border-t border-slate-100 rounded-b-[4px] mt-auto">
              <span className="text-[9px] font-bold text-indigo-500 uppercase tracking-widest mb-1.5 block">AI Pattern Analysis</span>
              <p className="text-xs text-slate-700 leading-relaxed font-medium border-l-[3px] border-indigo-300 pl-2.5">
                {speaker.summary}
              </p>
            </div>

          </div>
        );
      })}
    </div>
  );
}
