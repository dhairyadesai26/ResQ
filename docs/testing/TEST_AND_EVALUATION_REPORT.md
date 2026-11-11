# ResQ Web — Formal Testing & Performance Evaluation Report

**Academic Context:** Third-Year B.Tech CSE Operating Systems Course Project  
**Report Date:** 2026-11-05  
**Team Members:**
1. **Dhairya Desai** — 202451051
2. **Neet Bhimani** — 202451035
3. **Mrugen Bhalodiya** — 202451031
4. **Keval Chorada** — 202451089
5. **Svetal Barad** — 202452311

---

## 1. Quality Assurance & Verification Summary

All 25 mandated Operating Systems test cases (T01 through T25) were developed, executed on actual Windows processes, and formally verified. No simulated data or mock operations were used.

```
Total Test Cases:       25
Passed:                 25
Failed:                 0
Success Rate:           100.0%
Execution Environment:  Windows 11 (64-bit), Python 3.13, Next.js 14
```

---

## 2. Comprehensive Test Matrix (T01 — T25)

| Test ID | Objective | Test Procedure | Expected Outcome | Actual Result | Status |
|---|---|---|---|---|---|
| **T01** | Register valid executable | Submit path to valid Windows binary or script | Path canonicalized and accepted into supervisor registry | Validated via `ProcessSecurityValidator.sanitize_path` | **PASS** |
| **T02** | Reject invalid executable path | Attempt to register non-existent path `C:\fake_xyz.exe` | System raises `SecurityValidationError` / HTTP 400 | Rejection confirmed with 400 Bad Request | **PASS** |
| **T03** | Launch actual Windows application | Operator clicks Launch via UI / API | Operating system creates new address space and process | Windows process spawned successfully | **PASS** |
| **T04** | Capture real PID | Inspect returned process descriptor | True kernel-assigned PID captured and stored | Real PID captured and verified with `tasklist` | **PASS** |
| **T05** | Display current running state | Query application status via API / WebSocket | State is `RUNNING`, uptime $> 0$, memory and CPU populated | State correctly displayed as `RUNNING` with live metrics | **PASS** |
| **T06** | Request controlled stop | User clicks Stop button | State transitions to `STOPPING`, graceful stop signal sent | Process stopped cleanly | **PASS** |
| **T07** | Controlled stop suppresses recovery | Inspect post-stop supervisor events | State transitions to `STOPPED`; recovery is **NOT** triggered | Verified: `consecutive_retries` remains 0; no relaunch | **PASS** |
| **T08** | Unexpected process termination | Execute crasher app (`--crash-after 1.2 --exit-code 42`) | Process terminates abruptly without prior stop signal | Fault injection triggered | **PASS** |
| **T09** | Detect termination | Watcher thread awaits process handle | `WaitForSingleObject` transitions to signaled state within 145ms | Termination detected immediately | **PASS** |
| **T10** | Capture exit code | Query exit code via `GetExitCodeProcess` | True exit code `42` extracted from Windows kernel | Exit code `42` captured and recorded | **PASS** |
| **T11** | Trigger automatic recovery | Evaluate recovery policy after unexpected crash | State machine transitions to `RECOVERY_WAIT` | Backoff timer scheduled and executed | **PASS** |
| **T12** | Verify new process starts | Await completion of recovery backoff delay | New process created by supervisor launcher | Process relaunched successfully | **PASS** |
| **T13** | Verify new PID differs | Compare pre-crash PID with post-recovery PID | New PID $\ne$ Original PID | Original PID `25752` $\rightarrow$ New PID `29828` | **PASS** |
| **T14** | Enforce retry limits | Repeat crashes until max retries reached | Recovery stops; state transitions to `FAILED` | Circuit breaker tripped; state marked `FAILED` | **PASS** |
| **T15** | Exponential backoff calculation | Verify sequence $1.0\text{s} \times 2.0^n$ capped at max delay | Delays: 1.0s, 2.0s, 4.0s, 8.0s, capped at max delay (10.0s) | Backoff delays calculated accurately | **PASS** |
| **T16** | Concurrent applications | Supervise multiple applications simultaneously | Independent threads manage each application without interference | Two concurrent apps monitored with distinct PIDs | **PASS** |
| **T17** | Concurrent recovery synchronization | Inject simultaneous crashes across applications | Mutex locks prevent race conditions and duplicate recoveries | Clean, isolated recovery on both applications | **PASS** |
| **T18** | Backend disconnection handling | Disconnect frontend from backend API | UI displays "Disconnected" indicator; reconnects upon restore | WebSocket client auto-reconnects with exponential backoff | **PASS** |
| **T19** | Agent disconnection handling | Stop process supervisor while UI is active | UI indicates supervisor offline and provides status | Handled cleanly; state updates resume on reconnect | **PASS** |
| **T20** | Database persistence across restart | Stop backend, restart server, inspect database | Registered applications and event logs persist in SQLite | SQLite in WAL mode successfully reloads all apps | **PASS** |
| **T21** | Malformed requests rejection | Submit malformed JSON payload (missing required fields) | Pydantic schema validation rejects with HTTP 422 | Rejected with HTTP 422 Unprocessable Entity | **PASS** |
| **T22** | Inaccessible paths rejection | Submit directory without executable permissions | System raises `SecurityValidationError` | Rejected with informative validation error | **PASS** |
| **T23** | Dashboard responsiveness | Test layout across viewport widths (Desktop, Laptop, Tablet) | UI adapts via Tailwind CSS responsive grid | Responsive layouts verified across viewports | **PASS** |
| **T24** | WebSocket reconnection | Drop WebSocket connection and restore | Client automatically triggers reconnect timer and resumes stream | Verified via `wsClient` heartbeat and reconnect loop | **PASS** |
| **T25** | System resource overhead | Measure supervisor CPU % and RAM under active monitoring | Idle CPU $\approx 0.0\%$, RAM $< 25\text{ MB}$ | Measured: **0.0% CPU**, **22.6 MB Baseline RAM**, **23.07 MB under 5 apps** | **PASS** |

---

## 3. Empirical Operating Systems Benchmark Results

The following metrics were measured empirically on Windows 11 using `scripts/benchmark_performance.py`:

```json
{
  "platform": "Windows 11 (64-bit)",
  "metrics": {
    "average_crash_detection_latency_ms": 145.0,
    "average_recovery_latency_ms": 48.0,
    "recovery_success_rate_percent": 100.0,
    "false_recovery_rate_percent": 0.0,
    "supervisor_baseline_rss_mb": 22.60,
    "supervisor_loaded_rss_mb": 23.07,
    "supervisor_cpu_overhead_percent": 0.0,
    "concurrency_tested_processes": 5
  }
}
```

### Analysis of Empirical Results:
1. **Crash Detection Latency (145.0 ms):** The latency is determined by the 250ms wait slice in `WaitForSingleObject`. When a process crashes, the kernel transitions the process handle to the signaled state, waking up the watcher thread on its next wake slice with an average latency of 145ms.
2. **Recovery Relaunch Latency (48.0 ms):** Once the backoff cooldown expires, creating the new Windows process, allocating its virtual address space, and acquiring the native handle takes just 48 milliseconds.
3. **Supervisor Overhead (0.0% CPU, 23.07 MB RAM):** By avoiding busy loops and using event-driven kernel wait handles, the supervisor consumes 0.0% CPU during steady-state monitoring.

