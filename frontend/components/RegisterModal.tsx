"use client";

import React, { useState } from "react";
import { X, Terminal, RotateCcw, HelpCircle, CheckCircle2, Play, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";

interface RegisterModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function RegisterModal({ isOpen, onClose }: RegisterModalProps) {
  const queryClient = useQueryClient();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    name: "",
    executable_path: "",
    arguments: "",
    working_dir: "",
    auto_recovery: true,
    max_retries: 3,
    retry_delay_seconds: 1.0,
    backoff_multiplier: 2.0,
    max_delay_seconds: 30.0,
  });

  if (!isOpen) return null;

  const handlePreset = (type: "worker" | "crasher" | "notepad") => {
    if (type === "worker") {
      setFormData((prev) => ({
        ...prev,
        name: "Heartbeat Worker Service",
        executable_path: "test_apps/worker_app.py",
        arguments: "BackgroundWorker 1.0",
        auto_recovery: true,
        max_retries: 3,
        retry_delay_seconds: 1.0,
      }));
    } else if (type === "crasher") {
      setFormData((prev) => ({
        ...prev,
        name: "Crash Test App (Exit 42)",
        executable_path: "test_apps/crasher_app.py",
        arguments: "--crash-after 4.0 --exit-code 42",
        auto_recovery: true,
        max_retries: 3,
        retry_delay_seconds: 1.5,
        backoff_multiplier: 2.0,
      }));
    } else if (type === "notepad") {
      setFormData((prev) => ({
        ...prev,
        name: "Windows Notepad",
        executable_path: "notepad.exe",
        arguments: "",
        auto_recovery: true,
        max_retries: 2,
        retry_delay_seconds: 1.0,
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.executable_path.trim()) {
      toast.error("Application name and executable path are required.");
      return;
    }

    setIsSubmitting(true);
    try {
      await api.createApplication({
        name: formData.name.trim(),
        executable_path: formData.executable_path.trim(),
        arguments: formData.arguments.trim(),
        working_dir: formData.working_dir.trim() || undefined,
        auto_recovery: formData.auto_recovery,
        max_retries: Number(formData.max_retries),
        retry_delay_seconds: Number(formData.retry_delay_seconds),
        backoff_multiplier: Number(formData.backoff_multiplier),
        max_delay_seconds: Number(formData.max_delay_seconds),
      });

      toast.success(`Application '${formData.name}' registered successfully!`);
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
      onClose();
    } catch (err: any) {
      toast.error(err.message || "Failed to register application.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs overflow-y-auto animate-in fade-in duration-150">
      <div className="w-full max-w-xl bg-white border border-slate-200 rounded-2xl shadow-2xl overflow-hidden my-8">
        {/* Header */}
        <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/60">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-blue-50 text-blue-600 border border-blue-100">
              <Terminal className="w-5 h-5 stroke-[2.2]" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">
                Register Windows Application
              </h2>
              <p className="text-xs text-slate-500">
                Authorize ResQ Web to supervise, monitor, and recover a process.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Quick Presets */}
        <div className="px-6 pt-3.5 pb-2 border-b border-slate-100 bg-blue-50/30">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-blue-600" /> Quick Demonstration Presets:
          </div>
          <div className="flex flex-wrap gap-2 pb-2">
            <button
              type="button"
              onClick={() => handlePreset("worker")}
              className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 shadow-2xs transition-all hover:border-slate-300"
            >
              + Normal Worker
            </button>
            <button
              type="button"
              onClick={() => handlePreset("crasher")}
              className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-white hover:bg-slate-50 text-amber-700 border border-amber-200 shadow-2xs transition-all hover:border-amber-300"
            >
              + Fault Crasher (Exit 42)
            </button>
            <button
              type="button"
              onClick={() => handlePreset("notepad")}
              className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-white hover:bg-slate-50 text-emerald-700 border border-emerald-200 shadow-2xs transition-all hover:border-emerald-300"
            >
              + Windows Notepad
            </button>
          </div>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Application Name <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g. Heartbeat Worker Service"
              className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all font-medium"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Executable Path <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              required
              value={formData.executable_path}
              onChange={(e) => setFormData({ ...formData, executable_path: e.target.value })}
              placeholder="e.g. test_apps/worker_app.py or notepad.exe"
              className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all font-mono text-[11px]"
            />
            <p className="mt-1 text-[11px] text-slate-500">
              Target binary in PATH, relative script, or absolute system path.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Command Arguments
              </label>
              <input
                type="text"
                value={formData.arguments}
                onChange={(e) => setFormData({ ...formData, arguments: e.target.value })}
                placeholder="--arg value"
                className="w-full px-3.5 py-2 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-500 font-mono text-[11px]"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Working Directory (Optional)
              </label>
              <input
                type="text"
                value={formData.working_dir}
                onChange={(e) => setFormData({ ...formData, working_dir: e.target.value })}
                placeholder="Defaults to executable parent"
                className="w-full px-3.5 py-2 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-500 text-xs"
              />
            </div>
          </div>

          {/* Recovery Policy Box */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <RotateCcw className="w-4 h-4 text-blue-600" />
                <span className="text-xs font-bold text-slate-800">
                  Automatic Recovery Policy (Backoff)
                </span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.auto_recovery}
                  onChange={(e) => setFormData({ ...formData, auto_recovery: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            {formData.auto_recovery && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-1.5">
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">Max Retries</label>
                  <input
                    type="number"
                    min="0"
                    max="50"
                    value={formData.max_retries}
                    onChange={(e) => setFormData({ ...formData, max_retries: parseInt(e.target.value) || 0 })}
                    className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-semibold text-slate-900"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">Delay (s)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0.1"
                    value={formData.retry_delay_seconds}
                    onChange={(e) => setFormData({ ...formData, retry_delay_seconds: parseFloat(e.target.value) || 1.0 })}
                    className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-semibold text-slate-900"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">Multiplier</label>
                  <input
                    type="number"
                    step="0.1"
                    min="1.0"
                    value={formData.backoff_multiplier}
                    onChange={(e) => setFormData({ ...formData, backoff_multiplier: parseFloat(e.target.value) || 1.0 })}
                    className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-semibold text-slate-900"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">Cap Ceiling (s)</label>
                  <input
                    type="number"
                    min="1"
                    value={formData.max_delay_seconds}
                    onChange={(e) => setFormData({ ...formData, max_delay_seconds: parseFloat(e.target.value) || 30.0 })}
                    className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-semibold text-slate-900"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-2.5 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 bg-slate-50 border border-slate-200 rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-xl shadow-xs transition-all disabled:opacity-50"
            >
              {isSubmitting ? "Registering..." : "Register Application"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
