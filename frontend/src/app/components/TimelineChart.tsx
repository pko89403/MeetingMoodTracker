import React, { useEffect, useMemo, useState } from "react";
import type { ApexOptions } from "apexcharts";
import Chart from "react-apexcharts";
import { AlertTriangle, TrendingDown } from "lucide-react";
import {
  toTurnSentimentDistribution,
  type MeetingTurn,
} from "../../lib/meetingDashboard";

interface TimelineChartProps {
  turns: MeetingTurn[];
  view: "signals" | "emotions" | "sentiment" | "rubric";
  onSelectTurn: (turnId: string) => void;
  selectedTurnId: string | null;
}

const SIGNAL_COLORS = {
  tension: "#ef4444",
  alignment: "#22c55e",
  urgency: "#f97316",
  clarity: "#0ea5e9",
  engagement: "#8b5cf6",
};

const EMOTION_COLORS = {
  joy: "#eab308",
  anger: "#dc2626",
  anxiety: "#9333ea",
  sadness: "#3b82f6",
  neutral: "#64748b",
  frustration: "#f97316",
  excitement: "#f43f5e",
  confusion: "#14b8a6",
};

const RUBRIC_COLORS = {
  dominance: "#6366f1",
  efficiency: "#10b981",
  cohesion: "#f59e0b",
};

const SENTIMENT_COLORS = {
  positive: "#10b981",
  neutral: "#64748b",
  negative: "#ef4444",
};

type SeriesConfig = {
  key: string;
  name: string;
  color: string;
  strokeWidth: number;
  dashArray?: number;
};

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function getSeriesConfig(view: TimelineChartProps["view"]): SeriesConfig[] {
  if (view === "signals") {
    return [
      { key: "tension", name: "Tension", color: SIGNAL_COLORS.tension, strokeWidth: 3 },
      { key: "clarity", name: "Clarity", color: SIGNAL_COLORS.clarity, strokeWidth: 2.5 },
      { key: "alignment", name: "Alignment", color: SIGNAL_COLORS.alignment, strokeWidth: 2 },
      { key: "urgency", name: "Urgency", color: SIGNAL_COLORS.urgency, strokeWidth: 2, dashArray: 5 },
      { key: "engagement", name: "Engagement", color: SIGNAL_COLORS.engagement, strokeWidth: 1.5 },
    ];
  }

  if (view === "emotions") {
    return [
      { key: "joy", name: "Joy", color: EMOTION_COLORS.joy, strokeWidth: 2.5 },
      { key: "anger", name: "Anger", color: EMOTION_COLORS.anger, strokeWidth: 2.5 },
      { key: "anxiety", name: "Anxiety", color: EMOTION_COLORS.anxiety, strokeWidth: 2 },
      { key: "sadness", name: "Sadness", color: EMOTION_COLORS.sadness, strokeWidth: 2 },
      { key: "neutral", name: "Neutral", color: EMOTION_COLORS.neutral, strokeWidth: 2 },
      { key: "frustration", name: "Frustration", color: EMOTION_COLORS.frustration, strokeWidth: 1.75 },
      { key: "confusion", name: "Confusion", color: EMOTION_COLORS.confusion, strokeWidth: 1.75 },
      { key: "excitement", name: "Excitement", color: EMOTION_COLORS.excitement, strokeWidth: 1.5, dashArray: 4 },
    ];
  }

  if (view === "sentiment") {
    return [
      { key: "pos", name: "Positive", color: SENTIMENT_COLORS.positive, strokeWidth: 3 },
      { key: "neu", name: "Neutral", color: SENTIMENT_COLORS.neutral, strokeWidth: 2.5 },
      { key: "neg", name: "Negative", color: SENTIMENT_COLORS.negative, strokeWidth: 2.5 },
    ];
  }

  return [
    { key: "dominance", name: "Dominance", color: RUBRIC_COLORS.dominance, strokeWidth: 3 },
    { key: "efficiency", name: "Efficiency", color: RUBRIC_COLORS.efficiency, strokeWidth: 2.5 },
    { key: "cohesion", name: "Cohesion", color: RUBRIC_COLORS.cohesion, strokeWidth: 2.25 },
  ];
}

