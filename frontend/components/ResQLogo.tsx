"use client";

import React from "react";
import { LifeBuoy, HeartPulse } from "lucide-react";

interface ResQLogoProps {
  size?: "sm" | "md" | "lg";
  showText?: boolean;
}

export function ResQLogo({ size = "md", showText = true }: ResQLogoProps) {
  const iconSizes = {
    sm: "w-4 h-4",
    md: "w-5 h-5",
    lg: "w-6 h-6",
  }[size];

  const badgeSizes = {
    sm: "w-8 h-8 rounded-lg",
    md: "w-10 h-10 rounded-xl",
    lg: "w-12 h-12 rounded-2xl",
  }[size];

  return (
    <div className="flex items-center gap-3">
      {/* ResQ Distinctive Brand Emblem: Dual-Ring Rescue Lifebuoy + Kernel Heartbeat */}
      <div
        className={`relative ${badgeSizes} bg-gradient-to-br from-blue-600 via-indigo-600 to-sky-500 flex items-center justify-center text-white shadow-md shadow-blue-500/20 shrink-0 ring-2 ring-blue-100`}
      >
        <LifeBuoy className={`${iconSizes} animate-[spin_12s_linear_infinite] opacity-90`} />
        <HeartPulse className="w-3 h-3 text-amber-300 absolute" />
      </div>

      {showText && (
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            <span className="font-bold tracking-tight text-slate-900 text-base">
              ResQ<span className="text-blue-600 font-extrabold">.Web</span>
            </span>
            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
              v1.0
            </span>
          </div>
          <span className="text-[11px] font-medium text-slate-500 -mt-0.5">
            Process Supervisor
          </span>
        </div>
      )}
    </div>
  );
}

