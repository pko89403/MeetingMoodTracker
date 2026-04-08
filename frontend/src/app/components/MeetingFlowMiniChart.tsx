import React, { useMemo, useState } from "react";
import type { ApexOptions } from "apexcharts";
import Chart from "react-apexcharts";
import { Activity, BarChart3 } from "lucide-react";
import {
  toTurnSentimentDistribution,
  type MeetingTurn,
} from "../../lib/meetingDashboard";
import { cn } from "./ui/utils";

type MiniChartView = "sentiment" | "emotions" | "signals" | "rubric";

const VIEW_META: Record<
  MiniChartView,
  {
    label: string;
    description: string;
    series: Array<{ key: string; label: string; color: string }>;
  }
> = {
  sentiment: {
    label: "긍부정",
    description: "positive / neutral / negative 흐름",
    series: [
      { key: "pos", label: "Positive", color: "#10b981" },
      { key: "neu", label: "Neutral", color: "#94a3b8" },
      { key: "neg", label: "Negative", color: "#f43f5e" },
    ],
  },
  emotions: {
    label: "기본 감정",
    description: "joy / neutral / anxiety / frustration",
    series: [
      { key: "joy", label: "Joy", color: "#facc15" },
      { key: "neutral", label: "Neutral", color: "#94a3b8" },
      { key: "anxiety", label: "Anxiety", color: "#a855f7" },
      { key: "frustration", label: "Frustration", color: "#f97316" },
    ],
  },
  signals: {
    label: "회의 시그널",
    description: "engagement / clarity / tension",
    series: [
      { key: "engagement", label: "Engagement", color: "#8b5cf6" },
      { key: "clarity", label: "Clarity", color: "#38bdf8" },
      { key: "tension", label: "Tension", color: "#fb7185" },
    ],
  },
  rubric: {
    label: "종합 시그널",
    description: "dominance / efficiency / cohesion",
    series: [
      { key: "dominance", label: "Dominance", color: "#6366f1" },
      { key: "efficiency", label: "Efficiency", color: "#10b981" },
      { key: "cohesion", label: "Cohesion", color: "#f59e0b" },
    ],
  },
};

function getTurnMetricValue(turn: MeetingTurn, view: MiniChartView, key: string) {
  if (view === "sentiment") {
    const distribution = toTurnSentimentDistribution(turn.sentimentLabel, turn.sentimentConfidence);
    return distribution[key as keyof typeof distribution];
  }

  if (view === "signals") {
    return turn.meetingSignals[key as keyof typeof turn.meetingSignals];
  }

  if (view === "emotions") {
    return turn.baseEmotions[key as keyof typeof turn.baseEmotions];
  }

  return turn.rubric[key as keyof typeof turn.rubric];
}

