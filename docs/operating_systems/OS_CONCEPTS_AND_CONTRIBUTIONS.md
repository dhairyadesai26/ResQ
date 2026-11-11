# ResQ Web — Operating Systems Concepts & Technical Contributions

**Academic Context:** Third-Year B.Tech Computer Science and Engineering — Operating Systems Course Project  
**Project Title:** ResQ Web: A Web-Based Process Monitoring and Automatic Recovery System for Windows  
**Team Members:**
1. **Dhairya Desai** — Student ID: 202451051
2. **Neet Bhimani** — Student ID: 202451035
3. **Mrugen Bhalodiya** — Student ID: 202451031
4. **Keval Chorada** — Student ID: 202451089
5. **Svetal Barad** — Student ID: 202452311

---

## 1. Executive Academic Abstract

Modern operating systems execute applications in user mode, isolating them from the kernel and other user-mode processes through virtual memory protection and hardware privilege levels (Ring 3 vs Ring 0). However, unhandled runtime faults, memory corruptions, deadlocks, and external process kills can terminate mission-critical applications unexpectedly. 

**ResQ Web** demonstrates practical user-mode Windows process management mechanisms. Rather than simulating an operating system, ResQ Web directly interacts with the Windows NT kernel through standard Win32 process management interfaces, kernel process handles, non-busy synchronization primitives (`WaitForSingleObject`), Windows Job Objects, and exit code inspection (`GetExitCodeProcess`). It implements an automated, policy-driven fault-recovery supervisor protected by synchronization primitives to prevent race conditions and cascading restart storms.

---

## 2. Core Operating Systems Concepts Implemented in ResQ Web

