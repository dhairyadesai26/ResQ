# ResQ Web: A Web-Based Process Monitoring and Automatic Recovery System for Windows

## Master Academic Project Report

**Degree Program:** Third-Year Bachelor of Technology (B.Tech) in Computer Science & Engineering  
**Course:** Operating Systems  
**Academic Year:** 2026  

---

### Project Team Members:
1. **Dhairya Desai** — Student ID: 202451051
2. **Neet Bhimani** — Student ID: 202451035
3. **Mrugen Bhalodiya** — Student ID: 202451031
4. **Keval Chorada** — Student ID: 202451089
5. **Svetal Barad** — Student ID: 202452311

---

## 1. Project Abstract
Operating systems isolate user-mode processes to maintain system stability, but this isolation means that unhandled faults in individual applications cause immediate process death. In server, desktop, and industrial automation environments, mission-critical worker processes, database relays, and background services require continuous availability.

**ResQ Web** is a complete, production-grade, web-based process monitoring and automated fault recovery platform for the Windows operating system. Unlike simulated academic dashboards, ResQ Web directly interfaces with the Windows NT kernel through Win32 executive handles, non-busy wait synchronization (`WaitForSingleObject`), exit code inspection (`GetExitCodeProcess`), and Windows Job Objects. A high-performance FastAPI backend coordinates with a Next.js 14 real-time dashboard to provide application registration, live telemetry, policy-driven exponential backoff recovery, circuit breaker loop prevention, and performance evaluation.

---

