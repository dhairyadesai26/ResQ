export type ProcessState =
  | "STOPPED"
  | "STARTING"
  | "RUNNING"
  | "STOPPING"
  | "RECOVERY_WAIT"
  | "FAILED";

export interface Application {
  id: string;
  name: string;
  executable_path: string;
  arguments?: string;
  working_dir?: string | null;
  auto_recovery: boolean;
  max_retries: number;
  retry_delay_seconds: number;
  backoff_multiplier: number;
  max_delay_seconds: number;
  status: ProcessState;
  current_pid?: number | null;
  uptime_seconds: number;
  cpu_percent: number;
  memory_rss_bytes: number;
  memory_percent: number;
  num_threads: number;
  num_handles: number;
  consecutive_retries: number;
  total_recoveries: number;
  last_exit_code?: number | null;
  last_crash_timestamp?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApplicationCreatePayload {
  name: string;
  executable_path: string;
  arguments?: string;
  working_dir?: string;
  auto_recovery: boolean;
  max_retries: number;
  retry_delay_seconds: number;
  backoff_multiplier: number;
  max_delay_seconds: number;
}

export interface EventItem {
  id: string;
  app_id?: string | null;
  app_name?: string | null;
  event_type: string;
  severity: "INFO" | "WARNING" | "ERROR" | "CRITICAL";
  message: string;
  pid?: number | null;
  exit_code?: number | null;
  details?: string | null;
  timestamp: string;
}

export interface SystemMetrics {
  cpu_percent: number;
  memory_used_bytes: number;
  memory_available_bytes: number;
  memory_total_bytes: number;
  memory_percent: number;
  managed_process_count: number;
  timestamp: string;
}

export interface AnalyticsSummary {
  total_applications: number;
  running_applications: number;
  stopped_applications: number;
  recovering_applications: number;
  failed_applications: number;
  total_recovery_attempts: number;
  successful_recoveries: number;
  failed_recoveries: number;
  recovery_success_rate: number;
  average_recovery_latency_seconds: number;
  average_crash_detection_latency_seconds: number;
  system_cpu_percent: number;
  system_memory_percent: number;
  system_memory_used_mb: number;
  system_memory_total_mb: number;
}

export interface ProcessRun {
  id: string;
  pid: number;
  start_time: string;
  end_time?: string | null;
  duration_seconds?: number | null;
  exit_code?: number | null;
  termination_type: "ACTIVE" | "EXPECTED" | "UNEXPECTED";
}

export interface RecoveryAttemptItem {
  id: string;
  app_id: string;
  attempt_number: number;
  backoff_delay_seconds: number;
  status: "SCHEDULED" | "STARTED" | "SUCCEEDED" | "FAILED";
  error_message?: string | null;
  new_pid?: number | null;
  created_at: string;
}

