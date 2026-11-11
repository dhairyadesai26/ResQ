"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  badge?: string;
  badgeType?: "default" | "success" | "warning" | "danger";
  className?: string;
}

export function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  badge,
  badgeType = "default",
  className,
}: MetricCardProps) {
  const badgeClasses = {
    default: "bg-slate-100 text-slate-600 border-slate-200",
    success: "bg-emerald-50 text-emerald-700 border-emerald-200",
    warning: "bg-amber-50 text-amber-700 border-amber-200",
    danger: "bg-rose-50 text-rose-700 border-rose-200",
  }[badgeType];

  return (
    <div
      className={cn(
        "relative p-5 rounded-2xl bg-white border border-slate-200 shadow-xs hover:shadow-sm hover:border-slate-300 transition-all",
        className
      )}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-bold text-slate-500 tracking-wider uppercase">
          {title}
        </span>
        <div className="p-2.5 rounded-xl bg-blue-50 text-blue-600 border border-blue-100">
          <Icon className="w-4 h-4 stroke-[2.2]" />
        </div>
      </div>

      <div className="flex items-baseline gap-2.5">
        <div className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 tabular-nums">
          {value}
        </div>
        {badge && (
          <span
            className={cn(
              "px-2 py-0.5 text-[11px] font-semibold rounded-full border shadow-2xs",
              badgeClasses
            )}
          >
            {badge}
          </span>
        )}
      </div>

      {subtitle && (
        <div className="mt-1.5 text-xs text-slate-500 font-medium">
          {subtitle}
        </div>
      )}
    </div>
  );
}
