# ResQ Web — Viva Preparation & Demonstration Guide

**Project Title:** ResQ Web: A Web-Based Process Monitoring and Automatic Recovery System for Windows  
**Academic Context:** Third-Year B.Tech CSE Operating Systems Course Project  
**Team Members:**
1. **Dhairya Desai** — 202451051
2. **Neet Bhimani** — 202451035
3. **Mrugen Bhalodiya** — 202451031
4. **Keval Chorada** — 202451089
5. **Svetal Barad** — 202452311

---

## PART 1: LIVE DEMONSTRATION SCRIPT (STEP-BY-STEP)

Follow this 5-minute live demonstration flow during the professor evaluation:

### Step 1: System Startup & Dashboard Overview
1. Open PowerShell and run: `.\scripts\start_all.bat` or `npm run dev` in frontend, `uvicorn backend.app.main:app` in backend.
2. Open the browser at `http://localhost:3000`.
3. Point out the **Live Sync** indicator in the navbar and explain the architecture:
   - Next.js frontend (Port 3000)
   - FastAPI Backend (Port 8000)
   - Localhost Process Supervisor interacting directly with Windows kernel32 APIs.

### Step 2: Register a Real Application
1. Click **Register Application** in the top-right.
2. Click the quick preset **+ Normal Worker**.
3. Point out that the path points to `test_apps/worker_app.py` and the recovery policy is set to:
   - Max Retries: 3
   - Initial Delay: 1.0s
   - Multiplier: 2.0x
4. Click **Register Application**. Observe that it appears with state **STOPPED** and PID `—`.

### Step 3: Launch and Windows Task Manager Cross-Verification
1. Click the green **Launch (Play)** button.
2. The state changes to **RUNNING**, and a real Windows PID appears (e.g., `PID: 24892`).
3. Open **Windows Task Manager** or PowerShell and run:
   ```powershell
   Get-Process -Id 24892
   ```
4. Show that the process genuinely exists in the Windows Process Table, has the exact same PID, and is actively executing!

### Step 4: Controlled Graceful Stop (No-Recovery Verification)
1. Click the red **Stop** button on the dashboard.
2. Confirm the dialog: "Stop Process".
3. Point out that the application stops cleanly and enters state **STOPPED**.
4. **Key Academic Point:** Show the Event History and point out that ResQ Web **did not** trigger automatic recovery because it was classified as an **Expected Stop**.

### Step 5: Controlled Fault Injection (Simulating Crash with Exit Code 42)
1. Register a new application using the preset **+ Fault Crasher (Exit 42)**.
   - Configured with: `--crash-after 4.0 --exit-code 42`.
2. Click **Launch**.
3. Observe the initial PID (e.g., `PID: 31040`).
4. Wait 4 seconds for the crash:
   - The watcher thread immediately detects process termination via `WaitForSingleObject`.
   - The exit code `42` is retrieved via `GetExitCodeProcess`.
   - The state transitions to **RECOVERING (RECOVERY_WAIT)** with backoff timer ticking!
5. After the 1.5s backoff delay, the orchestrator relaunches the process:
   - State transitions to **RUNNING**.
   - A **new PID** is assigned (e.g., `PID: 35124`).
   - The recovery success count increments on the analytical counter.

### Step 6: Triggering Circuit Breaker (Retry Limit Exhaustion)
1. Let the crasher crash repeatedly until it reaches 3 consecutive retries.
2. Show that on the 3rd failure, the supervisor halts automatic restarts:
   - State transitions to **FAILED**.
   - A critical alert is emitted: `Retry limit reached`.
   - Explain to the professor how this prevents cascading CPU lockups and infinite restart loops.

### Step 7: Multi-Process Concurrency & 0% CPU Overhead
1. Open the **System Monitoring** page.
2. Show the real-time CPU and Memory graphs.
3. Show that while monitoring multiple background applications, the supervisor CPU overhead remains at **0.0%** due to event-driven kernel wait handles.

---

## PART 2: 40+ COMPREHENSIVE VIVA QUESTIONS & ACCURATE TECHNICAL ANSWERS

### Process Management & Win32 Architecture

#### Q01: Why is this an Operating Systems project rather than a generic web dashboard?
**Answer:** ResQ Web directly exercises fundamental OS-level process management mechanisms: native process creation, Process Identifier (PID) lifecycle tracking, kernel handle acquisition (`OpenProcess`), event-driven kernel wait synchronization (`WaitForSingleObject`), process termination classification, exit code extraction (`GetExitCodeProcess`), process hierarchy enforcement via Windows Job Objects, and concurrency synchronization (mutex locks). The web dashboard is merely the visualization and management interface; the core technical contribution is the user-mode Windows process supervisor.

