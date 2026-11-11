"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useWebSocket } from "@/lib/websocket";
import { StatusBadge } from "@/components/StatusBadge";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { RegisterModal } from "@/components/RegisterModal";
import { formatUptime, formatBytes } from "@/lib/utils";
import { toast } from "sonner";
import Link from "next/link";
import {
  Plus,
  Search,
  Play,
  Square,
  RotateCcw,
  Trash2,
  ExternalLink,
  Filter,
  RefreshCw,
  Terminal,
} from "lucide-react";

export default function ApplicationsPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [confirmStopId, setConfirmStopId] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const { data: apps = [], isLoading, refetch } = useQuery({
    queryKey: ["applications"],
    queryFn: api.getApplications,
    refetchInterval: 2500,
  });

  useWebSocket((payload) => {
    if (payload.type === "application_updated" || payload.type === "application_deleted") {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    }
  });

  // Mutations
  const startMutation = useMutation({
    mutationFn: (id: string) => api.startProcess(id),
    onSuccess: (data) => {
      toast.success(data.message || "Process started.");
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
    onError: (err: any) => toast.error(err.message),
  });

  const stopMutation = useMutation({
    mutationFn: (id: string) => api.stopProcess(id),
    onSuccess: (data) => {
      toast.success(data.message || "Process stopped.");
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

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteApplication(id),
    onSuccess: () => {
      toast.success("Application registration removed.");
      setConfirmDeleteId(null);
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
    onError: (err: any) => toast.error(err.message),
  });

  const resetCounterMutation = useMutation({
    mutationFn: (id: string) => api.resetRecoveryCounter(id),
    onSuccess: () => {
      toast.success("Consecutive retry counter reset to 0.");
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
    onError: (err: any) => toast.error(err.message),
  });

  // Filtering
  const filteredApps = apps.filter((app) => {
    const matchesSearch =
      app.name.toLowerCase().includes(search.toLowerCase()) ||
      app.executable_path.toLowerCase().includes(search.toLowerCase());
    const matchesStatus =
      statusFilter === "ALL" || app.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex flex-1 items-center gap-3">
          {/* Search Bar */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3.5 top-3 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by application name or executable path..."
              className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 shadow-2xs font-medium"
            />
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-2 bg-white border border-slate-300 rounded-xl px-3 py-2 text-xs text-slate-700 shadow-2xs">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-transparent text-xs text-slate-800 font-semibold focus:outline-none cursor-pointer"
            >
              <option value="ALL">All States ({apps.length})</option>
              <option value="RUNNING">RUNNING</option>
              <option value="STOPPED">STOPPED</option>
              <option value="RECOVERY_WAIT">RECOVERY_WAIT</option>
              <option value="FAILED">FAILED</option>
            </select>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => refetch()}
            className="p-2.5 rounded-xl bg-white hover:bg-slate-50 text-slate-600 border border-slate-200 shadow-2xs transition-colors"
            title="Refresh Application Table"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={() => setIsRegisterOpen(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition-all hover:shadow"
          >
            <Plus className="w-4 h-4 stroke-[2.5]" />
            <span>Register Application</span>
          </button>
        </div>
      </div>

      {/* Applications Table */}
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
                <th className="px-5 py-3.5">Fault Retries</th>
                <th className="px-5 py-3.5">Last Exit</th>
                <th className="px-5 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700 font-normal">
              {filteredApps.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-5 py-10 text-center text-slate-500 text-xs">
                    {apps.length === 0
                      ? "No applications registered yet. Click 'Register Application' above."
                      : "No applications match the search or filter criteria."}
                  </td>
                </tr>
              ) : (
                filteredApps.map((app) => (
                  <tr key={app.id} className="hover:bg-slate-50/70 transition-colors">
                    {/* App info */}
                    <td className="px-5 py-3.5">
                      <Link
                        href={`/applications/${app.id}`}
                        className="font-bold text-slate-900 hover:text-blue-600 transition-colors flex items-center gap-1.5 text-sm"
                      >
                        {app.name}
                        <ExternalLink className="w-3 h-3 text-slate-400" />
                      </Link>
                      <span className="text-[11px] text-slate-400 font-mono truncate block max-w-sm mt-0.5">
                        {app.executable_path}
                      </span>
                    </td>

                    {/* State Badge */}
                    <td className="px-5 py-3.5">
                      <StatusBadge status={app.status} />
                    </td>

                    {/* PID */}
                    <td className="px-5 py-3.5 font-mono tabular-nums">
                      {app.current_pid ? (
                        <span className="px-2 py-0.5 rounded-lg bg-blue-50 text-blue-700 border border-blue-200 font-bold">
                          {app.current_pid}
                        </span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>

                    {/* Uptime */}
                    <td className="px-5 py-3.5 tabular-nums font-mono text-slate-600 font-medium">
                      {app.status === "RUNNING"
                        ? formatUptime(app.uptime_seconds)
                        : "—"}
                    </td>

                    {/* Resources */}
                    <td className="px-5 py-3.5 tabular-nums text-slate-600 font-mono">
                      {app.status === "RUNNING" ? (
                        <span>
                          {app.cpu_percent}% · {formatBytes(app.memory_rss_bytes)}
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>

                    {/* Retries */}
                    <td className="px-5 py-3.5 font-mono tabular-nums">
                      <div className="flex items-center gap-2">
                        <span
                          className={`font-semibold ${
                            app.consecutive_retries > 0
                              ? "text-amber-600"
                              : "text-slate-600"
                          }`}
                        >
                          {app.consecutive_retries} / {app.max_retries}
                        </span>
                        {app.consecutive_retries > 0 && (
                          <button
                            onClick={() => resetCounterMutation.mutate(app.id)}
                            className="text-[11px] text-blue-600 hover:underline font-semibold"
                            title="Reset consecutive retries to 0"
                          >
                            [Reset]
                          </button>
                        )}
                      </div>
                    </td>

                    {/* Last Exit Code */}
                    <td className="px-5 py-3.5 font-mono tabular-nums">
                      {app.last_exit_code !== null && app.last_exit_code !== undefined ? (
                        <span
                          className={`px-2 py-0.5 rounded-full text-[11px] font-semibold border ${
                            app.last_exit_code === 0
                              ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                              : "bg-rose-50 text-rose-700 border-rose-200"
                          }`}
                        >
                          code {app.last_exit_code}
                        </span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>

                    {/* Actions */}
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

                        <button
                          onClick={() => setConfirmDeleteId(app.id)}
                          className="p-2 rounded-xl bg-slate-50 hover:bg-rose-50 text-slate-400 hover:text-rose-600 border border-slate-200 transition-colors shadow-2xs"
                          title="Unregister Application"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
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
        isOpen={confirmStopId !== null}
        title="Stop Process?"
        message="Graceful stop requests intentionally do not trigger automatic recovery."
        confirmLabel="Stop Process"
        variant="warning"
        onConfirm={() => confirmStopId && stopMutation.mutate(confirmStopId)}
        onCancel={() => setConfirmStopId(null)}
      />

      <ConfirmDialog
        isOpen={confirmDeleteId !== null}
        title="Unregister Application?"
        message="This will terminate any running instance and remove the application registration from ResQ Web."
        confirmLabel="Unregister"
        variant="danger"
        onConfirm={() => confirmDeleteId && deleteMutation.mutate(confirmDeleteId)}
        onCancel={() => setConfirmDeleteId(null)}
      />

      <RegisterModal
        isOpen={isRegisterOpen}
        onClose={() => setIsRegisterOpen(false)}
      />
    </div>
  );
}
