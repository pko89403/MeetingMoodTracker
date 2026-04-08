import React from "react";
import { cn } from "./ui/utils";

type BrandMarkSize = "sm" | "md" | "lg";
type BrandMarkTone = "light" | "dark";

const SIZE_STYLES: Record<
  BrandMarkSize,
  {
    icon: string;
    title: string;
    subtitle: string;
    gap: string;
  }
> = {
  sm: {
    icon: "h-10 w-10 rounded-2xl",
    title: "text-sm font-semibold tracking-[-0.02em]",
    subtitle: "text-[11px] leading-5",
    gap: "gap-3",
  },
  md: {
    icon: "h-12 w-12 rounded-[20px]",
    title: "text-base font-semibold tracking-[-0.03em]",
    subtitle: "text-xs leading-5",
    gap: "gap-3.5",
  },
  lg: {
    icon: "h-14 w-14 rounded-[22px]",
    title: "text-lg font-semibold tracking-[-0.04em]",
    subtitle: "text-sm leading-6",
    gap: "gap-4",
  },
};

interface BrandMarkProps {
  className?: string;
  showText?: boolean;
  size?: BrandMarkSize;
  subtitle?: string;
  tone?: BrandMarkTone;
  testId?: string;
}

export function BrandMark({
  className,
  showText = true,
  size = "md",
  subtitle,
  tone = "light",
  testId,
}: BrandMarkProps) {
  const styles = SIZE_STYLES[size];
  const titleClassName = tone === "light" ? "text-white" : "text-slate-950";
  const subtitleClassName = tone === "light" ? "text-slate-400" : "text-slate-500";

  return (
    <div
      data-testid={testId}
      aria-label="Meeting Mood Tracker"
      className={cn("flex items-center", styles.gap, className)}
    >
      <img
        src="/brand/meeting-mood-tracker-logo.svg"
        alt={showText ? "" : "Meeting Mood Tracker 로고"}
        aria-hidden={showText}
        className={cn("shrink-0 shadow-[0_18px_48px_-24px_rgba(17,24,39,0.7)]", styles.icon)}
      />
      {showText && (
        <div className="min-w-0">
          <p className={cn(styles.title, titleClassName)}>Meeting Mood Tracker</p>
          {subtitle && <p className={cn("mt-0.5", styles.subtitle, subtitleClassName)}>{subtitle}</p>}
        </div>
      )}
    </div>
  );
}
