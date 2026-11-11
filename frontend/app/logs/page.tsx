"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import {
  FileText,
  Search,
  Filter,
  Download,
  Copy,
  Terminal,
  RefreshCw,
  AlertTriangle,
  Info,
  AlertCircle,
  Clock,
  Layers,
} from "lucide-react";
import { toast } from "sonner";

export default function LogsPage() {
  const [search, setSearch] = useState("");
  const [level, setLevel] = useState("ALL");

  const { data: events = [], isLoading, refetch } = useQuery({
    queryKey: ["diagnosticLogs", level],
    queryFn: () =>
      api.getEvents({
        severity: level !== "ALL" ? level : undefined,
        limit: 150,
      }),
    refetchInterval: 3000,
  });

  const filteredLogs = events.filter((e) => {
    if (!search.trim()) return true;
    const term = search.toLowerCase();
    return (
      e.message.toLowerCase().includes(term) ||
      (e.app_name && e.app_name.toLowerCase().includes(term)) ||
      (e.pid && e.pid.toString().includes(term))
    );
  });

  const copyLogLine = (logText: string) => {
    navigator.clipboard.writeText(logText);
    toast.success("Log entry copied to clipboard.");
  };

  const exportLogs = () => {
    const jsonStr = JSON.stringify(filteredLogs, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `resq_supervisor_logs_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Diagnostic logs exported successfully.");
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2.5">
            <Terminal className="w-5 h-5 text-blue-600" />
            Diagnostic & Supervisor Logs
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Real-time stdout, stderr, process lifecycle transitions, and Win32 wait handle notifications.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={exportLogs}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 shadow-xs transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            Export JSON
          </button>
          <button
            onClick={() => refetch()}
            className="p-2 rounded-lg bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 shadow-xs transition-colors"
            title="Refresh logs"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin text-blue-600" : "text-slate-500"}`} />
          </button>
        </div>
      </div>

      {/* Controls Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex flex-1 items-center gap-3">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search logs by message, process name, or PID..."
              className="w-full pl-9 pr-4 py-2 bg-white border border-slate-200 rounded-lg text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors shadow-xs"
            />
          </div>

          <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-700 shadow-xs">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={level}
              onChange={(e) => setLevel(e.target.value)}
              className="bg-transparent text-xs text-slate-800 font-medium focus:outline-none cursor-pointer"
            >
              <option value="ALL">All Severity Levels</option>
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>Polling frequency: <strong className="text-slate-700 font-mono">3s</strong></span>
        </div>
      </div>

      {/* Structured Log Console */}
      <div className="rounded-xl bg-white border border-slate-200 shadow-xs overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-200 flex items-center justify-between bg-slate-50/70">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-blue-600" />
            <span className="font-semibold text-slate-900 text-xs">
              Live Supervisor Stream
            </span>
          </div>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-slate-200/60 text-slate-700 font-medium">
            {filteredLogs.length} entries
          </span>
        </div>

        <div className="divide-y divide-slate-100 max-h-[600px] overflow-y-auto font-mono text-xs">
          {filteredLogs.length === 0 ? (
            <div className="p-12 text-center text-slate-400 font-sans text-xs flex flex-col items-center justify-center gap-2">
              <FileText className="w-8 h-8 text-slate-300" />
              <span>No diagnostic logs match the current search or filter criteria.</span>
            </div>
          ) : (
            filteredLogs.map((log) => {
              const severityBadge = {
                INFO: "bg-blue-50 text-blue-700 border-blue-200",
                WARNING: "bg-amber-50 text-amber-800 border-amber-200",
                ERROR: "bg-rose-50 text-rose-700 border-rose-200",
                CRITICAL: "bg-red-100 text-red-800 border-red-300 font-bold",
              }[log.severity] || "bg-slate-100 text-slate-700 border-slate-200";

              return (
                <div
                  key={log.id}
                  className="px-4 py-2.5 hover:bg-slate-50/80 flex items-start justify-between gap-4 group transition-colors"
                >
                  <div className="flex items-start gap-3 min-w-0">
                    <span className="text-slate-400 shrink-0 select-none text-[11px] mt-0.5">
                      {formatDate(log.timestamp)}
                    </span>
                    <span
                      className={`shrink-0 px-2 py-0.5 text-[10px] rounded font-semibold border ${severityBadge}`}
                    >
                      {log.severity}
                    </span>
                    <div className="text-slate-800 break-words leading-relaxed">
                      {log.app_name && (
                        <span className="font-bold text-slate-900 mr-1.5 font-sans">
                          [{log.app_name}]
                        </span>
                      )}
                      <span className="font-mono text-slate-700">
                        {log.message}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2.5 shrink-0 text-[11px]">
                    {log.pid && (
                      <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-mono">
                        PID: {log.pid}
                      </span>
                    )}
                    {log.exit_code !== null && log.exit_code !== undefined && (
                      <span className={`px-1.5 py-0.5 rounded font-mono ${
                        log.exit_code === 0 ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"
                      }`}>
                        exit={log.exit_code}
                      </span>
                    )}
                    <button
                      onClick={() =>
                        copyLogLine(
                          `[${formatDate(log.timestamp)}] [${log.severity}] ${log.app_name || "System"}: ${log.message}`
                        )
                      }
                      className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-slate-200 text-slate-400 hover:text-slate-700 transition-all"
                      title="Copy entry"
                    >
                      <Copy className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
