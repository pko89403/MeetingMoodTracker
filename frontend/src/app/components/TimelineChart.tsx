import React, { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea
} from "recharts";
import { AlertTriangle, TrendingDown } from "lucide-react";
import { Turn } from "../../mockData";

interface TimelineChartProps {
  turns: Turn[];
  view: "signals" | "emotions";
  onSelectTurn: (turnId: string) => void;
  selectedTurnId: string | null;
}

const SIGNAL_COLORS = {
  tension: "#ef4444", // red
  alignment: "#22c55e", // emerald
  urgency: "#f97316", // orange
  clarity: "#0ea5e9", // sky blue
  engagement: "#8b5cf6", // violet
};

const EMOTION_COLORS = {
  joy: "#eab308",         // yellow
  anger: "#dc2626",       // red
  anxiety: "#9333ea",     // purple  (was fear)
  sadness: "#3b82f6",     // blue
  excitement: "#f43f5e",  // rose    (was surprise)
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const turn = payload[0].payload as Turn;
    if (!turn) return null;
    return (
      <div className="bg-slate-900 border border-slate-700 shadow-2xl rounded-sm p-3 max-w-[280px] pointer-events-none z-50">
        <div className="flex justify-between items-center mb-2 pb-2 border-b border-slate-700">
          <span className="font-bold text-white text-[11px] uppercase tracking-wider">Turn {turn.order}</span>
          <span className="bg-slate-800 text-slate-300 text-[10px] px-2 py-0.5 rounded-[2px] font-bold uppercase tracking-wider border border-slate-700">
            {turn.speaker_id ? turn.speaker_id.replace('spk_', 'Speaker ') : 'Speaker'}
          </span>
        </div>
        {turn.text && (
          <p className="text-slate-300 text-xs leading-relaxed italic border-l-[3px] border-indigo-500 pl-2.5 mb-3 font-medium">
            "{turn.text.substring(0, 60)}..."
          </p>
        )}
        <div className="grid grid-cols-2 gap-x-4 gap-y-1">
          {payload.map((entry: any, index: number) => (
             <div key={index} className="flex justify-between items-center text-[10px] font-bold">
              <span style={{ color: entry.color }} className="uppercase tracking-wider opacity-90">{entry.name}</span>
              <span className="text-white ml-2">{entry.value}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }
  return null;
};

export function TimelineChart({ turns = [], view = "signals", onSelectTurn, selectedTurnId }: TimelineChartProps) {
  if (!turns || turns.length === 0) return <div className="w-full h-full flex items-center justify-center">No data</div>;

  const data = turns.map((t) => {
    if (view === "signals") {
      return { ...t, ...(t.meetingSignals || {}), isSelected: t.turn_id === selectedTurnId };
    } else {
      return { ...t, ...(t.baseEmotions || {}), isSelected: t.turn_id === selectedTurnId };
    }
  });

  const isSelectedActive = Boolean(selectedTurnId);
  const selectedTurnData = selectedTurnId ? turns.find(t => t.turn_id === selectedTurnId) : null;

  const anomalies = useMemo(() => {
    const tensionAreas: { start: number; end: number }[] = [];
    const clarityAreas: { start: number; end: number }[] = [];
    
    if (view === "signals") {
      let inTension = false;
      let startTension = 0;
      
      let inClarity = false;
      let startClarity = 0;

      turns.forEach((t, i) => {
        if (!t.meetingSignals) return;

        if (t.meetingSignals.tension >= 70) {
          if (!inTension) {
            inTension = true;
            startTension = t.order;
          }
        } else {
          if (inTension && i > 0) {
            tensionAreas.push({ start: startTension, end: turns[i - 1].order });
            inTension = false;
          }
        }

        if (t.meetingSignals.clarity <= 50) {
          if (!inClarity) {
            inClarity = true;
            startClarity = t.order;
          }
        } else {
          if (inClarity && i > 0) {
            clarityAreas.push({ start: startClarity, end: turns[i - 1].order });
            inClarity = false;
          }
        }
      });

      if (inTension && turns.length > 0) tensionAreas.push({ start: startTension, end: turns[turns.length - 1].order });
      if (inClarity && turns.length > 0) clarityAreas.push({ start: startClarity, end: turns[turns.length - 1].order });
    }
    
    return { tensionAreas, clarityAreas };
  }, [turns, view]);

  return (
    <div className="w-full h-full flex flex-col">
      <div className="flex-1 w-full h-[400px] min-h-[400px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{ top: 30, right: 20, left: -20, bottom: 20 }}
            onClick={(e) => {
              if (e && e.activePayload && e.activePayload.length > 0) {
                onSelectTurn(e.activePayload[0].payload.turn_id);
              }
            }}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
            <XAxis 
               dataKey="order" 
               axisLine={{ stroke: '#cbd5e1', strokeWidth: 1 }} 
               tickLine={false} 
               tick={{ fill: "#64748b", fontSize: 10, fontWeight: 700 }} 
               dy={10}
               label={{ value: 'TURN SEQUENCE', position: 'insideBottom', offset: -15, fill: '#94a3b8', fontSize: 10, fontWeight: 700, letterSpacing: 1 }}
            />
            <YAxis 
               axisLine={false} 
               tickLine={false} 
               tick={{ fill: "#64748b", fontSize: 10, fontWeight: 700 }}
               domain={[0, 100]}
               ticks={[0, 25, 50, 75, 100]}
            />
            <RechartsTooltip 
               content={<CustomTooltip />} 
               cursor={{ stroke: '#94a3b8', strokeWidth: 1, strokeDasharray: '4 4' }} 
               isAnimationActive={false}
            />

            {view === "signals" && anomalies.tensionAreas.map((area, idx) => (
              <ReferenceArea 
                key={`tension-${idx}`} 
                x1={area.start === area.end ? area.start - 0.5 : area.start} 
                x2={area.end === area.start ? area.end + 0.5 : area.end} 
                fill="#fee2e2" 
                fillOpacity={0.5} 
                y1={0} y2={100}
              />
            ))}
            {view === "signals" && anomalies.clarityAreas.map((area, idx) => (
              <ReferenceArea 
                key={`clarity-${idx}`} 
                x1={area.start === area.end ? area.start - 0.5 : area.start} 
                x2={area.end === area.start ? area.end + 0.5 : area.end} 
                fill="#e0f2fe" 
                fillOpacity={0.5} 
                y1={0} y2={100}
              />
            ))}

            {selectedTurnData && selectedTurnData.order !== undefined && (
               <ReferenceLine x={selectedTurnData.order} stroke="#6366f1" strokeWidth={2} opacity={0.6} strokeDasharray="3 3" />
            )}

            {view === "signals" ? (
              <>
                <Line type="linear" dataKey="tension" name="Tension" stroke={SIGNAL_COLORS.tension} strokeWidth={3} dot={{ r: 3, strokeWidth: 2 }} activeDot={{ r: 6, strokeWidth: 2, fill: "#fff", stroke: SIGNAL_COLORS.tension }} opacity={isSelectedActive ? 0.3 : 1} />
                <Line type="linear" dataKey="clarity" name="Clarity" stroke={SIGNAL_COLORS.clarity} strokeWidth={2.5} dot={{ r: 3, strokeWidth: 1 }} activeDot={{ r: 5, fill: "#fff", stroke: SIGNAL_COLORS.clarity }} opacity={isSelectedActive ? 0.3 : 0.9} />
                <Line type="linear" dataKey="alignment" name="Alignment" stroke={SIGNAL_COLORS.alignment} strokeWidth={2} dot={{ r: 2 }} activeDot={{ r: 5 }} opacity={isSelectedActive ? 0.3 : 0.8} />
                <Line type="linear" dataKey="urgency" name="Urgency" stroke={SIGNAL_COLORS.urgency} strokeWidth={2} strokeDasharray="5 5" dot={{ r: 2 }} activeDot={{ r: 5 }} opacity={isSelectedActive ? 0.3 : 0.7} />
                <Line type="linear" dataKey="engagement" name="Engagement" stroke={SIGNAL_COLORS.engagement} strokeWidth={1.5} dot={{ r: 2 }} activeDot={{ r: 5 }} opacity={isSelectedActive ? 0.2 : 0.5} />
              </>
            ) : (
              <>
                <Line type="linear" dataKey="joy" name="Joy" stroke={EMOTION_COLORS.joy} strokeWidth={2.5} dot={{ r: 3 }} activeDot={{ r: 6 }} opacity={isSelectedActive ? 0.3 : 1} />
                <Line type="linear" dataKey="anger" name="Anger" stroke={EMOTION_COLORS.anger} strokeWidth={2.5} dot={{ r: 3 }} activeDot={{ r: 6 }} opacity={isSelectedActive ? 0.3 : 1} />
                <Line type="linear" dataKey="anxiety" name="Anxiety" stroke={EMOTION_COLORS.anxiety} strokeWidth={2} dot={{ r: 2 }} activeDot={{ r: 5 }} opacity={isSelectedActive ? 0.3 : 0.8} />
                <Line type="linear" dataKey="sadness" name="Sadness" stroke={EMOTION_COLORS.sadness} strokeWidth={2} dot={{ r: 2 }} activeDot={{ r: 5 }} opacity={isSelectedActive ? 0.3 : 0.8} />
                <Line type="linear" dataKey="excitement" name="Excitement" stroke={EMOTION_COLORS.excitement} strokeWidth={1.5} strokeDasharray="4 4" dot={{ r: 2 }} activeDot={{ r: 5 }} opacity={isSelectedActive ? 0.2 : 0.6} />
              </>
            )}

          </LineChart>
        </ResponsiveContainer>
      </div>
      
      <div className="flex flex-col sm:flex-row items-center justify-between mt-6 pt-4 border-t border-slate-100 gap-4">
        <div className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2">
          {view === "signals" 
            ? Object.entries(SIGNAL_COLORS).map(([key, color]) => (
              <div key={key} className="flex items-center gap-1.5 cursor-pointer hover:opacity-80 transition-opacity">
                {key === 'urgency' ? (
                   <div className="w-4 border-t-2 border-dashed" style={{ borderColor: color }} />
                ) : (
                   <div className={`h-1.5 rounded-sm ${key === 'tension' ? 'w-4' : key === 'clarity' ? 'w-3.5' : 'w-3'}`} style={{ backgroundColor: color }} />
                )}
                <span className="text-[10px] text-slate-600 font-bold uppercase tracking-wider">{key}</span>
              </div>
            ))
            : Object.entries(EMOTION_COLORS).map(([key, color]) => (
              <div key={key} className="flex items-center gap-1.5 cursor-pointer hover:opacity-80 transition-opacity">
                {key === 'excitement' ? (
                   <div className="w-3 border-t-[1.5px] border-dashed" style={{ borderColor: color }} />
                ) : (
                   <div className="w-3 h-1.5 rounded-sm" style={{ backgroundColor: color }} />
                )}
                <span className="text-[10px] text-slate-600 font-bold uppercase tracking-wider">{key}</span>
              </div>
            ))
          }
        </div>

        {view === "signals" && (
           <div className="flex items-center gap-4 bg-slate-50 px-3 py-1.5 rounded-sm border border-slate-200">
             <div className="flex items-center gap-1.5 text-[10px] font-bold text-rose-700 uppercase tracking-wider">
                <AlertTriangle size={12} className="text-rose-500" />
                <span className="flex items-center gap-1"><span className="w-2 h-2 bg-red-100 border border-red-200 rounded-sm inline-block"></span>Tension Spike</span>
             </div>
             <div className="flex items-center gap-1.5 text-[10px] font-bold text-sky-700 uppercase tracking-wider">
                <TrendingDown size={12} className="text-sky-500" />
                <span className="flex items-center gap-1"><span className="w-2 h-2 bg-sky-100 border border-sky-200 rounded-sm inline-block"></span>Clarity Drop</span>
             </div>
           </div>
        )}
      </div>
    </div>
  );
}