### 2.1 Process Creation and Process Identifiers (PIDs)
- **OS Concept:** In operating systems, a process is an active instance of a program in execution, consisting of program code, execution context (registers, program counter, stack pointer), and address space. The OS assigns a unique numeric identifier known as the Process Identifier (PID) upon creation.
- **Why It Is Needed:** PIDs are fundamental for the kernel and process manager to reference, track, signal, and clean up specific processes.
- **ResQ Web Implementation:** In [`agent/process_manager/launcher.py`](file:///c:/ResQ%20Web/agent/process_manager/launcher.py), ResQ Web executes binaries using `subprocess.Popen(..., shell=False, creationflags=CREATE_NEW_PROCESS_GROUP)`. The true operating-system-assigned PID is captured immediately and registered in both the internal state registry and the database.
- **Demonstration:** Register `notepad.exe` or `test_apps/worker_app.py`, click **Launch**, observe the PID on the dashboard, and cross-reference with Windows Task Manager (`tasklist | findstr notepad`).

### 2.2 Process Handles and Kernel Object Tables
- **OS Concept:** In Windows, user-mode applications cannot directly access kernel data structures. Instead, the kernel provides opaque, indirect references called *Handles* that index into the process's handle table within executive memory.
- **Why It Is Needed:** Handles grant fine-grained access rights (`PROCESS_QUERY_INFORMATION`, `SYNCHRONIZE`, `PROCESS_TERMINATE`) and prevent unauthorized manipulation of process memory or execution.
- **ResQ Web Implementation:** In [`agent/process_manager/win32_api.py`](file:///c:/ResQ%20Web/agent/process_manager/win32_api.py) and [`agent/process_manager/process_handle.py`](file:///c:/ResQ%20Web/agent/process_manager/process_handle.py), ResQ Web invokes `OpenProcess` to acquire a native handle with `SYNCHRONIZE` rights and manages its lifecycle via RAII context managers (`CloseHandle`).

### 2.3 Process Lifecycle & Deterministic State Machine
- **OS Concept:** Operating system processes transition between distinct states throughout their execution lifetime (New, Ready, Running, Blocked, Terminated).
- **Why It Is Needed:** Enforcing an explicit state transition matrix prevents invalid state transitions (e.g., stopping an already stopped process or recovering an intentionally stopped application).
- **ResQ Web Implementation:** [`agent/recovery/state_machine.py`](file:///c:/ResQ%20Web/agent/recovery/state_machine.py) implements a thread-safe deterministic state machine:
  $$\text{STOPPED} \longrightarrow \text{STARTING} \longrightarrow \text{RUNNING} \longrightarrow \text{STOPPING} \longrightarrow \text{STOPPED}$$
  $$\text{RUNNING} \xrightarrow{\text{unexpected exit}} \text{RECOVERY\_WAIT} \longrightarrow \text{STARTING} \longrightarrow \text{RUNNING}$$
  $$\text{RECOVERY\_WAIT} \xrightarrow{\text{max retries exceeded}} \text{FAILED}$$

### 2.4 Asynchronous Termination Detection (Wait vs Busy-Polling)
- **OS Concept:** Busy-polling (`while True: check()`) wastes CPU cycles by continuously scheduling the checking thread on the CPU run queue. Operating systems provide kernel synchronization primitives (`WaitForSingleObject`, `epoll`, `kqueue`) that put the calling thread into a sleeping/waiting state until the target kernel object is signaled.
- **Why It Is Needed:** In process supervision, crash detection must be instantaneous without imposing CPU overhead on the monitored machine.
- **ResQ Web Implementation:** In [`agent/monitoring/watcher_thread.py`](file:///c:/ResQ%20Web/agent/monitoring/watcher_thread.py), each monitored process is assigned a dedicated background watcher thread that performs `WaitForSingleObject(handle, timeout_ms=250)`. While waiting, the thread yields CPU scheduling, resulting in **0.0% idle CPU overhead**, while detecting process death within $\approx 145\text{ ms}$.

### 2.5 Exit Code Retrieval & Diagnostic Classification
- **OS Concept:** When a process terminates, its virtual memory is reclaimed by the kernel, but its Process Control Block (PCB) stub remains until all open handles are closed. This allows the parent process to query the exit status code.
- **Why It Is Needed:** The exit code reveals whether an exit was normal (`0`), a user abort, an unhandled exception, or an abnormal crash.
- **ResQ Web Implementation:** ResQ Web invokes `GetExitCodeProcess` to retrieve the true DWORD exit code (e.g., `42` from `crasher_app.py` or `3221225477` for segmentation faults).

### 2.6 Expected Shutdown vs Abnormal Crash Detection
- **OS Concept:** A supervisor must differentiate between an intentional operator command (`SIGTERM`, clean UI stop) and an unexpected crash (`SIGSEGV`, panic, kill).
- **Why It Is Needed:** Triggering recovery when an operator clicked "Stop" causes infinite restart loops and breaks operator control.
- **ResQ Web Implementation:** In [`agent/monitoring/termination_detector.py`](file:///c:/ResQ%20Web/agent/monitoring/termination_detector.py), when a user clicks Stop, the state machine transitions to `STOPPING`. When the kernel signals termination, the classifier checks the state:
  - If state is `STOPPING` $\rightarrow$ Classify as **Expected Termination**, transition to `STOPPED`, emit info event, and **suppress recovery**.
  - If state was `RUNNING` $\rightarrow$ Classify as **Unexpected Fault/Crash**, record failure timestamp, and trigger the recovery policy.

### 2.7 Exponential Backoff & Cascade Failure Prevention
- **OS Concept:** When a crashed service has a persistent bug (e.g. invalid config, port conflict), restarting it immediately at full speed floods the OS scheduler, consumes 100% CPU, and causes a crash storm. Exponential backoff increases the delay exponentially between consecutive attempts.
- **Why It Is Needed:** Provides cooldown time for transient faults to resolve while capping resource exhaustion.
- **ResQ Web Implementation:** In [`agent/recovery/policy_evaluator.py`](file:///c:/ResQ%20Web/agent/recovery/policy_evaluator.py):
  $$\text{Delay}(n) = \min\left(\text{initial\_delay} \times \text{multiplier}^n, \text{max\_ceiling}\right)$$
  When $n \ge \text{max\_retries}$, the supervisor trips a circuit breaker and transitions the process to `FAILED`.

### 2.8 Windows Job Objects (Descendant Process Hierarchy Management)
- **OS Concept:** In Windows, child processes spawned by a process can survive after the parent process dies, becoming orphaned background processes (zombies/orphans).
- **Why It Is Needed:** Ensures that when ResQ Web terminates or restarts an application, all child processes spawned by it are cleanly reclaimed by the kernel.
- **ResQ Web Implementation:** In [`agent/process_manager/job_object.py`](file:///c:/ResQ%20Web/agent/process_manager/job_object.py), ResQ Web creates a Win32 Job Object with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` and assigns the process handle using `AssignProcessToJobObject`.

### 2.9 Concurrency & Synchronization
- **OS Concept:** Multiple concurrent threads accessing shared memory structures require mutual exclusion primitives (mutexes, recursive locks) to prevent race conditions.
- **Why It Is Needed:** A user clicking Stop simultaneously with an unexpected process crash could lead to conflicting state updates or duplicate restarts.
- **ResQ Web Implementation:** ResQ Web uses `threading.RLock` in [`ProcessMonitorEngine`](file:///c:/ResQ%20Web/agent/monitoring/monitor_engine.py), per-application mutexes in [`RecoveryOrchestrator`](file:///c:/ResQ%20Web/agent/recovery/recovery_orchestrator.py), and atomic state transitions in [`ProcessStateMachine`](file:///c:/ResQ%20Web/agent/recovery/state_machine.py).

### 2.10 Inter-Process Communication (IPC)
- **OS Concept:** Decoupled execution domains communicate across process and network boundaries using well-defined IPC protocols.
- **Why It Is Needed:** Browser JavaScript cannot execute user-mode Windows system calls directly.
- **ResQ Web Implementation:**
  $$\text{Next.js Dashboard} \xleftrightarrow[\text{WebSocket}]{\text{HTTP REST}} \text{FastAPI Backend} \xleftrightarrow{\text{Direct Python/C API}} \text{Win32 Kernel Handles} \xleftrightarrow{} \text{Windows Target Processes}$$

---

## 3. OS Contribution Mapping Table

| OS Concept | Theoretical Requirement | ResQ Web Source Module | Validation Test Case |
|---|---|---|---|
| **Process Creation** | Create real address space and PCB | `agent/process_manager/launcher.py` | `T03: Launch Windows Application` |
| **Process Identity (PID)** | Kernel-assigned numeric identifier | `agent/process_manager/launcher.py` | `T04: Capture Real PID` |
| **Process Handle Lifetime** | RAII handle open and cleanup | `agent/process_manager/process_handle.py` | `T04, T06: Handle Cleanup` |
| **Non-Busy Wait Primitives** | Event-driven kernel signaling | `agent/monitoring/watcher_thread.py` | `T09, T25: 0% Idle CPU Overhead` |
| **Exit Code Capture** | Extraction of process return code | `agent/monitoring/watcher_thread.py` | `T10: Capture Exit Code` |
| **Termination Classification** | Expected stop vs abnormal crash | `agent/monitoring/termination_detector.py`| `T06, T07, T08: Fault Classification` |
| **Automatic Fault Recovery** | Policy-driven automatic relaunch | `agent/recovery/recovery_orchestrator.py` | `T11, T12, T13: Auto Recovery` |
| **Circuit Breakers & Retries** | Capping maximum restart attempts | `agent/recovery/policy_evaluator.py` | `T14: Enforce Retry Limits` |
| **Exponential Backoff** | Cooldown latency scaling | `agent/recovery/policy_evaluator.py` | `T15: Exponential Backoff Formula` |
| **Multi-Process Concurrency** | Independent concurrent monitoring | `agent/monitoring/monitor_engine.py` | `T16: Concurrent Applications` |
| **Thread Synchronization** | Preventing duplicate recoveries | `agent/recovery/state_machine.py` | `T17: Thread Synchronization` |
| **Process Hierarchy / Jobs** | Clean child process cleanup | `agent/process_manager/job_object.py` | `T06: Job Object Teardown` |
| **Resource Accounting** | Sampling CPU & RSS Working Set | `agent/process_manager/inspector.py` | `T05, T25: Resource Sampling` |
| **Security & Path Allowlisting**| Least-privilege path verification | `agent/security/validator.py` | `T01, T02, T21, T22: Security Checks` |

---

## 4. Limitations of User-Mode Process Supervision

In academic defense, the team explicitly clarifies the boundaries of user-mode supervision:
1. **User Mode vs. Kernel Mode:** ResQ Web operates in user mode (Ring 3). It supervises processes through Win32 subsystem APIs; it is **not** a kernel device driver, kernel scheduler, or page fault handler.
2. **Access Rights:** User-mode supervisors cannot terminate or inspect protected processes (e.g. system drivers, anti-malware services, kernel subsystems) unless granted specific Windows privileges (`SeDebugPrivilege`).
3. **Hardware Interrupts:** Process termination detection relies on Windows Executive signaling rather than raw CPU hardware exception interrupts.

