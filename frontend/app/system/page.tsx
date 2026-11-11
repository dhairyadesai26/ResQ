"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useWebSocket } from "@/lib/websocket";
import { MetricCard } from "@/components/MetricCard";
import { StatusBadge } from "@/components/StatusBadge";
import { formatBytes, formatUptime } from "@/lib/utils";
import {
  Cpu,
  MemoryStick,
  Activity,
  Layers,
  Terminal,
  Server,
  RefreshCw,
  HardDrive,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

export default function SystemMonitoringPage() {
  const { data: currentMetrics } = useQuery({
    queryKey: ["currentMetrics"],
    queryFn: api.getCurrentMetrics,
    refetchInterval: 2000,
  });

  const { data: history = [] } = useQuery({
    queryKey: ["metricsHistory"],
    queryFn: () => api.getMetricsHistory(25),
    refetchInterval: 3000,
  });

  const { data: apps = [] } = useQuery({
    queryKey: ["applications"],
    queryFn: api.getApplications,
    refetchInterval: 2500,
  });

  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: api.getHealth,
  });

  // Prepare chart series
  const chartData = history.map((h) => ({
    time: new Date(h.timestamp).toLocaleTimeString([], {
      minute: "2-digit",
      second: "2-digit",
    }),
    cpu: h.cpu_percent,
    memory: h.memory_percent,
  }));

  const runningApps = apps.filter((a) => a.status === "RUNNING");

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Metric Cards Header */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="CPU Utilization"
          value={`${currentMetrics?.cpu_percent ?? 0}%`}
          subtitle={`${health?.cpu_count ?? 16} logical processor cores`}
          icon={Cpu}
          badge="Live psutil"
          badgeType="default"
        />

        <MetricCard
          title="Physical Memory Used"
          value={formatBytes(currentMetrics?.memory_used_bytes ?? 0)}
          subtitle={`Total: ${formatBytes(currentMetrics?.memory_total_bytes ?? 0)} (${currentMetrics?.memory_percent ?? 0}%)`}
          icon={MemoryStick}
          badge={`${currentMetrics?.memory_percent ?? 0}%`}
          badgeType="default"
        />

        <MetricCard
          title="Active Managed Processes"
          value={runningApps.length}
          subtitle={`Of ${apps.length} registered applications`}
          icon={Layers}
          badge="Active Handles"
          badgeType={runningApps.length > 0 ? "success" : "default"}
        />

        <MetricCard
          title="Supervisor Host Agent"
          value={health?.agent === "online" ? "Online" : "Connecting"}
          subtitle={`${health?.os || "Windows 11"}`}
          icon={Server}
          badge="Localhost"
          badgeType={health?.agent === "online" ? "success" : "danger"}
        />
      </div>

      {/* Real-time Time Series Area Chart */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-4 gap-2">
          <div>
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-600" />
              Real-Time System Resource Telemetry
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Time-series sampling of host CPU and physical RAM utilization.
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-semibold">
            <span className="flex items-center gap-2 text-blue-700 bg-blue-50 px-3 py-1 rounded-full border border-blue-200">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-600"></span> CPU %
            </span>
            <span className="flex items-center gap-2 text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-600"></span> RAM %
            </span>
          </div>
        </div>

        <div className="h-68 w-full pt-2">
          {chartData.length === 0 ? (
            <div className="h-full flex items-center justify-center text-xs text-slate-400">
              Accumulating resource data points...
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563eb" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#2563eb" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="colorMem" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="time" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#ffffff",
                    borderColor: "#e2e8f0",
                    borderRadius: "12px",
                    boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                    fontSize: "12px",
                    color: "#0f172a",
                    fontWeight: 600,
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="cpu"
                  name="CPU %"
                  stroke="#2563eb"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#colorCpu)"
                />
                <Area
                  type="monotone"
                  dataKey="memory"
                  name="RAM %"
                  stroke="#10b981"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#colorMem)"
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Per-Process Resource Footprint Breakdown Table */}
      <div className="rounded-2xl bg-white border border-slate-200 overflow-hidden shadow-xs">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/60">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Per-Process Resource Footprint Breakdown
          </h2>
          <span className="text-xs text-slate-500 font-mono">
            {runningApps.length} active Windows processes
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 uppercase tracking-wider font-semibold text-[11px] border-b border-slate-200">
              <tr>
                <th className="px-5 py-3">Application</th>
                <th className="px-5 py-3 font-mono">PID</th>
                <th className="px-5 py-3">CPU Usage</th>
                <th className="px-5 py-3">Physical Working Set</th>
                <th className="px-5 py-3">Thread Count</th>
                <th className="px-5 py-3">OS Handles</th>
                <th className="px-5 py-3">Uptime</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700 font-mono">
              {runningApps.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-5 py-8 text-center text-slate-400 font-sans">
                    No active processes currently running. Launch an application to inspect live metrics.
                  </td>
                </tr>
              ) : (
                runningApps.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-50/70">
                    <td className="px-5 py-3 font-sans font-bold text-slate-900">
                      {a.name}
                    </td>
                    <td className="px-5 py-3 text-blue-600 font-bold">{a.current_pid}</td>
                    <td className="px-5 py-3 text-slate-900 font-semibold">{a.cpu_percent}%</td>
                    <td className="px-5 py-3 text-slate-900 font-semibold">{formatBytes(a.memory_rss_bytes)}</td>
                    <td className="px-5 py-3 text-slate-600">{a.num_threads}</td>
                    <td className="px-5 py-3 text-slate-600">{a.num_handles}</td>
                    <td className="px-5 py-3 text-slate-600">{formatUptime(a.uptime_seconds)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
