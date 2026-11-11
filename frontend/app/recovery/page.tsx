"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useWebSocket } from "@/lib/websocket";
import { StatusBadge } from "@/components/StatusBadge";
import { MetricCard } from "@/components/MetricCard";
import { formatDate } from "@/lib/utils";
import { toast } from "sonner";
import Link from "next/link";
import {
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ShieldCheck,
  Zap,
  Calculator,
  RefreshCw,
} from "lucide-react";

export default function RecoveryManagementPage() {
  const queryClient = useQueryClient();

  // Test calculator state
  const [calcInitial, setCalcInitial] = useState<number>(1.0);
  const [calcMultiplier, setCalcMultiplier] = useState<number>(2.0);
  const [calcMaxDelay, setCalcMaxDelay] = useState<number>(30.0);

  const { data: apps = [], isLoading: isLoadingApps } = useQuery({
    queryKey: ["applications"],
    queryFn: api.getApplications,
    refetchInterval: 2500,
  });

  const { data: attempts = [], isLoading: isLoadingAttempts } = useQuery({
    queryKey: ["recoveryAttempts"],
    queryFn: () => api.getRecoveryAttempts(30),
    refetchInterval: 3000,
  });

  const { data: analytics } = useQuery({
    queryKey: ["analytics"],
    queryFn: api.getAnalyticsSummary,
    refetchInterval: 3000,
  });

  useWebSocket((payload) => {
    if (payload.type === "application_updated" || payload.type === "event") {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      queryClient.invalidateQueries({ queryKey: ["recoveryAttempts"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    }
  });

  const resetMutation = useMutation({
    mutationFn: (id: string) => api.resetRecoveryCounter(id),
    onSuccess: () => {
      toast.success("Retry counter reset to 0.");
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
    onError: (err: any) => toast.error(err.message),
  });

  // Calculate exponential sequence for preview
  const previewSequence = [0, 1, 2, 3, 4].map((retries) => {
    const raw = calcInitial * Math.pow(calcMultiplier, retries);
    return Math.min(raw, calcMaxDelay).toFixed(2);
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Metric Cards Header */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Recovery Success Rate"
          value={`${analytics?.recovery_success_rate ?? 0}%`}
          subtitle="Proportion of successful restarts"
          icon={CheckCircle2}
          badge="Fault Resilient"
          badgeType="success"
        />

        <MetricCard
          title="Total Recovery Attempts"
          value={analytics?.total_recovery_attempts ?? 0}
          subtitle={`${analytics?.successful_recoveries ?? 0} succeeded · ${analytics?.failed_recoveries ?? 0} aborted`}
          icon={RotateCcw}
          badgeType="default"
        />

        <MetricCard
          title="Mean Recovery Latency"
          value={`${((analytics?.average_recovery_latency_seconds ?? 0) * 1000).toFixed(0)} ms`}
          subtitle="Measured process creation overhead"
          icon={Clock}
          badge="Sub-second"
          badgeType="success"
        />

        <MetricCard
          title="Circuit Breakers Tripped"
          value={analytics?.failed_applications ?? 0}
          subtitle="Processes exceeding max retries"
          icon={AlertTriangle}
          badgeType={(analytics?.failed_applications ?? 0) > 0 ? "danger" : "default"}
        />
      </div>

      {/* Exponential Backoff Formula Calculator */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-4 gap-2">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-blue-50 text-blue-600 border border-blue-100">
              <Calculator className="w-4 h-4 stroke-[2.2]" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                Operating Systems Concept: Exponential Backoff Policy Simulator
              </h2>
              <p className="text-xs text-slate-500">
                Visualizes dynamic cooldown latency growth preventing restart storms.
              </p>
            </div>
          </div>
          <span className="text-xs font-mono font-bold text-blue-700 bg-blue-50 px-3 py-1.5 rounded-xl border border-blue-200">
            delay = min(initial × multiplier<sup>retries</sup>, max_delay)
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
            <div className="flex justify-between items-center mb-2">
              <label className="text-xs font-semibold text-slate-700">Initial Delay</label>
              <span className="text-xs font-bold text-blue-700 font-mono bg-white px-2 py-0.5 rounded border border-slate-200">
                {calcInitial}s
              </span>
            </div>
            <input
              type="range"
              min="0.5"
              max="5.0"
              step="0.5"
              value={calcInitial}
              onChange={(e) => setCalcInitial(parseFloat(e.target.value))}
              className="w-full accent-blue-600 cursor-pointer"
            />
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
            <div className="flex justify-between items-center mb-2">
              <label className="text-xs font-semibold text-slate-700">Multiplier</label>
              <span className="text-xs font-bold text-blue-700 font-mono bg-white px-2 py-0.5 rounded border border-slate-200">
                {calcMultiplier}x
              </span>
            </div>
            <input
              type="range"
              min="1.0"
              max="4.0"
              step="0.5"
              value={calcMultiplier}
              onChange={(e) => setCalcMultiplier(parseFloat(e.target.value))}
              className="w-full accent-blue-600 cursor-pointer"
            />
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
            <div className="flex justify-between items-center mb-2">
              <label className="text-xs font-semibold text-slate-700">Max Ceiling (Cap)</label>
              <span className="text-xs font-bold text-blue-700 font-mono bg-white px-2 py-0.5 rounded border border-slate-200">
                {calcMaxDelay}s
              </span>
            </div>
            <input
              type="range"
              min="5.0"
              max="60.0"
              step="5.0"
              value={calcMaxDelay}
              onChange={(e) => setCalcMaxDelay(parseFloat(e.target.value))}
              className="w-full accent-blue-600 cursor-pointer"
            />
          </div>
        </div>

        <div>
          <div className="text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">
            Simulated Cooldown Delay by Consecutive Failure:
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {previewSequence.map((delay, idx) => (
              <div key={idx} className="p-3.5 rounded-xl bg-white border border-slate-200 text-center shadow-2xs">
                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">
                  Failure #{idx + 1}
                </span>
                <span className="text-lg font-extrabold text-blue-600 font-mono tabular-nums mt-0.5 block">
                  {delay}s
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Applications Recovery State Table */}
      <div className="rounded-2xl bg-white border border-slate-200 overflow-hidden shadow-xs">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/60">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Per-Application Fault Policy Status
          </h2>
          <span className="text-xs text-slate-500 font-mono">
            {apps.length} applications
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 uppercase tracking-wider font-semibold text-[11px] border-b border-slate-200">
              <tr>
                <th className="px-5 py-3.5">Application</th>
                <th className="px-5 py-3.5">State</th>
                <th className="px-5 py-3.5">Auto Recovery</th>
                <th className="px-5 py-3.5">Consecutive Retries</th>
                <th className="px-5 py-3.5">Total Recoveries</th>
                <th className="px-5 py-3.5">Backoff Configuration</th>
                <th className="px-5 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700 font-normal">
              {apps.map((app) => (
                <tr key={app.id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="px-5 py-3.5 font-bold text-slate-900">
                    <Link href={`/applications/${app.id}`} className="hover:text-blue-600">
                      {app.name}
                    </Link>
                  </td>
                  <td className="px-5 py-3.5">
                    <StatusBadge status={app.status} />
                  </td>
                  <td className="px-5 py-3.5">
                    <span
                      className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${
                        app.auto_recovery
                          ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                          : "bg-slate-100 text-slate-600 border-slate-200"
                      }`}
                    >
                      {app.auto_recovery ? "Enabled" : "Disabled"}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 font-mono tabular-nums">
                    <span
                      className={`font-bold ${
                        app.consecutive_retries > 0 ? "text-amber-600" : "text-slate-600"
                      }`}
                    >
                      {app.consecutive_retries} / {app.max_retries}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 font-mono tabular-nums text-slate-900 font-semibold">
                    {app.total_recoveries}
                  </td>
                  <td className="px-5 py-3.5 font-mono text-[11px] text-slate-600">
                    {app.retry_delay_seconds}s × {app.backoff_multiplier} (max {app.max_delay_seconds}s)
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    {app.consecutive_retries > 0 && (
                      <button
                        onClick={() => resetMutation.mutate(app.id)}
                        className="px-3 py-1.5 text-xs font-semibold rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 transition-colors"
                      >
                        Reset Counter
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recovery History Log */}
      <div className="rounded-2xl bg-white border border-slate-200 overflow-hidden shadow-xs">
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/60">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Recent Automatic Recovery Attempts Audit Log
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 uppercase tracking-wider font-semibold text-[11px] border-b border-slate-200">
              <tr>
                <th className="px-5 py-3">Attempt #</th>
                <th className="px-5 py-3">Backoff Applied</th>
                <th className="px-5 py-3">Outcome</th>
                <th className="px-5 py-3 font-mono">New PID</th>
                <th className="px-5 py-3">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700 font-mono">
              {attempts.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-5 py-8 text-center text-slate-400 font-sans">
                    No recovery attempts recorded yet.
                  </td>
                </tr>
              ) : (
                attempts.map((att) => (
                  <tr key={att.id} className="hover:bg-slate-50/70">
                    <td className="px-5 py-3 font-bold text-slate-900">
                      Attempt #{att.attempt_number}
                    </td>
                    <td className="px-5 py-3 text-slate-600 font-semibold">
                      {att.backoff_delay_seconds.toFixed(2)}s delay
                    </td>
                    <td className="px-5 py-3 font-sans">
                      <span
                        className={`text-[11px] px-2.5 py-0.5 rounded-full font-bold border ${
                          att.status === "SUCCEEDED"
                            ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                            : att.status === "FAILED"
                            ? "bg-rose-50 text-rose-700 border-rose-200"
                            : "bg-amber-50 text-amber-700 border-amber-200"
                        }`}
                      >
                        {att.status}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-blue-600 font-bold">
                      {att.new_pid ?? "—"}
                    </td>
                    <td className="px-5 py-3 text-slate-500 font-sans">
                      {formatDate(att.created_at)}
                    </td>
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
