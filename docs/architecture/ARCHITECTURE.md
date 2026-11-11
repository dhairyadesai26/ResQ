# ResQ Web — System Architecture Specification

## 1. Architectural Overview

ResQ Web is built as a layered, fault-tolerant process supervision and automatic recovery platform for Windows. It provides strict isolation between user interface presentation, API validation, state persistence, and native Windows operating system calls.

```mermaid
flowchart TD
    subgraph Browser ["Layer 1: Frontend Dashboard (Next.js 14)"]
        UI["React 18 / Tailwind CSS UI"]
        TQ["TanStack Query (Server State)"]
        WSClient["WebSocket Client Manager"]
    end

    subgraph Backend ["Layer 2: API & Telemetry (FastAPI)"]
        Router["REST API Router (/api/v1)"]
        WSManager["WebSocket Connection Manager"]
        AppService["Application & Persistence Service"]
        MetricService["Metrics Collection Daemon"]
        DB[(SQLite in WAL Mode)]
    end

    subgraph Supervisor ["Layer 3: Local Process Supervisor"]
        Engine["ProcessMonitorEngine (Concurrency Control)"]
        SM["Deterministic Process State Machine"]
        Watcher["ProcessWatcherThread (WaitForSingleObject)"]
        Detector["ProcessTerminationDetector"]
        Orchestrator["RecoveryOrchestrator (Exponential Backoff)"]
        Bus["Supervisor EventEmitter"]
    end

    subgraph OS ["Layer 4: Windows Operating System Kernel"]
        Win32["Win32 Kernel32 APIs"]
        Handles["Process Handle Table"]
        Jobs["Windows Job Objects (Tree Tracking)"]
        Procs["Supervised Windows Applications"]
    end

    Browser <-->|HTTP REST & WebSockets| Backend
    Backend <-->|In-Process Thread-Safe IPC| Supervisor
    Supervisor <-->|Native Ctypes & pywin32| OS
```

---

## 2. Component Descriptions

### Layer 1: Frontend Dashboard (Next.js 14 App Router)
- **Role:** Centralized developer operations interface for operators.
- **Tech Stack:** Next.js 14, React 18, TypeScript, Tailwind CSS, Lucide React, TanStack Query v5, Recharts.
- **Key Modules:**
  - `app/page.tsx`: System overview, KPI cards, real-time metrics, active applications table, recent event feed.
  - `app/applications/page.tsx`: Application inventory, state filtering, full lifecycle actions (Launch, Stop, Restart, Delete).
  - `app/applications/[id]/page.tsx`: Telemetry deep dive, per-process CPU/RAM footprint, thread counts, OS handle counts, historical process run log.
  - `app/recovery/page.tsx`: Backoff policy controls, interactive simulator, recovery attempt logs.
  - `app/system/page.tsx`: System-wide CPU and RAM area charts, per-process resource breakdown.
  - `app/analytics/page.tsx`: Empirical MTTR, crash detection latency, recovery success rate analytics.
  - `app/logs/page.tsx`: Filterable, searchable diagnostic log viewer.
  - `app/settings/page.tsx`: Component health statuses, academic team credits.

### Layer 2: Backend API & Telemetry (FastAPI)
- **Role:** Validates operator requests, enforces authorization boundaries, persists state and audit history, and broadcasts real-time telemetry.
- **Tech Stack:** Python 3.12/3.13, FastAPI, Pydantic v2, SQLAlchemy 2.0 with SQLite WAL mode.
- **Key Services:**
  - `ApplicationService`: Synchronizes database entities with the supervisor engine's memory state.
  - `EventService`: Subscribes to the supervisor's event bus and persists audit logs.
  - `MetricsCollectorService`: Background thread that samples CPU, RAM, and process counts every 2 seconds.
  - `ConnectionManager`: Multi-client WebSocket broadcaster.

### Layer 3: Local Windows Process Supervisor
- **Role:** The core Operating Systems engine that interfaces with the Windows NT executive.
- **Key Modules:**
  - `ProcessLauncher`: Validates binary paths, prevents path traversal, and executes processes using `shell=False`.
  - `ProcessHandle`: RAII wrapper for native Windows handles (`OpenProcess`, `CloseHandle`).
  - `JobObject`: Win32 Job Object wrapper enforcing `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`.
  - `ProcessWatcherThread`: Asynchronous background thread executing non-busy `WaitForSingleObject` kernel waits.
  - `ProcessTerminationDetector`: Distinguishes expected user-initiated stops from unexpected crashes.
  - `RecoveryOrchestrator`: Coordinates exponential backoff delays, retry limits, and relaunches with thread-safe locking.
  - `ProcessStateMachine`: Enforces deterministic state transitions.

