"use client";

import React from "react";
import { ProcessState } from "@/types";
import { cn } from "@/lib/utils";
import { Loader2, RotateCcw, AlertTriangle, Square, Play } from "lucide-react";

interface StatusBadgeProps {
  status: ProcessState | string;
  className?: string;
  showIcon?: boolean;
}

export function StatusBadge({ status, className, showIcon = true }: StatusBadgeProps) {
  switch (status) {
    case "RUNNING":
      return (
        <span
          className={cn(
            "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-2xs",
            className
          )}
        >
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          RUNNING
        </span>
      );

    case "STARTING":
      return (
        <span
          className={cn(
            "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200 shadow-2xs",
            className
          )}
        >
          <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-600" />
          STARTING
        </span>
      );

    case "STOPPED":
      return (
        <span
          className={cn(
            "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200 shadow-2xs",
            className
          )}
        >
          <span className="h-1.5 w-1.5 rounded-full bg-slate-400" />
          STOPPED
        </span>
      );

    case "STOPPING":
      return (
        <span
          className={cn(
            "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200 shadow-2xs",
            className
          )}
        >
          <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-600" />
          STOPPING
        </span>
      );

    case "RECOVERY_WAIT":
      return (
        <span
          className={cn(
            "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-orange-50 text-orange-700 border border-orange-200 shadow-2xs",
            className
          )}
        >
          <RotateCcw className="w-3.5 h-3.5 animate-spin text-orange-600" />
          RECOVERING
        </span>
      );

    case "FAILED":
      return (
        <span
          className={cn(
            "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200 shadow-2xs",
            className
          )}
        >
          <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
          FAILED
        </span>
      );

    default:
      return (
        <span
          className={cn(
            "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200",
            className
          )}
        >
          {status}
        </span>
      );
  }
}
