# ResQ Web — REST & WebSocket API Specification

**Base URL:** `http://127.0.0.1:8000/api/v1`  
**WebSocket URL:** `ws://127.0.0.1:8000/ws`  
**Interactive Documentation:** `http://127.0.0.1:8000/docs` (Swagger UI) / `http://127.0.0.1:8000/redoc` (ReDoc)

---

## 1. Application Management Endpoints

### 1.1 List All Applications
- **Method & Path:** `GET /applications`
- **Description:** Returns all registered applications with their live running state, current PID, uptime, and real-time CPU/memory metrics.
- **Response (200 OK):**
```json
[
  {
    "id": "c1f77d6e-939e-4db9-a864-15949d8a5712",
    "name": "Heartbeat Worker Service",
    "executable_path": "C:\\ResQ Web\\test_apps\\worker_app.py",
    "arguments": "Worker1 1.0",
    "working_dir": null,
    "auto_recovery": true,
    "max_retries": 3,
    "retry_delay_seconds": 1.0,
    "backoff_multiplier": 2.0,
    "max_delay_seconds": 30.0,
    "status": "RUNNING",
    "current_pid": 28540,
    "uptime_seconds": 45.2,
    "cpu_percent": 0.1,
    "memory_rss_bytes": 16777216,
    "memory_percent": 0.05,
    "num_threads": 2,
    "num_handles": 38,
    "consecutive_retries": 0,
    "total_recoveries": 0,
    "last_exit_code": null,
    "last_crash_timestamp": null,
    "created_at": "2026-11-05T14:40:00Z",
    "updated_at": "2026-11-05T14:40:00Z"
  }
]
```

### 1.2 Register New Application
- **Method & Path:** `POST /applications`
- **Request Body:**
```json
{
  "name": "Crash Fault Injection App",
  "executable_path": "test_apps/crasher_app.py",
  "arguments": "--crash-after 4.0 --exit-code 42",
  "working_dir": null,
  "auto_recovery": true,
  "max_retries": 3,
  "retry_delay_seconds": 1.5,
  "backoff_multiplier": 2.0,
  "max_delay_seconds": 30.0
}
```
- **Responses:**
  - `201 Created`: Application successfully registered and validated.
  - `400 Bad Request`: Invalid executable path or security policy violation.
  - `422 Unprocessable Entity`: Missing required fields or schema validation failure.

### 1.3 Get Application Details
- **Method & Path:** `GET /applications/{id}`
- **Response (200 OK):** Detailed application object with live telemetry.
- **Response (404 Not Found):** `{"detail": "Application not found"}`

### 1.4 Update Application Configuration
- **Method & Path:** `PUT /applications/{id}`
- **Request Body:** Subset of application fields (Pydantic `ApplicationUpdate`).
- **Response (200 OK):** Updated application object.

### 1.5 Unregister Application
- **Method & Path:** `DELETE /applications/{id}`
- **Description:** Forcibly terminates any running instance, cleans up Win32 Job Objects, and removes registration from the database.
- **Response:** `204 No Content`

### 1.6 Execution Runs History
- **Method & Path:** `GET /applications/{id}/runs`
- **Response (200 OK):** Array of historical process runs including PIDs, durations, exit codes, and termination types (`ACTIVE`, `EXPECTED`, `UNEXPECTED`).

---

## 2. Process Control Endpoints

### 2.1 Launch Application Process
- **Method & Path:** `POST /applications/{id}/start`
- **Description:** Validates state machine (must be `STOPPED` or `FAILED`), spawns the process using native Win32 handles, creates a Job Object, and starts the watcher thread.
- **Response (200 OK):**
```json
{
  "success": true,
  "message": "Process launch initiated for application Heartbeat Worker.",
  "app_id": "c1f77d6e-939e-4db9-a864-15949d8a5712",
  "status": "RUNNING",
  "pid": 28540
}
```