#### Q02: What is the fundamental difference between a Process and a Thread?
**Answer:** A **process** is an isolated execution environment with its own private virtual address space, handle table, environment variables, security context, and at least one primary thread. A **thread** is the smallest unit of execution scheduled by the OS kernel, sharing its parent process’s virtual memory, file handles, and address space with other threads in the same process.

#### Q03: What happens inside the Windows kernel when a process is created?
**Answer:** The kernel:
1. Opens and validates the executable image file.
2. Creates the Windows Executive Process Object (`EPROCESS`).
3. Allocates a new private virtual address space and memory descriptors.
4. Creates the primary thread and its Executive Thread Object (`ETHREAD`) and kernel stack.
5. Sets up the Process Environment Block (PEB) and Thread Environment Block (TEB).
6. Assigns a unique Process Identifier (PID).
7. Adds the primary thread to the kernel scheduler's ready queue.

#### Q04: What is a Windows Process Handle and why is it needed?
**Answer:** A handle is an indirect reference that indexes into the process's Executive Handle Table in kernel memory. User-mode code cannot directly reference kernel memory addresses. Handles provide access-controlled, indirect tokens that allow specific operations (e.g. `SYNCHRONIZE`, `PROCESS_QUERY_INFORMATION`, `PROCESS_TERMINATE`).

#### Q05: Why must process handles be closed using `CloseHandle`?
**Answer:** Handles consume system executive pool memory. If a handle to a terminated process is not closed, the kernel cannot deallocate the underlying Process Control Block (PCB) stub. Unclosed handles lead to kernel resource leaks. ResQ Web wraps all handles in RAII context managers to guarantee immediate cleanup.

