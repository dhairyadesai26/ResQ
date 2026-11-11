"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Layers,
  RotateCcw,
  History,
  Cpu,
  BarChart3,
  FileCode2,
  SlidersHorizontal,
  Server,
  Users,
} from "lucide-react";
import { useWebSocket } from "@/lib/websocket";
import { ResQLogo } from "@/components/ResQLogo";

const navItems = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Applications", href: "/applications", icon: Layers },
  { name: "Recovery Policies", href: "/recovery", icon: RotateCcw },
  { name: "Event History", href: "/events", icon: History },
  { name: "System Monitoring", href: "/system", icon: Cpu },
  { name: "Analytics & MTTR", href: "/analytics", icon: BarChart3 },
  { name: "Diagnostics & Logs", href: "/logs", icon: FileCode2 },
  { name: "Settings & About", href: "/settings", icon: SlidersHorizontal },
];

export function Sidebar() {
  const pathname = usePathname();
  const { isConnected } = useWebSocket();

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col h-screen select-none shrink-0 sticky top-0 shadow-sm z-30">
      {/* Brand Header */}
      <div className="h-20 px-5 flex items-center border-b border-slate-100">
        <Link href="/" className="hover:opacity-95 transition-opacity">
          <ResQLogo size="md" />
        </Link>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-5 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
          Process Control
        </div>
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all group",
                isActive
                  ? "bg-blue-50 text-blue-700 font-semibold shadow-xs"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              )}
            >
              <Icon
                className={cn(
                  "w-4 h-4 transition-colors",
                  isActive
                    ? "text-blue-600"
                    : "text-slate-400 group-hover:text-slate-600"
                )}
              />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Agent Status & Academic Badge Footer */}
      <div className="p-4 border-t border-slate-100 bg-slate-50/50 space-y-3">
        {/* Supervisor Connection Card */}
        <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
              <Server className="w-3.5 h-3.5 text-blue-600" />
              Windows Agent
            </span>
            <span
              className={cn(
                "w-2 h-2 rounded-full",
                isConnected ? "bg-emerald-500 animate-pulse" : "bg-rose-500"
              )}
            />
          </div>
          <div className="text-[11px] text-slate-500 flex items-center justify-between">
            <span>Kernel Hook:</span>
            <span
              className={cn(
                "font-medium",
                isConnected ? "text-emerald-700 font-semibold" : "text-rose-600"
              )}
            >
              {isConnected ? "Active (Live Sync)" : "Connecting..."}
            </span>
          </div>
        </div>

        {/* Academic Group Info */}
        <div className="px-2 text-[10px] text-slate-500 leading-relaxed">
          <div className="font-semibold text-slate-700 flex items-center gap-1">
            <Users className="w-3 h-3 text-slate-400" /> B.Tech CSE Group 5
          </div>
          <div>Dhairya, Neet, Mrugen, Keval, Svetal</div>
        </div>
      </div>
    </aside>
  );
}
