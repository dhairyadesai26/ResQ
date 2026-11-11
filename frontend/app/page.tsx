"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useWebSocket } from "@/lib/websocket";
import { MetricCard } from "@/components/MetricCard";
import { StatusBadge } from "@/components/StatusBadge";
import { RegisterModal } from "@/components/RegisterModal";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { formatUptime, formatBytes, formatDate } from "@/lib/utils";
import { toast } from "sonner";
import Link from "next/link";
import {
  Activity,
  Play,
  Square,
  RotateCcw,
  Cpu,
  CheckCircle2,
  Clock,
  ArrowRight,
  Plus,
  Terminal,
  Zap,
  ShieldCheck,
  AlertCircle,
  AlertTriangle,
  Info,
} from "lucide-react";

export default function DashboardPage() {
  const queryClient = useQueryClient();
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [confirmStopId, setConfirmStopId] = useState<string | null>(null);

  // Queries
  const { data: apps = [], isLoading: isLoadingApps } = useQuery({
    queryKey: ["applications"],
    queryFn: api.getApplications,
    refetchInterval: 2500,
  });

  const { data: analytics } = useQuery({
    queryKey: ["analytics"],
    queryFn: api.getAnalyticsSummary,
    refetchInterval: 3000,
  });

  const { data: currentMetrics } = useQuery({
    queryKey: ["currentMetrics"],
    queryFn: api.getCurrentMetrics,
    refetchInterval: 2000,
  });

  const { data: events = [] } = useQuery({
    queryKey: ["recentEvents"],
    queryFn: () => api.getEvents({ limit: 6 }),
    refetchInterval: 3000,
  });

  // Real-time WebSocket hook to invalidate queries instantly on events
  useWebSocket((payload) => {
    if (payload.type === "application_updated" || payload.type === "event") {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
      queryClient.invalidateQueries({ queryKey: ["recentEvents"] });
    }
  });

  // Action Mutations
  const startMutation = useMutation({
    mutationFn: (id: string) => api.startProcess(id),
    onSuccess: (data) => {
      toast.success(data.message || "Process launched successfully.");
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
    onError: (err: any) => toast.error(err.message),
  });

  const stopMutation = useMutation({
    mutationFn: (id: string) => api.stopProcess(id),
    onSuccess: (data) => {
      toast.success(data.message || "Process stopped gracefully.");
      setConfirmStopId(null);
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
    onError: (err: any) => toast.error(err.message),
  });

  const restartMutation = useMutation({
    mutationFn: (id: string) => api.restartProcess(id),
    onSuccess: (data) => {
      toast.success(data.message || "Process restarted.");
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
    onError: (err: any) => toast.error(err.message),
  });

  const runningCount = apps.filter((a) => a.status === "RUNNING").length;
  const recoveringCount = apps.filter((a) => a.status === "RECOVERY_WAIT").length;
  const failedCount = apps.filter((a) => a.status === "FAILED").length;
  const stoppedCount = apps.filter((a) => a.status === "STOPPED").length;

  return (
    <div className="space-y-7 max-w-7xl mx-auto">
      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Supervised Applications"
          value={apps.length}
          subtitle={`${runningCount} running · ${stoppedCount} stopped`}
          icon={Activity}
          badge={`${runningCount} Running`}
          badgeType={runningCount > 0 ? "success" : "default"}
        />

        <MetricCard
          title="Recovery Success Rate"
          value={`${analytics?.recovery_success_rate ?? 0}%`}
          subtitle={`${analytics?.successful_recoveries ?? 0} successful of ${analytics?.total_recovery_attempts ?? 0} attempts`}
          icon={CheckCircle2}
          badge={recoveringCount > 0 ? "Recovering" : "Healthy"}
          badgeType={recoveringCount > 0 ? "warning" : "success"}
        />

        <MetricCard
          title="Mean Recovery Latency"
          value={`${((analytics?.average_recovery_latency_seconds ?? 0) * 1000).toFixed(0)} ms`}
          subtitle={`Crash detect latency: ~${((analytics?.average_crash_detection_latency_seconds ?? 0.15) * 1000).toFixed(0)} ms`}
          icon={Clock}
          badge="Win32 Fast"
          badgeType="default"
        />

        <MetricCard
          title="Host CPU Utilization"
          value={`${currentMetrics?.cpu_percent ?? 0}%`}
          subtitle={`RAM: ${formatBytes(currentMetrics?.memory_used_bytes ?? 0)} / ${formatBytes(currentMetrics?.memory_total_bytes ?? 0)}`}
          icon={Cpu}
          badge={`${currentMetrics?.memory_percent ?? 0}% RAM`}
          badgeType={(currentMetrics?.cpu_percent ?? 0) > 85 ? "danger" : "default"}
        />
      </div>

      {/* Main Grid: Applications Table (2/3) & Recent OS Events (1/3) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Applications Table */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                Active Windows Processes
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-semibold font-mono">
                  {runningCount} active
                </span>
              </h2>
              <p className="text-xs text-slate-500">
                Monitored via native Win32 kernel handles with WaitForSingleObject wait hooks.
              </p>
            </div>
            <Link
              href="/applications"
              className="text-xs text-blue-600 hover:text-blue-800 font-semibold flex items-center gap-1 group"
            >
              Manage all <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>

          {apps.length === 0 && !isLoadingApps ? (
            <div className="p-10 rounded-2xl bg-white border border-slate-200 text-center space-y-4 shadow-xs">
              <div className="w-12 h-12 mx-auto rounded-2xl bg-blue-50 text-blue-600 border border-blue-100 flex items-center justify-center">
                <Terminal className="w-6 h-6 stroke-[2.2]" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  No Applications Supervised Yet
                </h3>
                <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 leading-relaxed">
                  Register an application (like the included test worker or fault crasher) to observe real Windows process creation, fault detection, and recovery.
                </p>
              </div>
              <button
                onClick={() => setIsRegisterOpen(true)}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition-all hover:shadow"
              >
                <Plus className="w-4 h-4 stroke-[2.5]" />
                Register First Application
              </button>
            </div>
          ) : (
            <div className="rounded-2xl bg-white border border-slate-200 overflow-hidden shadow-xs">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50/80 text-slate-600 uppercase tracking-wider font-semibold border-b border-slate-200 text-[11px]">
                    <tr>
                      <th className="px-5 py-3.5">Application</th>
                      <th className="px-5 py-3.5">State</th>
                      <th className="px-5 py-3.5 font-mono">PID</th>
                      <th className="px-5 py-3.5">Uptime</th>
                      <th className="px-5 py-3.5">CPU / RAM</th>
                      <th className="px-5 py-3.5 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700 font-normal">
                    {apps.slice(0, 6).map((app) => (
                      <tr key={app.id} className="hover:bg-slate-50/70 transition-colors">
                        <td className="px-5 py-3.5">
                          <Link
                            href={`/applications/${app.id}`}
                            className="font-bold text-slate-900 hover:text-blue-600 transition-colors block text-sm"
                          >
                            {app.name}
                          </Link>
                          <span className="text-[11px] text-slate-400 font-mono truncate block max-w-xs mt-0.5">
                            {app.executable_path}
                          </span>
                        </td>
                        <td className="px-5 py-3.5">
                          <StatusBadge status={app.status} />
                        </td>
                        <td className="px-5 py-3.5 font-mono tabular-nums">
                          {app.current_pid ? (
                            <span className="px-2 py-0.5 rounded-lg bg-blue-50 text-blue-700 border border-blue-200 font-bold">
                              {app.current_pid}
                            </span>
                          ) : (
                            <span className="text-slate-400">—</span>
                          )}
                        </td>
                        <td className="px-5 py-3.5 tabular-nums font-mono text-slate-600 font-medium">
                          {app.status === "RUNNING"
                            ? formatUptime(app.uptime_seconds)
                            : "—"}
                        </td>
                        <td className="px-5 py-3.5 tabular-nums text-slate-600 font-mono">
                          {app.status === "RUNNING" ? (
                            <span>
                              {app.cpu_percent}% · {formatBytes(app.memory_rss_bytes)}
                            </span>
                          ) : (
                            "—"
                          )}
                        </td>
                        <td className="px-5 py-3.5 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            {app.status === "STOPPED" || app.status === "FAILED" ? (
                              <button
                                onClick={() => startMutation.mutate(app.id)}
                                disabled={startMutation.isPending}
                                className="p-2 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 transition-colors shadow-2xs"
                                title="Launch Process"
                              >
                                <Play className="w-3.5 h-3.5 fill-current" />
                              </button>
                            ) : (
                              <button
                                onClick={() => setConfirmStopId(app.id)}
                                className="p-2 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 transition-colors shadow-2xs"
                                title="Graceful Stop"
                              >
                                <Square className="w-3.5 h-3.5 fill-current" />
                              </button>
                            )}

                            <button
                              onClick={() => restartMutation.mutate(app.id)}
                              disabled={restartMutation.isPending}
                              className="p-2 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 transition-colors shadow-2xs"
                              title="Restart"
                            >
                              <RotateCcw className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Live Event Audit Stream */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Clock className="w-4 h-4 text-blue-600" />
                Recent OS Events
              </h2>
              <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                IST (UTC+5:30)
              </span>
            </div>
            <Link
              href="/events"
              className="text-xs text-blue-600 hover:text-blue-800 font-semibold flex items-center gap-1 group"
            >
              All events <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>

          <div className="rounded-2xl bg-white border border-slate-200 p-5 space-y-3 shadow-xs">
            {events.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-400">
                No events recorded yet. Launch an application to start telemetry.
              </div>
            ) : (
              events.map((evt) => {
                const isCrash = evt.event_type.includes("CRASH");
                const isRecovery = evt.event_type.includes("RECOVERY");

                return (
                  <div
                    key={evt.id}
                    className="p-3.5 rounded-xl bg-slate-50/80 border border-slate-200 text-xs space-y-1.5 hover:bg-slate-100/60 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900">
                        {evt.app_name || "Process Supervisor"}
                      </span>
                      <span className="text-[11px] text-slate-600 font-mono font-medium bg-white border border-slate-200/90 px-2 py-0.5 rounded-md shadow-2xs">
                        {formatDate(evt.timestamp)}
                      </span>
                    </div>

                    <p className="text-slate-700 text-xs leading-relaxed font-medium">
                      {evt.message}
                    </p>

                    <div className="flex items-center gap-2 pt-0.5 font-mono text-[11px]">
                      {evt.pid && (
                        <span className="px-1.5 py-0.2 rounded bg-slate-200 text-slate-700">
                          PID: {evt.pid}
                        </span>
                      )}
                      {evt.exit_code !== null && evt.exit_code !== undefined && (
                        <span
                          className={`px-1.5 py-0.2 rounded font-semibold ${
                            evt.exit_code === 0
                              ? "bg-emerald-100 text-emerald-800"
                              : "bg-rose-100 text-rose-800"
                          }`}
                        >
                          Exit: {evt.exit_code}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Confirmation Dialog for Process Stop */}
      <ConfirmDialog
        isOpen={confirmStopId !== null}
        title="Stop Supervised Process?"
        message="This will signal the Windows process to terminate gracefully. Because this is a user-initiated stop, automatic recovery will intentionally NOT be triggered."
        confirmLabel="Stop Process"
        variant="warning"
        onConfirm={() => confirmStopId && stopMutation.mutate(confirmStopId)}
        onCancel={() => setConfirmStopId(null)}
      />

      {/* Modal for App Registration */}
      <RegisterModal
        isOpen={isRegisterOpen}
        onClose={() => setIsRegisterOpen(false)}
      />
    </div>
  );
}
