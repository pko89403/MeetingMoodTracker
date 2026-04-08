import React from "react";
import { cn } from "./ui/utils";

export type DashboardView = "flow" | "timeline";

export function DashboardViewTabs({
  view,
  onChangeView,
}: {
  view: DashboardView;
  onChangeView: (view: DashboardView) => void;
}) {
  return (
    <div
      className="inline-flex rounded-full border border-white/10 bg-white/6 p-1"
      data-testid="dashboard-view-tabs"
    >
      {[
        { key: "flow", label: "Flow 보드" },
        { key: "timeline", label: "Timeline" },
      ].map((item) => (
        <button
          key={item.key}
          type="button"
          data-testid={`${item.key}-view-tab`}
          aria-pressed={view === item.key}
          onClick={() => onChangeView(item.key as DashboardView)}
          className={cn(
            "rounded-full px-4 py-2 text-xs font-semibold transition",
            view === item.key
              ? "bg-white text-slate-950 shadow-sm"
              : "text-slate-300 hover:text-white",
          )}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
