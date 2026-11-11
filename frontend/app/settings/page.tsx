"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useWebSocket } from "@/lib/websocket";
import {
  Settings,
  ShieldCheck,
  Server,
  Database,
  Radio,
  Users,
  GraduationCap,
  Terminal,
  CheckCircle2,
  Lock,
  Cpu,
  User,
  Hash,
  Activity,
  Layers,
} from "lucide-react";

export default function SettingsPage() {
  const { isConnected } = useWebSocket();
  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: api.getHealth,
  });

  const { data: systemInfo } = useQuery({
    queryKey: ["systemInfo"],
    queryFn: api.getSystemInfo,
  });

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2.5">
            <Settings className="w-5 h-5 text-blue-600" />
            System Architecture & Academic Settings
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Component health, inter-process communication topology, security constraints, and academic project credits.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            Localhost Secure
          </span>
        </div>
      </div>

      {/* System Status & Architecture */}
      <div className="p-6 rounded-xl bg-white border border-slate-200 shadow-xs space-y-4">
        <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Server className="w-5 h-5 text-blue-600" />
            <h2 className="text-sm font-semibold text-slate-900">
              System Components & IPC Status
            </h2>
          </div>
          <span className="text-xs font-mono text-slate-500">
            PID Supervision Topology
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          {/* Agent Supervisor */}
          <div className="p-4 rounded-lg bg-slate-50/70 border border-slate-200/90 space-y-2.5 hover:border-slate-300 transition-colors">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-900 flex items-center gap-1.5">
                <Cpu className="w-4 h-4 text-blue-600" />
                Process Supervisor
              </span>
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  health?.agent === "online" ? "bg-emerald-500 ring-2 ring-emerald-100" : "bg-rose-500"
                }`}
              />
            </div>
            <p className="text-slate-600 text-xs leading-relaxed">
              Direct Win32 kernel interface using WaitForSingleObject and Windows Job Objects.
            </p>
            <div className="pt-1.5 border-t border-slate-200 text-[11px] font-mono text-slate-500 flex items-center justify-between">
              <span>Platform: {health?.platform || "win32"}</span>
              <span>Python {health?.python_version || "3.13"}</span>
            </div>
          </div>

          {/* Database */}
          <div className="p-4 rounded-lg bg-slate-50/70 border border-slate-200/90 space-y-2.5 hover:border-slate-300 transition-colors">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-900 flex items-center gap-1.5">
                <Database className="w-4 h-4 text-blue-600" />
                Database Engine
              </span>
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-emerald-100" />
            </div>
            <p className="text-slate-600 text-xs leading-relaxed">
              SQLite configured in WAL mode (Write-Ahead Logging) for safe concurrent telemetry.
            </p>
            <div className="pt-1.5 border-t border-slate-200 text-[11px] font-mono text-slate-500 flex items-center justify-between">
              <span>Journal: WAL</span>
              <span>Sync: NORMAL</span>
            </div>
          </div>

          {/* WebSocket */}
          <div className="p-4 rounded-lg bg-slate-50/70 border border-slate-200/90 space-y-2.5 hover:border-slate-300 transition-colors">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-900 flex items-center gap-1.5">
                <Radio className="w-4 h-4 text-blue-600" />
                Live WebSocket Feed
              </span>
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  isConnected ? "bg-emerald-500 ring-2 ring-emerald-100 animate-pulse" : "bg-rose-500"
                }`}
              />
            </div>
            <p className="text-slate-600 text-xs leading-relaxed">
              Bi-directional reactive push of state transitions, crash alerts, and metrics.
            </p>
            <div className="pt-1.5 border-t border-slate-200 text-[11px] font-mono text-slate-500 flex items-center justify-between">
              <span>Status: {isConnected ? "Connected" : "Reconnecting"}</span>
              <span>Port: 8000</span>
            </div>
          </div>
        </div>
      </div>

      {/* Security Policies */}
      <div className="p-6 rounded-xl bg-white border border-slate-200 shadow-xs space-y-4">
        <div className="border-b border-slate-100 pb-3 flex items-center gap-2">
          <Lock className="w-5 h-5 text-blue-600" />
          <h2 className="text-sm font-semibold text-slate-900">
            Security & Process Execution Boundaries
          </h2>
        </div>

        <div className="space-y-3 text-xs text-slate-700">
          <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 border border-slate-200/80">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <strong className="text-slate-900">No Arbitrary Shell Invocation:</strong> Process creation strictly enforces{" "}
              <code className="text-blue-600 font-mono bg-blue-50 px-1 py-0.5 rounded border border-blue-200">shell=False</code>. Arbitrary command-line injection attacks via delimiters (like <code className="font-mono text-slate-800">&amp;&amp;</code> or <code className="font-mono text-slate-800">;</code>) are fundamentally prevented.
            </div>
          </div>

          <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 border border-slate-200/80">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <strong className="text-slate-900">Path Traversal &amp; Executable Verification:</strong> All registered executable paths are canonicalized through{" "}
              <code className="text-blue-600 font-mono bg-blue-50 px-1 py-0.5 rounded border border-blue-200">os.path.abspath</code> and validated against filesystem existence and execution permissions prior to spawning.
            </div>
          </div>

          <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 border border-slate-200/80">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <strong className="text-slate-900">Strict Localhost Binding:</strong> The backend API and process supervisor bind exclusively to{" "}
              <code className="text-blue-600 font-mono bg-blue-50 px-1 py-0.5 rounded border border-blue-200">127.0.0.1</code> to prevent any unsolicited external network tampering.
            </div>
          </div>
        </div>
      </div>

      {/* Academic Project Credits & Group Members */}
      <div className="p-6 rounded-xl bg-white border border-slate-200 shadow-xs space-y-4">
        <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <GraduationCap className="w-5 h-5 text-blue-600" />
            <div>
              <h2 className="text-sm font-semibold text-slate-900">
                Operating Systems Academic Project Information
              </h2>
              <p className="text-xs text-slate-500">
                Third-Year B.Tech Computer Science and Engineering Course Project
              </p>
            </div>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded bg-blue-50 text-blue-700 border border-blue-200">
            CSE B.Tech 3rd Year
          </span>
        </div>

        <div>
          <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <Users className="w-4 h-4 text-slate-500" /> Project Team Members:
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {[
              { name: "Dhairya Desai", id: "202451051" },
              { name: "Neet Bhimani", id: "202451035" },
              { name: "Mrugen Bhalodiya", id: "202451031" },
              { name: "Keval Chorada", id: "202451089" },
              { name: "Svetal Barad", id: "202452311" },
            ].map((member, i) => (
              <div
                key={member.id}
                className="p-3.5 rounded-lg bg-slate-50/80 border border-slate-200 text-xs flex items-center justify-between hover:bg-slate-50 transition-colors"
              >
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-xs shrink-0">
                    {member.name.charAt(0)}
                  </div>
                  <div>
                    <div className="font-semibold text-slate-900">{member.name}</div>
                    <div className="text-[11px] text-slate-500 font-mono">ID: {member.id}</div>
                  </div>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600 font-mono font-medium">
                  #{i + 1}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="pt-3 border-t border-slate-100 text-xs text-slate-600 leading-relaxed bg-slate-50/50 p-4 rounded-lg border border-slate-200/60">
          <div className="font-semibold text-slate-800 mb-1">
            ResQ Web — A Web-Based Process Monitoring and Automatic Recovery System for Windows
          </div>
          <p className="text-slate-500">
            <strong>Demonstrated Operating Systems Principles:</strong> User-mode process supervision, process lifecycle state machines, Win32 WaitForSingleObject synchronization handles, process exit code collection, Windows Job Objects for hierarchical process-tree cleanup, exponential backoff fault recovery policies, mutual exclusion synchronization primitives, and local IPC.
          </p>
        </div>
      </div>
    </div>
  );
}