## 2. Introduction
Process supervision is a foundational concept in systems programming and operating systems design. Traditional operating systems provide the primitives to create, monitor, and signal processes, but user-space supervision engines (such as Unix `init`, `systemd`, or Erlang's OTP supervisor trees) are required to monitor process lifecycles and recover from unexpected termination. On Microsoft Windows, process management relies on kernel handles, synchronization objects, and Job Objects. ResQ Web translates these low-level OS mechanisms into an intuitive, accessible, and resilient full-stack architecture.

---

## 3. Problem Statement
Windows applications frequently terminate due to unhandled exceptions, memory exhaustion, segmentation faults, or external termination. Standard Windows desktop and server environments offer limited native mechanisms for user-mode applications to automatically restart with configurable cooldowns without writing custom Windows Services or complex scripts. Furthermore, existing monitoring tools either lack automated recovery, introduce heavy CPU overhead via busy polling, or do not offer a centralized web-based management interface.

---

## 4. Motivation
The primary motivation behind ResQ Web is to bridge the gap between theoretical Operating Systems concepts taught in academic curricula and practical user-mode systems programming on modern Windows operating systems. By implementing native handle management, asynchronous wait mechanisms, exponential backoff, and thread synchronization, the project demonstrates how core operating system concepts solve real-world software reliability challenges.

---

## 5. Objectives
1. Implement real user-mode Windows process creation, PID capture, and handle tracking.
2. Achieve event-driven process termination detection with 0% idle CPU overhead using `WaitForSingleObject`.
3. Capture real process exit codes to distinguish clean shutdowns from abnormal faults.
4. Implement a thread-safe deterministic state machine: `STOPPED`, `STARTING`, `RUNNING`, `STOPPING`, `RECOVERY_WAIT`, `FAILED`.
5. Implement configurable exponential backoff recovery with retry limit capping (circuit breaker) to prevent cascading restart storms.
6. Provide an enterprise-grade Next.js dashboard with live WebSocket telemetry, resource charts, audit logging, and process controls.
7. Empirically measure and document crash detection latency, recovery latency, and supervisor resource overhead.

---

## 6. Existing Systems and Limitations
| Feature | Windows Task Manager | Windows Service Manager (SCM) | PM2 / Supervisor | ResQ Web |
|---|---|---|---|---|
| **Platform** | Windows Native | Windows Services Only | Node.js / Linux focused | Windows Desktop & Server Apps |
| **Automatic Recovery** | ❌ No | ⚠️ Basic (3 restarts only) | ⚠️ Limited Win32 API access | ✅ Full Exponential Backoff |
| **Web Dashboard** | ❌ None | ❌ None | ⚠️ Third-party / CLI | ✅ Built-in Modern Next.js UI |
| **Descendant Process Cleanup**| ❌ No | ❌ No | ⚠️ Partial | ✅ Windows Job Objects |
| **Exit Code Diagnostics** | ❌ No | ⚠️ Event Viewer logs | ⚠️ Partial | ✅ Real-Time Live Capture |

---

## 7. Proposed System
ResQ Web implements a layered architecture:
- **Presentation Layer:** Next.js 14 App Router, TypeScript, Tailwind CSS, Lucide React, and TanStack Query.
- **API & Telemetry Layer:** FastAPI with REST endpoints, WebSocket event streaming, and SQLite persistence in WAL mode.
- **Process Supervisor Engine:** Dedicated Python process supervisor communicating directly with the Windows NT kernel using native Ctypes and `pywin32`.
- **Target Applications:** Actual Windows executables and background workers.

---

## 8. Functional Requirements
- **FR01 (Registration):** Authorize and register approved Windows executables with validation of path, arguments, and working directory.
- **FR02 (Launch & PID Capture):** Spawn approved executables as real Windows processes, capturing the true operating-system PID.
- **FR03 (Continuous Monitoring):** Sample real-time CPU percentage, physical RAM Working Set, active thread count, and OS handle count.
- **FR04 (Termination Detection):** Detect process exit within $\approx 150\text{ ms}$ using event-driven kernel wait handles.
- **FR05 (Exit Code Collection):** Extract the 32-bit exit code from the terminating process.
- **FR06 (Controlled Stop):** Provide operator-initiated graceful stop and suppress automatic recovery.
- **FR07 (Automatic Recovery):** Relaunch unexpectedly terminated processes using configurable exponential backoff delays.
- **FR08 (Circuit Breaker):** Cease automatic restarts and mark application as `FAILED` upon reaching maximum retry limit.
- **FR09 (Concurrency):** Monitor multiple applications concurrently without blocking or cross-application interference.
- **FR10 (Audit Logging):** Persist all lifecycle transitions, crashes, and recovery attempts with timestamps in a relational database.

---

## 9. Non-Functional Requirements
- **NFR01 (Zero Idle Overhead):** The supervisor must consume $0.0\%$ CPU during steady-state monitoring.
- **NFR02 (Low Memory Footprint):** Baseline supervisor memory must remain below $25\text{ MB RSS}$.
- **NFR03 (High Reliability):** The supervisor must never enter recursive crash loops or deadlock during simultaneous state transitions.
- **NFR04 (Security):** Arbitrary shell execution must be blocked by enforcing `shell=False`. Path traversal attempts must be rejected.
- **NFR05 (User Experience):** The web dashboard must be responsive, modern, dark-first, and update in real-time via WebSockets without page refreshes.

---

## 10. System Architecture
*(See detailed architectural specification and Mermaid diagrams in `docs/architecture/ARCHITECTURE.md`)*

---

## 11. Component Descriptions
- **`agent/process_manager/win32_api.py`:** Directly encapsulates native `kernel32.dll` system calls: `OpenProcess`, `CloseHandle`, `WaitForSingleObject`, `GetExitCodeProcess`, `TerminateProcess`, `CreateJobObjectW`, `AssignProcessToJobObject`.
- **`agent/monitoring/watcher_thread.py`:** Dedicated daemon thread per process performing non-busy kernel waits.
- **`agent/monitoring/termination_detector.py`:** Thread-safe classifier distinguishing user stops from unexpected crashes.
- **`agent/recovery/state_machine.py`:** Deterministic state machine validating allowed transitions.
- **`agent/recovery/policy_evaluator.py`:** Computes exponential backoff delays and enforces retry limits.
- **`backend/app/services/application_service.py`:** Coordinates database persistence with supervisor memory state.
- **`frontend/app/page.tsx`:** Overview dashboard with live KPIs and quick action controls.

---

## 12. Technology Stack
- **Frontend:** Next.js 14, React 18, TypeScript, Tailwind CSS, TanStack Query v5, Recharts, Sonner, Lucide React.
- **Backend:** Python 3.12/3.13, FastAPI, Pydantic v2, SQLAlchemy 2.0, Uvicorn, WebSockets.
- **Process Management:** Python `subprocess`, `psutil`, native Win32 APIs via `ctypes` and `pywin32`.
- **Database:** SQLite 3 in WAL mode (Write-Ahead Logging).
- **Packaging:** Docker, Docker Compose, Windows Batch Scripts, PowerShell.

---

## 13. Database Design
Entity relational models:
- **`Application`:** ID, Name, Executable Path, Arguments, Auto Recovery, Max Retries, Retry Delay, Status, Current PID, Consecutive Retries, Total Recoveries.
- **`ProcessRun`:** ID, App ID (FK), PID, Start Time, End Time, Duration, Exit Code, Termination Type.
- **`RecoveryAttempt`:** ID, App ID (FK), Attempt Number, Delay Seconds, Status, New PID.
- **`Event`:** ID, App ID, App Name, Event Type, Severity, Message, PID, Exit Code, Details, Timestamp.
- **`SystemMetric`:** ID, CPU %, Memory Used, Memory Total, Memory %, Managed Process Count, Timestamp.

---

## 14. API Documentation
*(See complete endpoint specifications in `docs/api/API_SPECIFICATION.md`)*

---

## 15. Operating Systems Concepts and Contributions
*(See comprehensive academic analysis in `docs/operating_systems/OS_CONCEPTS_AND_CONTRIBUTIONS.md`)*

---

## 16. Algorithms and State Transitions
### Exponential Backoff Algorithm:
$$\text{Delay}(n) = \min\left(\text{initial\_delay} \times \text{multiplier}^n, \text{max\_ceiling}\right)$$

### Validated State Machine Transitions:
- $\text{STOPPED} \rightarrow \text{STARTING}$
- $\text{STARTING} \rightarrow \text{RUNNING} \mid \text{FAILED} \mid \text{STOPPED}$
- $\text{RUNNING} \rightarrow \text{STOPPING} \mid \text{RECOVERY\_WAIT} \mid \text{FAILED} \mid \text{STOPPED}$
- $\text{STOPPING} \rightarrow \text{STOPPED} \mid \text{FAILED}$
- $\text{RECOVERY\_WAIT} \rightarrow \text{STARTING} \mid \text{STOPPING} \mid \text{STOPPED} \mid \text{FAILED}$
- $\text{FAILED} \rightarrow \text{STARTING} \mid \text{STOPPED}$

---

## 17. Security Considerations
- **No Arbitrary Shell Execution:** `subprocess.Popen(..., shell=False)` prevents command concatenation injections.
- **Path Sanitization:** Paths are canonicalized using `os.path.abspath` to block directory traversal attacks (`..`).
- **Localhost Restricted:** Backend and WebSocket services strictly bind to `127.0.0.1`.
- **Least Privilege:** Does not require Administrator elevation; operates cleanly within standard user permissions.

---

## 18. Implementation Details
The project is structured as a modular monorepo:
- `backend/`: FastAPI application, database models, schemas, and routes.
- `agent/`: Local Windows process supervisor, Win32 API interfaces, and recovery orchestrators.
- `frontend/`: Next.js 14 App Router dashboard with responsive Tailwind CSS.
- `test_apps/`: Authentic test applications for live OS demonstration (`worker_app.py`, `crasher_app.py`, `child_spawner.py`).
- `scripts/`: Automated launch and benchmarking scripts.

---

## 19. Testing Methodology
Testing was conducted across unit, integration, and empirical performance levels:
- **Unit Testing:** Python `unittest` test suites verifying path validation, state machine transitions, and backoff calculations.
- **Integration Testing:** API route tests verifying application lifecycle, persistence, and error handling.
- **Live OS Verification:** Empirical testing using real Windows binaries to verify PIDs, crash detection, exit codes, and automatic relaunch.

---

## 20. Test Cases and Actual Results
*(All 25 test cases T01 through T25 passed with 100% success rate. See `docs/testing/TEST_AND_EVALUATION_REPORT.md`)*

---

## 21. Performance Evaluation
Empirical benchmark measurements collected on Windows 11:
- **Average Crash Detection Latency:** $145.0\text{ ms}$
- **Average Recovery Relaunch Time:** $48.0\text{ ms}$
- **Recovery Success Rate:** $100.0\%$
- **False Recovery Rate:** $0.0\%$
- **Supervisor Baseline RAM:** $22.60\text{ MB RSS}$
- **Supervisor 5-App Load RAM:** $23.07\text{ MB RSS}$
- **Supervisor CPU Overhead:** $0.0\%$

---

## 22. User Experience & Dashboard Walkthrough
The web interface features 8 major functional sections:
1. **Overview Dashboard:** Summary cards, CPU/RAM gauges, active applications, recent event stream.
2. **Applications Management:** Searchable, filterable table with inline lifecycle actions (Launch, Stop, Restart, Delete).
3. **Application Details:** Telemetry deep dive with live PID, uptime, process CPU/RAM, thread count, handle count, and run history.
4. **Recovery Policies:** Policy configuration, interactive backoff simulator, and recovery attempt logs.
5. **Event History:** Comprehensive audit trail with severity filtering and JSON export.
6. **System Monitoring:** Time-series area charts for host CPU and physical RAM with per-process resource breakdowns.
7. **Analytics:** MTTR, crash detection latency, and reliability metrics.
8. **Settings & Team:** System health indicators, security boundaries, and academic team credits.

---

## 23. Limitations
1. **User Mode Boundary:** ResQ Web operates in user space (Ring 3) and cannot supervise Ring 0 kernel device drivers.
2. **Platform Specificity:** Low-level process handles, `WaitForSingleObject`, and Job Objects are specific to Windows NT.
3. **Protected Processes:** Cannot terminate processes owned by other users or the Windows kernel without administrative privileges.

---

## 24. Future Enhancements
1. **Windows Service Wrapping:** Package the supervisor as a native background Windows Service (`services.msc`).
2. **Custom Alert Webhooks:** Email, Slack, or Discord webhook alerts upon critical circuit breaker trips.
3. **Memory Threshold Triggers:** Automatic graceful restart if a process exceeds a configurable memory ceiling.
4. **Linux Portability:** Provide a POSIX-compliant backend using `kqueue`/`epoll` and `waitpid` for cross-platform supervision.

---

## 25. Conclusion
ResQ Web successfully delivers a reliable, production-oriented process monitoring and automatic recovery system for Windows. By directly exercising Windows NT kernel handles, non-busy wait mechanisms, Job Objects, and exponential backoff recovery, the project provides an academically sound, demonstrable, and empirically evaluated implementation of core Operating Systems principles.

---

## 26. References
1. Silberschatz, A., Galvin, P. B., & Gagne, G. *Operating System Concepts* (10th ed.). Wiley, 2018.
2. Russinovich, M., Solomon, D. A., & Ionescu, A. *Windows Internals, Part 1: System architecture, processes, threads, memory management, and more* (7th ed.). Microsoft Press, 2017.
3. Hart, J. M. *Windows System Programming* (4th ed.). Addison-Wesley Professional, 2010.
4. Microsoft Corporation. *Process and Thread Functions (Windows)*. Microsoft Learn Documentation, 2024.
5. Tanenbaum, A. S., & Bos, H. *Modern Operating Systems* (4th ed.). Pearson, 2015.

