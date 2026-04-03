import React from "react";
import { AlertCircle, BarChart, Hash, Heart, MessageSquare, TrendingUp } from "lucide-react";
import {
  formatSentimentLabel,
  type MeetingTurn,
} from "../../lib/meetingDashboard";

interface DetailPanelProps {
  turn: MeetingTurn | null;
}

export function DetailPanel({ turn }: DetailPanelProps) {
  if (!turn) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center text-slate-400 bg-slate-50">
        <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4 border border-slate-200 shadow-sm">
          <BarChart size={24} className="text-slate-300" />
        </div>
        <h3 className="text-sm font-bold text-slate-600 mb-2">No Turn Selected</h3>
        <p className="text-xs font-medium text-slate-500 leading-relaxed max-w-[200px]">
          타임라인에서 발화를 선택해 상세 분석을 확인하세요.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white relative">
      <div className="p-5 border-b border-slate-200 bg-slate-50 z-10 flex-shrink-0">
        <div className="flex justify-between items-start mb-3">
          <span className="bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-[2px] text-[10px] font-bold border border-indigo-100 flex items-center gap-1 uppercase tracking-wider">
            <Hash size={10} /> Turn {turn.order}
          </span>
          <span className="text-[10px] font-mono font-bold text-slate-400 border border-slate-200 px-1.5 py-0.5 rounded-[2px] bg-white">
            {turn.turnId}
          </span>
        </div>

        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-sm bg-indigo-100 flex items-center justify-center text-indigo-600 border border-indigo-200 font-bold text-sm">
            {turn.agentLabel.charAt(0) || "A"}
          </div>
          <div>
            <h3 className="font-bold text-slate-800 text-sm">{turn.agentLabel}</h3>
            <p className="text-[10px] text-slate-500 font-bold tracking-wide">에이전트</p>
          </div>
        </div>
      </div>

      <div className="p-5 space-y-6 flex-1 overflow-y-auto bg-slate-50">
        <section>
          <h4 className="text-[10px] font-bold text-slate-400 tracking-wide flex items-center gap-1.5 mb-1.5">
            <MessageSquare size={12} /> 발화 원문
          </h4>
          <div className="bg-white border border-slate-200 rounded-[2px] p-3.5 text-xs text-slate-700 leading-relaxed relative">
            <div className="absolute top-0 left-0 w-0.5 h-full bg-indigo-400" />
            "{turn.text}"
          </div>
        </section>

        <section>
            <div className="flex justify-between items-center mb-1.5">
            <h4 className="text-[10px] font-bold text-slate-400 tracking-wide flex items-center gap-1.5">
              <Heart size={12} /> 감정 분류
            </h4>
            <span className="text-[10px] font-bold bg-white px-1.5 py-0.5 rounded-[2px] border border-slate-200 text-slate-600 font-mono">
              {formatSentimentLabel(turn.sentimentLabel)}
            </span>
          </div>
          <div className="bg-white border border-slate-200 rounded-[2px] p-3">
            <div className="h-1.5 w-full bg-slate-100 rounded-[1px] overflow-hidden flex mb-2">
              <div
                className={
                  turn.sentimentLabel === "POS"
                    ? "bg-emerald-400"
                    : turn.sentimentLabel === "NEG"
                      ? "bg-rose-400"
                      : "bg-slate-400"
                }
                style={{ width: `${Math.round(turn.sentimentConfidence * 100)}%` }}
              />
            </div>
            <div className="flex justify-between text-[9px] font-bold text-slate-500 tracking-wide">
              <span>신뢰도</span>
              <span>{Math.round(turn.sentimentConfidence * 100)}%</span>
            </div>
            <div className="mt-3 text-[11px] text-slate-600 leading-relaxed">
              수치 기반 턴 감정 분류 결과입니다.
            </div>
          </div>
        </section>

        <section className="grid grid-cols-2 gap-3">
          <div className="bg-white border border-slate-200 rounded-[2px] p-3">
            <h4 className="text-[9px] font-bold text-slate-400 tracking-wide mb-1">
              대표 감정
            </h4>
            <div className="text-sm font-bold text-slate-800">{turn.dominantEmotion}</div>
          </div>
          <div className="bg-white border border-slate-200 rounded-[2px] p-3">
            <h4 className="text-[9px] font-bold text-slate-400 tracking-wide mb-1">
              대표 시그널
            </h4>
            <div className="text-sm font-bold text-indigo-700">{turn.dominantSignal}</div>
          </div>
        </section>

        <section>
          <h4 className="text-[10px] font-bold text-slate-400 tracking-wide flex items-center gap-1.5 mb-2">
            <BarChart size={12} /> 루브릭
          </h4>
          <div className="grid grid-cols-3 gap-3">
            {[
              ["Dominance", turn.rubric.dominance],
              ["Efficiency", turn.rubric.efficiency],
              ["Cohesion", turn.rubric.cohesion],
            ].map(([label, value]) => (
              <div key={label} className="bg-white border border-slate-200 rounded-[2px] p-3">
                <h4 className="text-[9px] font-bold text-slate-400 tracking-wide mb-1">{label}</h4>
                <div className="text-sm font-bold text-slate-800">{value}</div>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h4 className="text-[10px] font-bold text-slate-400 tracking-wide flex items-center gap-1.5 mb-2">
            <TrendingUp size={12} /> 시그널 분포
          </h4>
          <div className="space-y-3 bg-white border border-slate-200 rounded-[2px] p-3">
            {Object.entries(turn.meetingSignals).map(([key, value]) => (
              <div key={key}>
                <div className="flex justify-between text-[10px] font-bold text-slate-600 mb-1 tracking-wide">
                  <span>{key}</span>
                  <span className={value > 70 ? "text-rose-500" : "text-slate-400"}>{value}</span>
                </div>
                <div className="w-full bg-slate-100 h-1 overflow-hidden">
                  <div
                    className={`h-1 ${
                      key === "tension" && value > 70
                        ? "bg-rose-500"
                        : key === "urgency" && value > 70
                          ? "bg-orange-500"
                          : "bg-indigo-400"
                    }`}
                    style={{ width: `${value}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>

        {turn.emergingEmotions.length > 0 && (
          <section>
            <h4 className="text-[10px] font-bold text-slate-400 tracking-wide flex items-center gap-1.5 mb-2">
              <AlertCircle size={12} /> 부가 감정 신호
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {turn.emergingEmotions.map((emotion, index) => (
                <span
                  key={`${emotion}-${index}`}
                  className="bg-white border border-slate-200 px-2 py-0.5 text-[9px] font-bold text-slate-600 uppercase tracking-widest"
                >
                  {emotion}
                </span>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
