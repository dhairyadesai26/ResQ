"use client";

import React, { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import { Plus, Radio, Clock, ShieldCheck, ChevronRight } from "lucide-react";
import { useWebSocket } from "@/lib/websocket";
import { RegisterModal } from "@/components/RegisterModal";

const titleMap: Record<string, { title: string; category: string }> = {
  "/": { title: "System Overview & Telemetry", category: "Dashboard" },
  "/applications": { title: "Supervised Applications", category: "Process Management" },
  "/recovery": { title: "Automatic Recovery Policies", category: "Fault Tolerance" },
  "/events": { title: "Event History & Audit Trail", category: "Telemetry Logs" },
  "/system": { title: "System Resource Monitoring", category: "Hardware Performance" },
  "/analytics": { title: "Reliability & Recovery Analytics", category: "Empirical Metrics" },
  "/logs": { title: "Supervisor Diagnostic Logs", category: "Runtime Output" },
  "/settings": { title: "Settings & System Architecture", category: "Platform" },
};

export function Navbar() {
  const pathname = usePathname();
  const { isConnected } = useWebSocket();
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [lastSync, setLastSync] = useState<string>("Live");

  useEffect(() => {
    const timer = setInterval(() => {
      setLastSync(
        new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        })
      );
    }, 4000);
    return () => clearInterval(timer);
  }, []);

  const meta = titleMap[pathname] || {
    title: "Process Supervision",
    category: "Application",
  };

  return (
    <>
      <header className="h-20 px-6 sm:px-8 border-b border-slate-200 bg-white/90 backdrop-blur-md sticky top-0 z-20 flex items-center justify-between">
        {/* Title & Breadcrumbs */}
        <div>
          <div className="flex items-center gap-1.5 text-xs font-semibold text-blue-600 uppercase tracking-wider">
            <span>ResQ Web</span>
            <ChevronRight className="w-3 h-3 text-slate-400" />
            <span className="text-slate-500 font-medium">{meta.category}</span>
          </div>
          <h1 className="text-lg sm:text-xl font-bold tracking-tight text-slate-900 mt-0.5">
            {meta.title}
          </h1>
        </div>

        {/* Live Status Pill & Primary Action */}
        <div className="flex items-center gap-3">
          {/* Real-time Connection Indicator */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-50 border border-slate-200 text-xs font-medium text-slate-700 shadow-xs">
            <span
              className={`w-2 h-2 rounded-full ${
                isConnected ? "bg-emerald-500 animate-pulse" : "bg-rose-500"
              }`}
            />
            <span className="text-slate-600">
              {isConnected ? "Live OS Sync" : "Disconnected"}
            </span>
            <span className="text-slate-400 text-[11px] border-l border-slate-200 pl-2 font-mono">
              {lastSync}
            </span>
          </div>

          {/* Quick Register Button */}
          <button
            onClick={() => setIsRegisterOpen(true)}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-xs font-semibold shadow-sm transition-all hover:shadow"
          >
            <Plus className="w-4 h-4 stroke-[2.5]" />
            <span>Register Application</span>
          </button>
        </div>
      </header>

      {/* Registration Modal Dialog */}
      <RegisterModal
        isOpen={isRegisterOpen}
        onClose={() => setIsRegisterOpen(false)}
      />
    </>
  );
}
