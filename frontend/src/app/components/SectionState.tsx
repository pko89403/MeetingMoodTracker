import React from "react";

interface SectionStateProps {
  title: string;
  message: string;
}

export function SectionState({ title, message }: SectionStateProps) {
  return (
    <div className="flex h-full min-h-[220px] flex-col items-center justify-center rounded-[24px] border border-slate-200 bg-[linear-gradient(180deg,_rgba(255,255,255,0.98)_0%,_rgba(248,250,252,1)_100%)] p-8 text-center shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]">
      <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-500">
        {title}
      </span>
      <p className="mt-4 max-w-md text-sm leading-6 text-slate-500">{message}</p>
    </div>
  );
}