---

## 3. Process Lifecycle Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User as Operator / Web UI
    participant Backend as FastAPI Backend
    participant Supervisor as Process Supervisor
    participant Kernel as Windows Kernel
    participant App as Target Process

    User->>Backend: POST /api/v1/applications/{id}/start
    Backend->>Supervisor: start_application(id)
    Supervisor->>Supervisor: Transition State: STOPPED -> STARTING
    Supervisor->>Kernel: CreateProcessW / subprocess.Popen (shell=False)
    Kernel->>App: Spawn Process & Assign New PID
    Supervisor->>Kernel: OpenProcess (SYNCHRONIZE | QUERY_INFO)
    Supervisor->>Supervisor: Transition State: STARTING -> RUNNING
    Supervisor->>Backend: Emit Event: PROCESS_LAUNCHED (PID)
    Backend->>User: WebSocket Broadcast State: RUNNING

    Note over Supervisor,Kernel: Kernel Event-Driven Monitoring
    Supervisor->>Kernel: WaitForSingleObject(handle, 250ms)

    alt Unexpected Process Crash
        App->>Kernel: Fatal Fault / Crash (Exit Code 42)
        Kernel-->>Supervisor: Signal Process Handle (WAIT_OBJECT_0)
        Supervisor->>Kernel: GetExitCodeProcess(handle)
        Kernel-->>Supervisor: Exit Code = 42
        Supervisor->>Supervisor: Check State: RUNNING -> Unexpected Crash!
        Supervisor->>Supervisor: Transition State: RECOVERY_WAIT
        Supervisor->>Backend: Emit Event: PROCESS_CRASHED_UNEXPECTED
        Supervisor->>Supervisor: Sleep Exponential Backoff Delay
        Supervisor->>Kernel: CreateProcessW (Relaunch)
        Kernel->>App: Spawn New Process with NEW PID
        Supervisor->>Supervisor: Transition State: RUNNING
        Supervisor->>Backend: Emit Event: RECOVERY_SUCCEEDED (New PID)
        Backend->>User: WebSocket Broadcast: Recovered with New PID
    else Expected User Stop
        User->>Backend: POST /api/v1/applications/{id}/stop
        Backend->>Supervisor: stop_application(id)
        Supervisor->>Supervisor: Transition State: STOPPING
        Supervisor->>App: Terminate Process Signal
        Kernel-->>Supervisor: Signal Process Handle
        Supervisor->>Supervisor: Check State: STOPPING -> Expected Stop!
        Supervisor->>Supervisor: Transition State: STOPPED
        Supervisor->>Backend: Emit Event: PROCESS_STOPPED_EXPECTED (No Recovery)
        Backend->>User: WebSocket Broadcast State: STOPPED
    end
```

---

## 4. Database Schema (Entity-Relationship)

```mermaid
erDiagram
    Application ||--o{ ProcessRun : "tracks"
    Application ||--o{ RecoveryAttempt : "records"
    Application ||--o{ Event : "generates"

    Application {
        string id PK
        string name
        string executable_path
        string arguments
        string working_dir
        boolean auto_recovery
        int max_retries
        float retry_delay_seconds
        float backoff_multiplier
        float max_delay_seconds
        string status
        int current_pid
        int consecutive_retries
        int total_recoveries
        datetime created_at
    }

    ProcessRun {
        string id PK
        string app_id FK
        int pid
        datetime start_time
        datetime end_time
        float duration_seconds
        int exit_code
        string termination_type
    }

    RecoveryAttempt {
        string id PK
        string app_id FK
        int attempt_number
        float backoff_delay_seconds
        string status
        int new_pid
        string error_message
        datetime created_at
    }

    Event {
        string id PK
        string app_id
        string app_name
        string event_type
        string severity
        string message
        int pid
        int exit_code
        string details
        datetime timestamp
    }

    SystemMetric {
        string id PK
        float cpu_percent
        int memory_used_bytes
        int memory_total_bytes
        float memory_percent
        int managed_process_count
        datetime timestamp
    }
```