export function TimelineChart({
  turns = [],
  view = "signals",
  onSelectTurn,
  selectedTurnId,
}: TimelineChartProps) {
  const seriesConfig = useMemo(() => getSeriesConfig(view), [view]);
  const allSeriesKeys = useMemo(
    () => seriesConfig.map((config) => config.key),
    [seriesConfig],
  );
  const [visibleSeriesKeys, setVisibleSeriesKeys] = useState<string[]>(allSeriesKeys);

  useEffect(() => {
    setVisibleSeriesKeys(allSeriesKeys);
  }, [allSeriesKeys]);

  const data = useMemo(
    () =>
      turns.map((turn) =>
        view === "signals"
          ? { ...turn, ...turn.meetingSignals }
          : view === "emotions"
            ? { ...turn, ...turn.baseEmotions }
            : view === "sentiment"
              ? {
                  ...turn,
                  ...toTurnSentimentDistribution(
                    turn.sentimentLabel,
                    turn.sentimentConfidence,
                  ),
                }
              : { ...turn, ...turn.rubric },
      ),
    [turns, view],
  );

  const filteredSeriesConfig = useMemo(
    () => seriesConfig.filter((config) => visibleSeriesKeys.includes(config.key)),
    [seriesConfig, visibleSeriesKeys],
  );

  const series = useMemo(
    () =>
      filteredSeriesConfig.map((config) => ({
        name: config.name,
        data: data.map((turn) => ({
          x: turn.order,
          y: (turn as Record<string, number>)[config.key],
        })),
      })),
    [data, filteredSeriesConfig],
  );

  const chartWidth = Math.max(turns.length * 110, 720);
  const selectedTurnData = selectedTurnId
    ? turns.find((turn) => turn.turnId === selectedTurnId) ?? null
    : null;

  const signalAnnotations = useMemo(() => {
    if (view !== "signals") {
      return [];
    }

    const annotations: ApexOptions["annotations"] = { xaxis: [] };
    let tensionStart: number | null = null;
    let clarityStart: number | null = null;

    turns.forEach((turn, index) => {
      if (turn.meetingSignals.tension >= 70 && tensionStart === null) {
        tensionStart = turn.order;
      }
      if (turn.meetingSignals.tension < 70 && tensionStart !== null) {
        annotations.xaxis?.push({
          x: tensionStart,
          x2: turns[index - 1].order,
          fillColor: "#fee2e2",
          opacity: 0.5,
          borderColor: "transparent",
        });
        tensionStart = null;
      }

      if (turn.meetingSignals.clarity <= 50 && clarityStart === null) {
        clarityStart = turn.order;
      }
      if (turn.meetingSignals.clarity > 50 && clarityStart !== null) {
        annotations.xaxis?.push({
          x: clarityStart,
          x2: turns[index - 1].order,
          fillColor: "#e0f2fe",
          opacity: 0.5,
          borderColor: "transparent",
        });
        clarityStart = null;
      }
    });

    if (tensionStart !== null && turns.length > 0) {
      annotations.xaxis?.push({
        x: tensionStart,
        x2: turns[turns.length - 1].order,
        fillColor: "#fee2e2",
        opacity: 0.5,
        borderColor: "transparent",
      });
    }

    if (clarityStart !== null && turns.length > 0) {
      annotations.xaxis?.push({
        x: clarityStart,
        x2: turns[turns.length - 1].order,
        fillColor: "#e0f2fe",
        opacity: 0.5,
        borderColor: "transparent",
      });
    }

    return annotations.xaxis ?? [];
  }, [turns, view]);

  const isFiltered = visibleSeriesKeys.length !== allSeriesKeys.length;

  function restoreAllSeries() {
    setVisibleSeriesKeys(allSeriesKeys);
  }

  function handleLegendClick(metricKey: string) {
    setVisibleSeriesKeys((currentKeys) => {
      if (currentKeys.length === allSeriesKeys.length) {
        return [metricKey];
      }

      if (currentKeys.includes(metricKey)) {
        if (currentKeys.length === 1) {
          return allSeriesKeys;
        }

        return currentKeys.filter((key) => key !== metricKey);
      }

      return [...currentKeys, metricKey];
    });
  }

  const options = useMemo<ApexOptions>(
    () => ({
      chart: {
        id: "meeting-timeline-chart",
        type: "line",
        height: 380,
        toolbar: { show: false },
        zoom: { enabled: false },
        animations: { enabled: false },
        fontFamily: "inherit",
        events: {
          dataPointSelection: (_event, _chartContext, config) => {
            const pointIndex = config.dataPointIndex;
            if (pointIndex >= 0 && turns[pointIndex]) {
              onSelectTurn(turns[pointIndex].turnId);
            }
          },
        },
      },
      stroke: {
        curve: "straight",
        width: filteredSeriesConfig.map((config) => config.strokeWidth),
        dashArray: filteredSeriesConfig.map((config) => config.dashArray ?? 0),
      },
      colors: filteredSeriesConfig.map((config) => config.color),
      grid: {
        borderColor: "#e2e8f0",
        strokeDashArray: 3,
        padding: { top: 8, right: 24, bottom: 8, left: 8 },
      },
      dataLabels: { enabled: false },
      markers: {
        size: 4,
        strokeWidth: 2,
        hover: { size: 6 },
      },
      xaxis: {
        type: "numeric",
        tickAmount: Math.min(Math.max(turns.length - 1, 1), 10),
        labels: {
          style: {
            colors: "#64748b",
            fontSize: "10px",
            fontWeight: 700,
          },
          formatter: (value) => `${Math.round(Number(value))}`,
        },
        title: {
          text: "TURN SEQUENCE",
          style: {
            color: "#94a3b8",
            fontSize: "10px",
            fontWeight: 700,
          },
        },
        axisBorder: { color: "#cbd5e1" },
        axisTicks: { show: false },
      },
      yaxis: {
        min: 0,
        max: 100,
        tickAmount: 4,
        labels: {
          style: {
            colors: "#64748b",
            fontSize: "10px",
            fontWeight: 700,
          },
        },
      },
      tooltip: {
        shared: true,
        intersect: false,
        custom: ({ dataPointIndex, w }) => {
          const turn = turns[dataPointIndex];
          if (!turn) {
            return "";
          }

          const values = w.config.series
            .map((item: { name?: string; data?: Array<{ y?: number }> }, index: number) => {
              const value = item.data?.[dataPointIndex]?.y;
              if (typeof value !== "number") {
                return "";
              }

              return `<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;font-size:10px;font-weight:700;">
                <span style="color:${w.globals.colors[index]};text-transform:uppercase;opacity:0.9;">${escapeHtml(item.name ?? "")}</span>
                <span style="color:#fff;">${Math.round(value)}</span>
              </div>`;
            })
            .join("");

          return `<div style="background:#0f172a;border:1px solid #334155;box-shadow:0 25px 50px -12px rgba(15,23,42,0.45);border-radius:4px;padding:12px;max-width:280px;pointer-events:none;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid #334155;">
              <span style="font-weight:700;color:#fff;font-size:11px;text-transform:uppercase;letter-spacing:0.08em;">Turn ${turn.order}</span>
              <span style="background:#1e293b;color:#cbd5e1;font-size:10px;padding:2px 8px;border-radius:2px;font-weight:700;border:1px solid #334155;text-transform:uppercase;letter-spacing:0.08em;">${escapeHtml(turn.agentLabel)}</span>
            </div>
            <p style="color:#cbd5e1;font-size:12px;line-height:1.5;font-style:italic;border-left:3px solid #6366f1;padding-left:10px;margin:0 0 12px 0;">"${escapeHtml(turn.text.substring(0, 60))}..."</p>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 16px;">${values}</div>
          </div>`;
        },
      },
      legend: { show: false },
      annotations: {
        xaxis: [
          ...signalAnnotations,
          ...(selectedTurnData
            ? [
                {
                  x: selectedTurnData.order,
                  borderColor: "#6366f1",
                  strokeDashArray: 4,
                  opacity: 0.75,
                },
              ]
            : []),
        ],
      },
      noData: {
        text: "No data",
        align: "center",
        verticalAlign: "middle",
      },
    }),
    [filteredSeriesConfig, onSelectTurn, selectedTurnData, signalAnnotations, turns],
  );

  if (turns.length === 0) {
    return <div className="flex h-full w-full items-center justify-center">No data</div>;
  }

  return (
    <div className="flex h-full w-full flex-col">
      <div className="w-full flex-1 overflow-x-auto overflow-y-hidden rounded-[20px] border border-slate-100 bg-white">
        <div className="min-w-full">
          <Chart
            options={options}
            series={series}
            type="line"
            height={380}
            width={chartWidth}
          />
        </div>
      </div>

      <div className="mt-6 flex flex-col items-center justify-between gap-4 border-t border-slate-100 pt-4 sm:flex-row">
        <div className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2">
          {seriesConfig.map((config) => {
            const isVisible = visibleSeriesKeys.includes(config.key);

            return (
              <button
                key={config.key}
                type="button"
                aria-pressed={isVisible}
                onClick={() => handleLegendClick(config.key)}
                className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 transition ${
                  isVisible
                    ? "border-slate-300 bg-white shadow-sm"
                    : "border-slate-200 bg-slate-50 opacity-55"
                }`}
              >
                {config.dashArray ? (
                  <div className="w-4 border-t-2 border-dashed" style={{ borderColor: config.color }} />
                ) : (
                  <div
                    className={`h-1.5 rounded-sm ${
                      config.key === "tension" || config.key === "positive" || config.key === "dominance"
                        ? "w-4"
                        : config.key === "clarity" || config.key === "neutral" || config.key === "efficiency"
                          ? "w-3.5"
                          : "w-3"
                    }`}
                    style={{ backgroundColor: config.color }}
                  />
                )}
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-600">
                  {config.name.toLowerCase()}
                </span>
              </button>
            );
          })}
        </div>

        <div className="flex flex-wrap items-center justify-center gap-3">
          {isFiltered && (
            <button
              type="button"
              onClick={restoreAllSeries}
              className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-600 transition hover:border-slate-300 hover:bg-slate-50"
            >
              전체 지표 보기
            </button>
          )}

          {view === "signals" && (
            <div className="flex items-center gap-4 rounded-sm border border-slate-200 bg-slate-50 px-3 py-1.5">
              <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-rose-700">
                <AlertTriangle size={12} className="text-rose-500" />
                <span className="flex items-center gap-1">
                  <span className="inline-block h-2 w-2 rounded-sm border border-red-200 bg-red-100" />
                  Tension Spike
                </span>
              </div>
              <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-sky-700">
                <TrendingDown size={12} className="text-sky-500" />
                <span className="flex items-center gap-1">
                  <span className="inline-block h-2 w-2 rounded-sm border border-sky-200 bg-sky-100" />
                  Clarity Drop
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
