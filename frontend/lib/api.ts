import {
  Application,
  ApplicationCreatePayload,
  EventItem,
  SystemMetrics,
  AnalyticsSummary,
  ProcessRun,
  RecoveryAttemptItem,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

async function fetcher<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });

  if (!res.ok) {
    let errorDetail = "API Request Failed";
    try {
      const err = await res.json();
      errorDetail = err.detail || JSON.stringify(err);
    } catch {
      errorDetail = await res.text();
    }
    throw new Error(errorDetail);
  }

  if (res.status === 204) {
    return {} as T;
  }

  return res.json();
}

export const api = {
  // Applications
  getApplications: () => fetcher<Application[]>("/api/v1/applications"),
  getApplication: (id: string) => fetcher<Application>(`/api/v1/applications/${id}`),
  createApplication: (data: ApplicationCreatePayload) =>
    fetcher<Application>("/api/v1/applications", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateApplication: (id: string, data: Partial<ApplicationCreatePayload>) =>
    fetcher<Application>(`/api/v1/applications/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  deleteApplication: (id: string) =>
    fetcher<void>(`/api/v1/applications/${id}`, {
      method: "DELETE",
    }),
  getApplicationRuns: (id: string) =>
    fetcher<ProcessRun[]>(`/api/v1/applications/${id}/runs`),

  // Process Controls
  startProcess: (id: string) =>
    fetcher<{ success: boolean; message: string; pid?: number; status: string }>(
      `/api/v1/applications/${id}/start`,
      { method: "POST" }
    ),
  stopProcess: (id: string) =>
    fetcher<{ success: boolean; message: string; status: string }>(
      `/api/v1/applications/${id}/stop`,
      { method: "POST" }
    ),
  restartProcess: (id: string) =>
    fetcher<{ success: boolean; message: string; pid?: number; status: string }>(
      `/api/v1/applications/${id}/restart`,
      { method: "POST" }
    ),
  resetRecoveryCounter: (id: string) =>
    fetcher<{ success: boolean; message: string }>(
      `/api/v1/applications/${id}/reset-counter`,
      { method: "POST" }
    ),

  // Events
  getEvents: (params?: { app_id?: string; event_type?: string; severity?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.app_id) q.append("app_id", params.app_id);
    if (params?.event_type) q.append("event_type", params.event_type);
    if (params?.severity) q.append("severity", params.severity);
    if (params?.limit) q.append("limit", params.limit.toString());
    const query = q.toString() ? `?${q.toString()}` : "";
    return fetcher<EventItem[]>(`/api/v1/events${query}`);
  },

  // Metrics
  getCurrentMetrics: () => fetcher<SystemMetrics>("/api/v1/metrics/current"),
  getMetricsHistory: (limit: number = 30) =>
    fetcher<SystemMetrics[]>(`/api/v1/metrics/history?limit=${limit}`),

  // Analytics
  getAnalyticsSummary: () => fetcher<AnalyticsSummary>("/api/v1/analytics/summary"),
  getRecoveryTimeline: () => fetcher<RecoveryAttemptItem[]>("/api/v1/analytics/recovery-timeline"),

  // Recovery
  getRecoveryAttempts: (limit: number = 50) =>
    fetcher<RecoveryAttemptItem[]>(`/api/v1/recovery/attempts?limit=${limit}`),
  updateRecoveryPolicy: (
    appId: string,
    policy: {
      auto_recovery: boolean;
      max_retries: number;
      retry_delay_seconds: number;
      backoff_multiplier: number;
      max_delay_seconds: number;
    }
  ) =>
    fetcher<Application>(`/api/v1/recovery/applications/${appId}/policy`, {
      method: "PUT",
      body: JSON.stringify(policy),
    }),

  // System
  getHealth: () =>
    fetcher<{ status: string; agent: string; platform: string; os: string; python_version: string; cpu_count: number }>(
      "/api/v1/system/health"
    ),
  getSystemInfo: () =>
    fetcher<{
      product_name: string;
      full_title: string;
      version: string;
      operating_system: string;
      team_members: Array<{ name: string; student_id: string }>;
    }>("/api/v1/system/info"),
};