export function MeetingFlowMiniChart({
  turns,
  selectedTurnId,
  selectedAgentLabel,
  isLoading,
  onSelectTurn,
  variant = "compact",
  testId = "flow-mini-chart",
}: {
  turns: MeetingTurn[];
  selectedTurnId: string | null;
  selectedAgentLabel?: string;
  isLoading: boolean;
  onSelectTurn: (turnId: string) => void;
  variant?: "compact" | "page";
  testId?: string;
}) {
  const [view, setView] = useState<MiniChartView>("sentiment");
  const viewMeta = VIEW_META[view];
  const selectedTurn =
    selectedTurnId === null ? null : turns.find((turn) => turn.turnId === selectedTurnId) ?? null;

  const series = useMemo(
    () =>
      viewMeta.series.map((seriesMeta) => ({
        name: seriesMeta.label,
        data: turns.map((turn) => ({
          x: turn.order,
          y: getTurnMetricValue(turn, view, seriesMeta.key),
        })),
      })),
    [turns, view, viewMeta.series],
  );

  const chartHeight = variant === "page" ? 360 : 176;

  const options = useMemo<ApexOptions>(
    () => ({
      chart: {
        id: "meeting-flow-mini-chart",
        type: "line",
        height: chartHeight,
        background: "transparent",
        toolbar: { show: false },
        zoom: { enabled: false },
        sparkline: { enabled: false },
        animations: { enabled: false },
        fontFamily: "inherit",
        events: {
          dataPointSelection: (_event, _chart, config) => {
            const turn = turns[config.dataPointIndex];
            if (turn) {
              onSelectTurn(turn.turnId);
            }
          },
        },
      },
      stroke: {
        curve: "smooth",
        width: viewMeta.series.map((_, index) => (index === 0 ? 2.8 : index === 1 ? 2.4 : index === 2 ? 2.1 : 1.8)),
      },
      colors: viewMeta.series.map((item) => item.color),
      dataLabels: { enabled: false },
      legend: { show: false },
      markers: {
        size: 0,
        hover: { size: 5 },
      },
      grid: {
        borderColor: "rgba(255,255,255,0.08)",
        strokeDashArray: 4,
        padding:
          variant === "page"
            ? { top: 8, right: 20, bottom: 8, left: 8 }
            : { top: 0, right: 12, bottom: -8, left: 4 },
      },
      xaxis: {
        type: "numeric",
        labels: {
          style: {
            colors: "#64748b",
            fontSize: "10px",
            fontWeight: 600,
          },
          formatter: (value) => `${Math.round(Number(value))}`,
        },
        axisBorder: { show: false },
        axisTicks: { show: false },
        tooltip: { enabled: false },
      },
      yaxis: {
        min: 0,
        max: 100,
        tickAmount: 4,
        labels: {
          style: {
            colors: "#64748b",
            fontSize: "10px",
            fontWeight: 600,
          },
        },
      },
      tooltip: {
        theme: "dark",
        shared: true,
        intersect: false,
      },
      annotations: {
        xaxis: selectedTurn
          ? [
              {
                x: selectedTurn.order,
                borderColor: "#c64aff",
                strokeDashArray: 4,
                opacity: 0.8,
              },
            ]
          : [],
      },
      noData: {
        text: isLoading ? "Loading..." : "No turns",
        align: "center",
        verticalAlign: "middle",
        style: {
          color: "#94a3b8",
          fontSize: "12px",
        },
      },
    }),
    [chartHeight, isLoading, onSelectTurn, selectedTurn, turns, variant, viewMeta.series],
  );

  return (
    <div
      data-testid={testId}
      className={cn(
        "pointer-events-auto rounded-[24px] border border-white/10 bg-[#141416]/88 p-4 text-white shadow-[0_24px_80px_-40px_rgba(15,23,42,0.85)] backdrop-blur-xl",
        variant === "page" ? "min-h-[460px]" : "flex-1",
      )}
    >
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.28em] text-violet-200/70">
            <BarChart3 size={13} />
            {variant === "page" ? "Timeline page" : "Timeline mini chart"}
          </div>
          <h2 className="mt-2 text-lg font-medium tracking-tight text-white">
            {viewMeta.label} {variant === "page" ? "explorer" : "overlay"}
          </h2>
          <p className="mt-1 text-xs text-slate-400">
            {viewMeta.description}
            {selectedAgentLabel ? ` · ${selectedAgentLabel} lane focus` : " · 전체 turn 흐름"}
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          {(Object.keys(VIEW_META) as MiniChartView[]).map((item) => (
            <button
              key={item}
              type="button"
              data-testid={`flow-mini-chart-tab-${item}`}
              aria-pressed={view === item}
              onClick={() => setView(item)}
              className={cn(
                "rounded-full border px-3 py-1.5 text-xs font-semibold transition",
                view === item
                  ? "border-violet-400/60 bg-violet-500/20 text-white"
                  : "border-white/10 bg-white/6 text-slate-300 hover:bg-white/12",
              )}
            >
              {VIEW_META[item].label}
            </button>
          ))}
        </div>
      </div>

      <div className={cn("mt-4", variant === "page" ? "h-[360px]" : "h-[176px]")}>
        <Chart options={options} series={series} type="line" height={chartHeight} />
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        {viewMeta.series.map((item) => (
          <span
            key={item.key}
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/6 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-300"
          >
            <span className="h-2 w-2 rounded-full" style={{ backgroundColor: item.color }} />
            {item.label}
          </span>
        ))}
        {selectedTurn && (
          <span className="inline-flex items-center gap-2 rounded-full border border-fuchsia-400/25 bg-fuchsia-500/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-fuchsia-100">
            <Activity size={11} />
            Turn {selectedTurn.order} selected
          </span>
        )}
      </div>
    </div>
  );
}
