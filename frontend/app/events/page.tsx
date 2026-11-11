"use client";

import React, { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useWebSocket } from "@/lib/websocket";
import { formatDate } from "@/lib/utils";
import {
  History,
  Search,
  Filter,
  Download,
  AlertCircle,
  AlertTriangle,
  Info,
  CheckCircle2,
  RefreshCw,
} from "lucide-react";

export default function EventHistoryPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");
  const [selectedAppId, setSelectedAppId] = useState<string>("ALL");

  const { data: apps = [] } = useQuery({
    queryKey: ["applications"],
    queryFn: api.getApplications,
  });

  const { data: events = [], isLoading, refetch } = useQuery({
    queryKey: ["events", selectedAppId, severityFilter],
    queryFn: () =>
      api.getEvents({
        app_id: selectedAppId !== "ALL" ? selectedAppId : undefined,
        severity: severityFilter !== "ALL" ? severityFilter : undefined,
        limit: 100,
      }),
    refetchInterval: 3000,
  });

  useWebSocket((payload) => {
    if (payload.type === "event") {
      queryClient.invalidateQueries({ queryKey: ["events"] });
    }
  });

  const filteredEvents = events.filter((e) => {
    if (!search.trim()) return true;
    const term = search.toLowerCase();
    return (
      e.message.toLowerCase().includes(term) ||
      (e.app_name && e.app_name.toLowerCase().includes(term)) ||
      e.event_type.toLowerCase().includes(term)
    );
  });

  const handleExportJSON = () => {
    const dataStr =
      "data:text/json;charset=utf-8," +
      encodeURIComponent(JSON.stringify(events, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `resq-events-${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex flex-1 flex-wrap items-center gap-3">
          {/* Search */}
          <div className="relative flex-1 min-w-[220px] max-w-sm">
            <Search className="absolute left-3.5 top-3 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter events by message or type..."
              className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 shadow-2xs font-medium"
            />
          </div>

          {/* Severity Filter */}
          <div className="flex items-center gap-2 bg-white border border-slate-300 rounded-xl px-3 py-2 text-xs text-slate-700 shadow-2xs">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-transparent text-xs text-slate-800 font-semibold focus:outline-none cursor-pointer"
            >
              <option value="ALL">All Severities</option>
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          </div>

          {/* Application Filter */}
          <div className="flex items-center gap-2 bg-white border border-slate-300 rounded-xl px-3 py-2 text-xs text-slate-700 shadow-2xs">
            <select
              value={selectedAppId}
              onChange={(e) => setSelectedAppId(e.target.value)}
              className="bg-transparent text-xs text-slate-800 font-semibold focus:outline-none cursor-pointer"
            >
              <option value="ALL">All Applications ({apps.length})</option>
              {apps.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => refetch()}
            className="p-2.5 rounded-xl bg-white hover:bg-slate-50 text-slate-600 border border-slate-200 shadow-2xs transition-colors"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={handleExportJSON}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold border border-slate-200 shadow-2xs transition-colors"
          >
            <Download className="w-4 h-4 text-blue-600" />
            <span>Export JSON</span>
          </button>
        </div>
      </div>

      {/* Events Table */}
      <div className="rounded-2xl bg-white border border-slate-200 overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/80 text-slate-600 uppercase tracking-wider font-semibold border-b border-slate-200 text-[11px]">
              <tr>
                <th className="px-5 py-3.5">Severity</th>
                <th className="px-5 py-3.5">Event Type</th>
                <th className="px-5 py-3.5">Application</th>
                <th className="px-5 py-3.5">Description</th>
                <th className="px-5 py-3.5 font-mono">PID</th>
                <th className="px-5 py-3.5 font-mono">Exit Code</th>
                <th className="px-5 py-3.5 text-right">Timestamp (IST)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700 font-normal">
              {filteredEvents.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-5 py-10 text-center text-slate-400">
                    No matching supervisor events found.
                  </td>
                </tr>
              ) : (
                filteredEvents.map((evt) => {
                  const severityBadge = {
                    INFO: "bg-blue-50 text-blue-700 border-blue-200",
                    WARNING: "bg-amber-50 text-amber-700 border-amber-200",
                    ERROR: "bg-rose-50 text-rose-700 border-rose-200",
                    CRITICAL: "bg-rose-100 text-rose-800 border-rose-300 font-bold",
                  }[evt.severity] || "bg-slate-100 text-slate-700 border-slate-200";

                  const severityIcon = {
                    INFO: <Info className="w-3.5 h-3.5 text-blue-600" />,
                    WARNING: <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />,
                    ERROR: <AlertCircle className="w-3.5 h-3.5 text-rose-600" />,
                    CRITICAL: <AlertCircle className="w-3.5 h-3.5 text-rose-700" />,
                  }[evt.severity] || <Info className="w-3.5 h-3.5 text-slate-500" />;

                  return (
                    <tr key={evt.id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="px-5 py-3.5">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold border shadow-2xs ${severityBadge}`}
                        >
                          {severityIcon}
                          {evt.severity}
                        </span>
                      </td>

                      <td className="px-5 py-3.5 font-mono text-[11px] font-semibold text-slate-800">
                        {evt.event_type}
                      </td>

                      <td className="px-5 py-3.5 font-bold text-slate-900">
                        {evt.app_name || "System"}
                      </td>

                      <td className="px-5 py-3.5 text-slate-700 max-w-md font-medium leading-relaxed">
                        {evt.message}
                      </td>

                      <td className="px-5 py-3.5 font-mono tabular-nums text-slate-600">
                        {evt.pid ? (
                          <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-800 font-bold">
                            {evt.pid}
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>

                      <td className="px-5 py-3.5 font-mono tabular-nums">
                        {evt.exit_code !== null && evt.exit_code !== undefined ? (
                          <span
                            className={`px-2 py-0.5 rounded-full text-[11px] font-bold border ${
                              evt.exit_code === 0
                                ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                : "bg-rose-50 text-rose-700 border-rose-200"
                            }`}
                          >
                            code {evt.exit_code}
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>

                      <td className="px-5 py-3.5 text-right font-mono text-[11px] text-slate-500">
                        {formatDate(evt.timestamp)}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