### 2.2 Graceful Process Stop
- **Method & Path:** `POST /applications/{id}/stop`
- **Description:** Atomically transitions state machine to `STOPPING`, sends graceful stop signal, falls back to `TerminateProcess` if necessary, and **suppresses automatic recovery**.
- **Response (200 OK):**
```json
{
  "success": true,
  "message": "Stop signal sent to application Heartbeat Worker.",
  "app_id": "c1f77d6e-939e-4db9-a864-15949d8a5712",
  "status": "STOPPED",
  "pid": null
}
```

### 2.3 Restart Process
- **Method & Path:** `POST /applications/{id}/restart`
- **Description:** Performs a controlled stop and subsequent launch.
- **Response (200 OK):** Process control response with new PID.

### 2.4 Reset Consecutive Retry Counter
- **Method & Path:** `POST /applications/{id}/reset-counter`
- **Description:** Resets consecutive retry counter to 0 and transitions `FAILED` state back to `STOPPED`.

---

## 3. Telemetry & Analytics Endpoints

### 3.1 Get Event History
- **Method & Path:** `GET /events`
- **Query Parameters:**
  - `app_id` (optional): Filter by application UUID.
  - `severity` (optional): Filter by `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.
  - `search` (optional): Free-text search in messages.
  - `limit` (default: 50): Number of records.
  - `offset` (default: 0): Pagination offset.
- **Response (200 OK):** Array of stored audit events.

### 3.2 Current System Metrics
- **Method & Path:** `GET /metrics/current`
- **Response (200 OK):**
```json
{
  "cpu_percent": 12.4,
  "cpu_count": 16,
  "memory_total": 34241777664,
  "memory_available": 18253611008,
  "memory_used": 15988166656,
  "memory_percent": 46.7,
  "managed_process_count": 2,
  "total_applications": 3
}
```

### 3.3 Analytics Summary
- **Method & Path:** `GET /analytics/summary`
- **Response (200 OK):**
```json
{
  "total_applications": 3,
  "running_applications": 1,
  "stopped_applications": 2,
  "recovering_applications": 0,
  "failed_applications": 0,
  "total_recovery_attempts": 6,
  "successful_recoveries": 6,
  "failed_recoveries": 0,
  "recovery_success_rate": 100.0,
  "average_recovery_latency_seconds": 0.048,
  "average_crash_detection_latency_seconds": 0.145,
  "system_cpu_percent": 12.4,
  "system_memory_percent": 46.7,
  "system_memory_used_mb": 15247.5,
  "system_memory_total_mb": 32655.5
}
```

### 3.4 System Health & Academic Info
- **Method & Path:** `GET /system/health`
- **Method & Path:** `GET /system/info`

---

## 4. WebSocket Real-Time API Contract

Clients connect via `ws://127.0.0.1:8000/ws`.

### 4.1 Broadcast Event Payloads

#### `application_updated`
Broadcast whenever an application transitions states, captures a new PID, or recovers:
```json
{
  "type": "application_updated",
  "data": {
    "id": "c1f77d6e-939e-4db9-a864-15949d8a5712",
    "name": "Crasher",
    "status": "RUNNING",
    "current_pid": 29840,
    "uptime_seconds": 0.5,
    "cpu_percent": 0.0,
    "memory_rss_bytes": 12450000
  }
}
```

#### `system_metrics` (Tick every 2.0s)
```json
{
  "type": "system_metrics",
  "data": {
    "cpu_percent": 11.8,
    "memory_total_bytes": 34241777664,
    "memory_used_bytes": 15988166656,
    "memory_percent": 46.7,
    "managed_process_count": 2,
    "timestamp": "2026-11-05T14:45:10Z"
  }
}
```

#### `event` (Process Crash / Recovery Notification)
```json
{
  "type": "event",
  "data": {
    "id": "e2f18374-9a01-4475-b65a-8b15d2e73111",
    "app_name": "Crasher",
    "event_type": "PROCESS_CRASHED_UNEXPECTED",
    "severity": "ERROR",
    "message": "Application 'Crasher' (PID: 28540) terminated unexpectedly with exit code 42 after 4.02 seconds.",
    "pid": 28540,
    "exit_code": 42,
    "timestamp": "2026-11-05T14:45:14Z"
  }
}
```

