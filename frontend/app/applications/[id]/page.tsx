"use client";

import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useWebSocket } from "@/lib/websocket";
import { StatusBadge } from "@/components/StatusBadge";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { formatUptime, formatBytes, formatDate } from "@/lib/utils";
import { toast } from "sonner";
import Link from "next/link";
import {
  ArrowLeft,
  Play,
  Square,
  RotateCcw,
  Trash2,
  Terminal,
  Cpu,
  MemoryStick,
  Clock,
  ShieldCheck,
  AlertTriangle,
  History,
  Layers,
  Settings,
} from "lucide-react";

export default function ApplicationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const appId = params.id as string;

  const [confirmStop, setConfirmStop] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const { data: app, isLoading } = useQuery({
    queryKey: ["application", appId],
    queryFn: () => api.getApplication(appId),
    refetchInterval: 2000,
  });

  const { data: runs = [] } = useQuery({
    queryKey: ["applicationRuns", appId],
    queryFn: () => api.getApplicationRuns(appId),
    refetchInterval: 3000,
  });

  const { data: events = [] } = useQuery({
    queryKey: ["applicationEvents", appId],
    queryFn: () => api.getEvents({ app_id: appId, limit: 15 }),
    refetchInterval: 3000,
  });

  useWebSocket((payload) => {
    if (payload.type === "application_updated" && payload.data?.id === appId) {
      queryClient.invalidateQueries({ queryKey: ["application", appId] });
      queryClient.invalidateQueries({ queryKey: ["applicationRuns", appId] });
      queryClient.invalidateQueries({ queryKey: ["applicationEvents", appId] });
    }
  });

  const startMutation = useMutation({
    mutationFn: () => api.startProcess(appId),
    onSuccess: (data) => {
      toast.success(data.message || "Process started.");
      queryClient.invalidateQueries({ queryKey: ["application", appId] });
    },
    onError: (err: any) => toast.error(err.message),
  });

  const stopMutation = useMutation({
    mutationFn: () => api.stopProcess(appId),
    onSuccess: (data) => {
      toast.success(data.message || "Process stopped.");
      setConfirmStop(false);
      queryClient.invalidateQueries({ queryKey: ["application", appId] });
    },
    onError: (err: any) => toast.error(err.message),
  });

  const restartMutation = useMutation({
    mutationFn: () => api.restartProcess(appId),
    onSuccess: (data) => {
      toast.success(data.message || "Process restarted.");
      queryClient.invalidateQueries({ queryKey: ["application", appId] });
    },
    onError: (err: any) => toast.error(err.message),
  });

  const resetMutation = useMutation({
    mutationFn: () => api.resetRecoveryCounter(appId),
    onSuccess: () => {
      toast.success("Retry counter reset to 0.");
      queryClient.invalidateQueries({ queryKey: ["application", appId] });
    },
    onError: (err: any) => toast.error(err.message),
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.deleteApplication(appId),
    onSuccess: () => {
      toast.success("Application unregister complete.");
      router.push("/applications");
    },
    onError: (err: any) => toast.error(err.message),
  });

  if (isLoading || !app) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-sm font-semibold text-slate-500">Loading process telemetry...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header with Back button and Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <Link
            href="/applications"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-800 transition-colors mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Applications
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-extrabold tracking-tight text-slate-900">
              {app.name}
            </h1>
            <StatusBadge status={app.status} />
          </div>
          <div className="mt-1 text-xs text-slate-500 font-mono">
            {app.executable_path}
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {app.status === "STOPPED" || app.status === "FAILED" ? (
            <button
              onClick={() => startMutation.mutate()}
              disabled={startMutation.isPending}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-xs transition-all"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Launch</span>
            </button>
          ) : (
            <button
              onClick={() => setConfirmStop(true)}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold shadow-xs transition-all"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              <span>Graceful Stop</span>
            </button>
          )}

          <button
            onClick={() => restartMutation.mutate()}
            disabled={restartMutation.isPending}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold border border-slate-200 shadow-2xs transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Restart</span>
          </button>

          {app.consecutive_retries > 0 && (
            <button
              onClick={() => resetMutation.mutate()}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-700 text-xs font-semibold border border-amber-200 transition-colors"
            >
              <span>Reset Retries (0)</span>
            </button>
          )}

          <button
            onClick={() => setConfirmDelete(true)}
            className="p-2 rounded-xl bg-white hover:bg-rose-50 text-slate-400 hover:text-rose-600 border border-slate-200 shadow-2xs transition-colors"
            title="Unregister Application"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Process Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
            Process ID (PID)
          </span>
          <span className="text-xl font-extrabold font-mono text-blue-600 tabular-nums mt-1 block">
            {app.current_pid ?? "—"}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
            Current Uptime
          </span>
          <span className="text-xl font-extrabold font-mono text-slate-900 tabular-nums mt-1 block">
            {app.status === "RUNNING" ? formatUptime(app.uptime_seconds) : "0s"}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
            Process CPU
          </span>
          <span className="text-xl font-extrabold font-mono text-slate-900 tabular-nums mt-1 block">
            {app.cpu_percent}%
          </span>
        </div>

        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
            Working Set (RAM)
          </span>
          <span className="text-xl font-extrabold font-mono text-slate-900 tabular-nums mt-1 block">
            {formatBytes(app.memory_rss_bytes)}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
            Active Threads
          </span>
          <span className="text-xl font-extrabold font-mono text-slate-900 tabular-nums mt-1 block">
            {app.num_threads}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
            Win32 Handles
          </span>
          <span className="text-xl font-extrabold font-mono text-slate-900 tabular-nums mt-1 block">
            {app.num_handles}
          </span>
        </div>
      </div>

      {/* Recovery Policy & Process Spec */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Recovery Policy Settings Card */}
        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <span className="text-xs font-bold text-slate-900 flex items-center gap-2">
              <RotateCcw className="w-4 h-4 text-blue-600" />
              Configured Recovery Policy
            </span>
            <span
              className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${
                app.auto_recovery
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : "bg-slate-100 text-slate-600 border-slate-200"
              }`}
            >
              {app.auto_recovery ? "Automatic Recovery Enabled" : "Disabled"}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4 text-xs">
            <div>
              <span className="text-slate-500 block text-[11px] font-medium">Consecutive Crash Retries</span>
              <span className="font-bold text-slate-900 tabular-nums text-sm mt-0.5 block">
                {app.consecutive_retries} of {app.max_retries} maximum
              </span>
            </div>
            <div>
              <span className="text-slate-500 block text-[11px] font-medium">Lifetime Recoveries</span>
              <span className="font-bold text-slate-900 tabular-nums text-sm mt-0.5 block">
                {app.total_recoveries} automatic relaunches
              </span>
            </div>
            <div>
              <span className="text-slate-500 block text-[11px] font-medium">Exponential Backoff</span>
              <span className="font-bold text-slate-900 tabular-nums text-sm mt-0.5 block">
                {app.retry_delay_seconds}s × {app.backoff_multiplier}
                <span className="text-[10px] text-slate-400 font-normal"> (cap {app.max_delay_seconds}s)</span>
              </span>
            </div>
            <div>
              <span className="text-slate-500 block text-[11px] font-medium">Last Process Exit</span>
              <span className="font-bold text-slate-900 tabular-nums text-sm mt-0.5 block">
                {app.last_exit_code !== null ? `Exit Code ${app.last_exit_code}` : "None recorded"}
              </span>
            </div>
          </div>
        </div>

        {/* Process Launch Specifications */}
        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-4">
          <div className="border-b border-slate-100 pb-3">
            <span className="text-xs font-bold text-slate-900 flex items-center gap-2">
              <Terminal className="w-4 h-4 text-blue-600" />
              Execution Parameters
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <span className="text-slate-500 block text-[11px] font-medium">Command Arguments:</span>
              <span className="font-mono text-slate-800 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg block truncate mt-1">
                {app.arguments || "(None specified)"}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block text-[11px] font-medium">Working Directory:</span>
              <span className="font-mono text-slate-800 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg block truncate mt-1">
                {app.working_dir || "(Executable parent directory)"}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block text-[11px] font-medium">Registered At:</span>
              <span className="text-slate-700 font-medium">{formatDate(app.created_at)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Historical Execution Runs Table */}
      <div className="rounded-2xl bg-white border border-slate-200 overflow-hidden shadow-xs">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/60">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
            <History className="w-4 h-4 text-blue-600" />
            Process Run History (PIDs & Exit Codes)
          </h2>
          <span className="text-xs text-slate-500 font-mono">
            {runs.length} recorded runs
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 uppercase tracking-wider font-semibold text-[11px] border-b border-slate-200">
              <tr>
                <th className="px-5 py-3">PID</th>
                <th className="px-5 py-3">Start Time</th>
                <th className="px-5 py-3">End Time</th>
                <th className="px-5 py-3">Duration</th>
                <th className="px-5 py-3">Exit Code</th>
                <th className="px-5 py-3">Termination Type</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700 font-normal">
              {runs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-8 text-center text-slate-400">
                    No execution runs recorded yet. Launch the process to record runtime sessions.
                  </td>
                </tr>
              ) : (
                runs.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/70 font-mono">
                    <td className="px-5 py-3 font-bold text-blue-600">{r.pid}</td>
                    <td className="px-5 py-3 text-slate-600">{formatDate(r.start_time)}</td>
                    <td className="px-5 py-3 text-slate-600">
                      {r.end_time ? (
                        formatDate(r.end_time)
                      ) : (
                        <span className="text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                          Active
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-slate-800">
                      {r.duration_seconds ? formatUptime(r.duration_seconds) : "Running"}
                    </td>
                    <td className="px-5 py-3">
                      {r.exit_code !== null ? (
                        <span
                          className={`px-2 py-0.5 rounded font-bold ${
                            r.exit_code === 0
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : "bg-rose-50 text-rose-700 border border-rose-200"
                          }`}
                        >
                          {r.exit_code}
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="px-5 py-3 font-sans">
                      <span
                        className={`text-[11px] px-2.5 py-0.5 rounded-full font-bold border ${
                          r.termination_type === "ACTIVE"
                            ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                            : r.termination_type === "EXPECTED"
                            ? "bg-slate-100 text-slate-700 border-slate-200"
                            : "bg-rose-50 text-rose-700 border-rose-200"
                        }`}
                      >
                        {r.termination_type}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Confirmation Dialogs */}
      <ConfirmDialog
        isOpen={confirmStop}
        title="Stop Process?"
        message="Graceful stop requests intentionally do not trigger automatic recovery."
        confirmLabel="Stop Process"
        variant="warning"
        onConfirm={() => stopMutation.mutate()}
        onCancel={() => setConfirmStop(false)}
      />

      <ConfirmDialog
        isOpen={confirmDelete}
        title="Unregister Application?"
        message="This will terminate any running instance and remove the application registration from ResQ Web."
        confirmLabel="Unregister"
        variant="danger"
        onConfirm={() => deleteMutation.mutate()}
        onCancel={() => setConfirmDelete(false)}
      />
    </div>
  );
}