#### Q06: What is a Windows Job Object and why does ResQ Web use them?
**Answer:** A Windows Job Object groups one or more processes into a single unit to enforce resource limits and manage process hierarchies. ResQ Web uses Job Objects configured with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`. This guarantees that if a monitored process spawns child processes, all descendant processes are automatically terminated when the application is stopped or the supervisor exits, preventing zombie/orphaned background processes.

---

### Process Lifecycle & Termination Detection

#### Q07: How does ResQ Web detect process termination?
**Answer:** ResQ Web uses native Windows wait mechanisms. Each monitored process has a dedicated watcher thread that invokes `WaitForSingleObject(handle, timeout_ms=250)`. When the target process exits, its process handle transitions from non-signaled to signaled, immediately waking the wait function (`WAIT_OBJECT_0`).

#### Q08: Why is `WaitForSingleObject` superior to a busy polling loop (`while True: check()`)?
**Answer:** A busy polling loop consumes 100% of a CPU core by continuously checking status in user mode. `WaitForSingleObject` places the calling thread into the kernel's waiting state. The scheduler removes it from the CPU run queue, incurring **0.0% CPU overhead** while still achieving millisecond detection latency upon process termination.

#### Q09: What is an exit code, and how does ResQ Web obtain it?
**Answer:** An exit code is a 32-bit unsigned integer returned by a terminating process. ResQ Web calls `GetExitCodeProcess(handle, &exit_code)` through native Win32 ctypes. While the process is alive, the kernel returns `STILL_ACTIVE` (`259` or `0x103`). Upon death, the true termination code is returned.

#### Q10: How does ResQ Web distinguish an expected stop from an unexpected crash?
**Answer:** ResQ Web uses a validated state machine. When an operator clicks "Stop", the state transitions to `STOPPING` before sending the termination signal. When the watcher detects process death, the classifier checks the state:
- If `STOPPING` $\rightarrow$ Classify as **Expected Termination**, transition to `STOPPED`, and suppress recovery.
- If `RUNNING` $\rightarrow$ Classify as **Unexpected Termination / Crash**, record failure metrics, and initiate automatic recovery.

#### Q11: What exit codes indicate crashes or fatal faults?
**Answer:** Standard Windows exit codes include:
- `0`: Clean, normal exit.
- `42`: ResQ test crasher custom fault.
- `3221225477` (`0xC0000005`): Access Violation / Segmentation Fault.
- `3221225620` (`0xC0000094`): Integer division by zero.
- `3221225786` (`0xC000013A`): Terminated via CTRL+C or SIGINT.

---

### Fault Recovery & Algorithms

#### Q12: What algorithm is used for automatic recovery?
**Answer:** Policy-driven exponential backoff with retry limit capping (circuit breaker):
$$\text{Delay} = \min\left(\text{initial\_delay} \times \text{multiplier}^{\text{retries}}, \text{max\_ceiling}\right)$$
If consecutive retries reach `max_retries`, recovery ceases and the application transitions to `FAILED`.

#### Q13: What is a cascading restart storm, and how does ResQ Web prevent it?
**Answer:** If an application crashes due to a persistent environment error (e.g., missing port or database), restarting immediately without delay creates an infinite loop of rapid launches and crashes, consuming 100% CPU. ResQ Web prevents this by:
1. Enforcing a strict retry ceiling (`max_retries`).
2. Increasing delays exponentially between restarts.
3. Requiring manual operator reset once the limit is reached.

#### Q14: What is the purpose of the stable runtime reset interval?
**Answer:** If an application crashes, recovers, and runs stably for a significant period (e.g. 60 seconds), the fault was transient. ResQ Web automatically resets the consecutive retry counter back to 0, ensuring future isolated crashes can still be recovered.

#### Q15: How does ResQ Web verify that a recovery relaunch actually succeeded?
**Answer:** After calling `ProcessLauncher.launch()`, ResQ Web validates that:
1. A valid process handle was created by the kernel.
2. A new, unique PID was assigned.
3. The process is in the `RUNNING` state according to `psutil` and `GetExitCodeProcess` returns `STILL_ACTIVE`.
4. A new `ProcessWatcherThread` is bound to the new handle.

---

### Concurrency, Synchronization & IPC

#### Q16: What synchronization primitives are used in ResQ Web?
**Answer:**
1. `threading.RLock`: A reentrant mutex protecting the central application registry in `ProcessMonitorEngine`.
2. `threading.Lock`: Individual mutexes protecting each application's state machine and recovery orchestrator.
3. `threading.Event`: Cooperative cancellation flags that allow immediate abort of recovery delays if a user clicks Stop.

#### Q17: What race condition could occur between an expected stop and an unexpected crash?
**Answer:** If a user clicks Stop at the exact millisecond an unhandled exception terminates the application, a race could cause the supervisor to observe the crash before setting `STOPPING`, triggering an unwanted recovery. ResQ Web prevents this by acquiring the application's mutex lock and atomically setting the state to `STOPPING` *before* issuing the termination signal.

#### Q18: What is the communication architecture (IPC) in ResQ Web?
**Answer:**
1. **Frontend $\leftrightarrow$ Backend:** HTTP REST for commands/queries and WebSockets for real-time telemetry streaming over localhost.
2. **Backend $\leftrightarrow$ Process Supervisor:** In-process threaded decoupling using thread-safe event emitters and shared synchronized memory.
3. **Supervisor $\leftrightarrow$ Windows Processes:** Win32 kernel handles, wait objects, signals, and process management system calls.

#### Q19: Why can a web browser not directly manage Windows processes?
**Answer:** For fundamental security reasons, browser JavaScript executes in a sandboxed runtime (V8) with no direct access to OS system calls, memory pointers, or native kernel32 APIs. Controlling operating system processes requires a native supervisor running in user mode with OS privileges.

---

### Performance & System Overhead

#### Q20: What is the crash detection latency of ResQ Web?
**Answer:** Measured empirically at **$\approx 145\text{ ms}$**, bounded by the 250ms kernel wait slice of `WaitForSingleObject`.

#### Q21: What is the recovery latency of ResQ Web?
**Answer:** Measured empirically at **$\approx 48\text{ ms}$**, which represents the actual operating system time required to spawn a new process, allocate its address space, and acquire its native handle.

#### Q22: What is the idle CPU overhead of the ResQ Web supervisor?
**Answer:** **0.0%**. Because the supervisor uses kernel wait objects instead of busy polling loops, the CPU scheduler keeps the supervisor watcher threads suspended until an event occurs.

#### Q23: What is the memory footprint of the supervisor under load?
**Answer:** Baseline memory is **22.6 MB RSS**. Under active management of 5 concurrent processes, memory is **23.07 MB RSS** — an overhead of less than 0.5 MB for multi-process monitoring.

---

### Security & System Boundaries

#### Q24: How does ResQ Web prevent arbitrary command execution?
**Answer:** ResQ Web strictly enforces `shell=False` across all subprocess creation routines. Arguments are parsed into discrete string arrays. Shell metacharacters (`|`, `&`, `;`, `&&`, `` ` ``) are treated as literal characters and cannot be interpreted as shell commands.

#### Q25: How does ResQ Web prevent path traversal attacks?
**Answer:** All target binary paths are sanitized using `os.path.abspath()` and verified on disk using `os.path.exists()` and `os.path.isfile()` before any execution call is made.

#### Q26: Does ResQ Web require Administrator privileges?
**Answer:** No. ResQ Web adheres to the principle of least privilege. It operates with standard user privileges, managing processes belonging to the logged-in user. Administrator rights are only needed if supervising system-level Windows services.

