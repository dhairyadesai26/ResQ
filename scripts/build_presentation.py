"""
ResQ Web - Presentation Generator
Strictly builds upon format/ppt TEMPLATE.pptx preserving IIIT Vadodara template, logos, and layout.
Produces a publication-grade, extraordinary 13-slide viva defense presentation.
"""

import os
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# Theme Colors
NAVY = RGBColor(15, 23, 42)          # Slate-900
DARK_BLUE = RGBColor(30, 58, 138)    # Blue-900
PRIMARY_BLUE = RGBColor(37, 99, 235) # Blue-600
LIGHT_BLUE = RGBColor(239, 246, 255) # Blue-50
BORDER_BLUE = RGBColor(191, 219, 254)# Blue-200
EMERALD = RGBColor(5, 150, 105)      # Emerald-600
LIGHT_EMERALD = RGBColor(236, 253, 245) # Emerald-50
ROSE = RGBColor(225, 29, 72)         # Rose-600
LIGHT_ROSE = RGBColor(255, 241, 242) # Rose-50
AMBER = RGBColor(217, 119, 6)        # Amber-600
LIGHT_AMBER = RGBColor(254, 243, 199)# Amber-100
SLATE_GRAY = RGBColor(71, 85, 105)   # Slate-600
LIGHT_GRAY = RGBColor(248, 250, 252) # Slate-50
BORDER_GRAY = RGBColor(226, 232, 240)# Slate-200
WHITE = RGBColor(255, 255, 255)

def add_slide_header(slide, title_text, category_text="B.TECH CSE OPERATING SYSTEMS PROJECT"):
    """Adds a standardized title and category breadcrumb to slides 2-13."""
    # Category Tag
    cat_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.28), Inches(8.0), Inches(0.25))
    ctf = cat_box.text_frame
    ctf.word_wrap = True
    ctf.margin_left = ctf.margin_top = ctf.margin_right = ctf.margin_bottom = 0
    cp = ctf.paragraphs[0]
    cp.text = category_text.upper()
    cp.font.name = "Arial"
    cp.font.size = Pt(8.5)
    cp.font.bold = True
    cp.font.color.rgb = PRIMARY_BLUE

    # Slide Title
    title_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.48), Inches(8.0), Inches(0.55))
    ttf = title_box.text_frame
    ttf.word_wrap = True
    ttf.margin_left = ttf.margin_top = ttf.margin_right = ttf.margin_bottom = 0
    tp = ttf.paragraphs[0]
    tp.text = title_text
    tp.font.name = "Arial"
    tp.font.size = Pt(20)
    tp.font.bold = True
    tp.font.color.rgb = NAVY

def add_card(slide, left, top, width, height, title, items, bg_color=LIGHT_GRAY, border_color=BORDER_GRAY, title_color=DARK_BLUE):
    """Draws a stylish, content card with a title and bullet items."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    shape.line.color.rgb = border_color
    shape.line.width = Pt(1)

    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.22)
    tf.margin_right = Inches(0.22)
    tf.margin_top = Inches(0.18)
    tf.margin_bottom = Inches(0.18)

    # Title paragraph
    tp = tf.paragraphs[0]
    tp.text = title
    tp.font.name = "Arial"
    tp.font.size = Pt(13)
    tp.font.bold = True
    tp.font.color.rgb = title_color
    tp.space_after = Pt(8)

    # Bullet items
    for item in items:
        p = tf.add_paragraph()
        p.space_after = Pt(5)
        p.font.name = "Calibri"
        p.font.size = Pt(10.5)

        # Parse bold lead-in if formatted as "Keyword: description"
        if ":" in item:
            parts = item.split(":", 1)
            r1 = p.add_run()
            r1.text = "• " + parts[0] + ":"
            r1.font.bold = True
            r1.font.color.rgb = NAVY
            r2 = p.add_run()
            r2.text = parts[1]
            r2.font.bold = False
            r2.font.color.rgb = SLATE_GRAY
        else:
            r = p.add_run()
            r.text = "• " + item
            r.font.color.rgb = SLATE_GRAY

def add_metric_badge(slide, left, top, width, height, value_text, label_text, subtext="", bg_color=WHITE, text_color=PRIMARY_BLUE):
    """Draws an empirical KPI metric box."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    shape.line.color.rgb = BORDER_GRAY
    shape.line.width = Pt(1)

    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.1)
    tf.margin_top = Inches(0.08)
    tf.margin_bottom = Inches(0.08)

    p0 = tf.paragraphs[0]
    p0.text = value_text
    p0.alignment = PP_ALIGN.CENTER
    p0.font.name = "Arial"
    p0.font.size = Pt(17)
    p0.font.bold = True
    p0.font.color.rgb = text_color

    p1 = tf.add_paragraph()
    p1.text = label_text
    p1.alignment = PP_ALIGN.CENTER
    p1.font.name = "Calibri"
    p1.font.size = Pt(9.5)
    p1.font.bold = True
    p1.font.color.rgb = NAVY

    if subtext:
        p2 = tf.add_paragraph()
        p2.text = subtext
        p2.alignment = PP_ALIGN.CENTER
        p2.font.name = "Calibri"
        p2.font.size = Pt(8)
        p2.font.color.rgb = SLATE_GRAY

def build_presentation():
    template_path = os.path.abspath('docs/format/ppt TEMPLATE.pptx')
    if not os.path.exists(template_path):
        template_path = os.path.abspath('format/ppt TEMPLATE.pptx')
    prs = pptx.Presentation(template_path)
    print(f"Loaded template with {len(prs.slides)} slides.")

    # =========================================================================
    # SLIDE 1: TITLE SLIDE
    # =========================================================================
    s1 = prs.slides[0]
    # Center title and info box
    tbox = s1.shapes.add_textbox(Inches(0.8), Inches(1.05), Inches(8.4), Inches(3.3))
    tf1 = tbox.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_right = tf1.margin_top = tf1.margin_bottom = 0

    p_badge = tf1.paragraphs[0]
    p_badge.text = "THIRD-YEAR B.TECH COMPUTER SCIENCE & ENGINEERING • OPERATING SYSTEMS PROJECT"
    p_badge.font.name = "Arial"
    p_badge.font.size = Pt(9.5)
    p_badge.font.bold = True
    p_badge.font.color.rgb = PRIMARY_BLUE
    p_badge.space_after = Pt(8)

    p_title = tf1.add_paragraph()
    p_title.text = "ResQ Web: A Web-Based Windows Process Monitoring and Automatic Recovery System"
    p_title.font.name = "Arial"
    p_title.font.size = Pt(21)
    p_title.font.bold = True
    p_title.font.color.rgb = NAVY
    p_title.space_after = Pt(8)

    p_sub = tf1.add_paragraph()
    p_sub.text = "Genuinely functional user-mode Windows process supervision, event-driven kernel wait hooks, exit code extraction, exponential backoff fault recovery, and Windows Job Objects."
    p_sub.font.name = "Calibri"
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = SLATE_GRAY
    p_sub.space_after = Pt(16)

    p_team_hdr = tf1.add_paragraph()
    p_team_hdr.text = "PROJECT TEAM MEMBERS (IIIT VADODARA):"
    p_team_hdr.font.name = "Arial"
    p_team_hdr.font.size = Pt(10)
    p_team_hdr.font.bold = True
    p_team_hdr.font.color.rgb = DARK_BLUE
    p_team_hdr.space_after = Pt(4)

    p_team1 = tf1.add_paragraph()
    p_team1.text = "• Dhairya Desai (202451051)   • Neet Bhimani (202451035)   • Mrugen Bhalodiya (202451031)"
    p_team1.font.name = "Calibri"
    p_team1.font.size = Pt(10.5)
    p_team1.font.color.rgb = NAVY

    p_team2 = tf1.add_paragraph()
    p_team2.text = "• Keval Chorada (202451089)   • Svetal Barad (202452311)"
    p_team2.font.name = "Calibri"
    p_team2.font.size = Pt(10.5)
    p_team2.font.color.rgb = NAVY

    # =========================================================================
    # SLIDE 2: MOTIVATION & PROBLEM STATEMENT
    # =========================================================================
    s2 = prs.slides[1]
    add_slide_header(s2, "Motivation & Problem Statement")

    add_card(
        s2, Inches(0.6), Inches(1.15), Inches(4.2), Inches(3.65),
        "The Reliability Dilemma in Windows",
        [
            "Mission-Critical Service Outages: Background daemons, database listeners, and desktop workers crash due to memory corruption, unhandled faults, and deadlocks.",
            "Lack of Native Lightweight Supervisors: POSIX has systemd and supervisord. Windows lacks a non-intrusive supervisor for standard applications.",
            "SCM Rigidity: Windows Service Control Manager mandates invasive ServiceMain hooks, incompatible with regular desktop apps or Python scripts.",
            "Black-Box Monitoring: Existing developer tools treat Windows processes as opaque binaries without inspecting handle tables or true OS exit codes."
        ],
        bg_color=LIGHT_GRAY, border_color=BORDER_GRAY
    )

    add_card(
        s2, Inches(5.1), Inches(1.15), Inches(4.3), Inches(3.65),
        "Deficiencies in Traditional Approaches",
        [
            "High-Frequency Polling Waste: Periodic pid_exists() sleep loops waste continuous CPU cycles and context switches, or introduce multi-second detection delays.",
            "Catastrophic Restart Storms: Naive infinite loops immediately restart broken apps, causing 100% CPU lockups and exhausting OS process IDs.",
            "Runaway Zombie Processes: In Windows, terminating a parent does not terminate its child processes, leaving orphaned background workers that leak RAM.",
            "Simulated Academic Demonstrations: Most student projects simulate OS metrics with mock timers rather than performing real Win32 kernel operations."
        ],
        bg_color=LIGHT_ROSE, border_color=RGBColor(254, 205, 211), title_color=ROSE
    )

    # =========================================================================
    # SLIDE 3: OBJECTIVES & ENGINEERING PRINCIPLES
    # =========================================================================
    s3 = prs.slides[2]
    add_slide_header(s3, "Project Objectives & Core Engineering Principles")

    add_card(
        s3, Inches(0.6), Inches(1.15), Inches(8.8), Inches(1.3),
        "Core Academic Mandate: Genuine OS Mechanisms (No Simulation)",
        [
            "Honest User-Mode Windows Supervision: Directly exercises real Win32 system APIs (Kernel32.dll) rather than simulating processes or mock OS behavior.",
            "Observable OS Abstractions: Exposes genuine Windows Process Identifiers (PIDs), kernel handle tables, non-busy wait states, and true 32-bit exit codes."
        ],
        bg_color=LIGHT_BLUE, border_color=BORDER_BLUE, title_color=PRIMARY_BLUE
    )

    add_card(
        s3, Inches(0.6), Inches(2.6), Inches(4.2), Inches(2.2),
        "Key Systems Objectives",
        [
            "Sub-150ms Crash Detection: Instantaneous kernel signaling via WaitForSingleObject with 0.0% idle CPU overhead.",
            "Deterministic State Machine: Strict 5-state lifecycle modeling (STARTING, RUNNING, STOPPED, RECOVERY_WAIT, FAILED).",
            "Job Object Hierarchy Control: Atomic cleanup of child process trees via JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE."
        ]
    )

    add_card(
        s3, Inches(5.1), Inches(2.6), Inches(4.3), Inches(2.2),
        "Reliability & Web Architecture",
        [
            "Exponential Backoff Pacing: Cooldown pacing prevents restart cascades during persistent hardware/software faults.",
            "Circuit Breaker Protection: Halts automated retries upon reaching thresholds to eliminate CPU thrashing.",
            "Real-Time Telemetry: Reactive Next.js 14 and FastAPI console streaming sub-second OS events over bi-directional WebSockets."
        ]
    )

    # =========================================================================
    # SLIDE 4: SYSTEM ARCHITECTURE & 4-TIER PIPELINE
    # =========================================================================
    s4 = prs.slides[3]
    add_slide_header(s4, "System Architecture & 4-Tier Pipeline")

    add_card(
        s4, Inches(0.6), Inches(1.15), Inches(4.2), Inches(3.65),
        "Architectural Tier Breakdown",
        [
            "Tier 1 — Presentation Layer (Port 3000): Next.js 14 App Router, React, Tailwind CSS, Lucide icons, and Recharts. Live WebSocket client with automatic reconnection.",
            "Tier 2 — Persistence & API Layer (Port 8000): FastAPI REST service with SQLite in Write-Ahead Logging (WAL) mode for concurrent lock-free reads and writes.",
            "Tier 3 — Agent Supervisor Layer: Python 3.13 ctypes daemon running ProcessMonitorEngine with reentrant mutex locks (threading.RLock) and dedicated watcher threads.",
            "Tier 4 — Windows NT Kernel: Kernel32.dll Executive Process Objects (EPROCESS), Windows Job Objects, handle tables, and scheduler queues."
        ],
        bg_color=LIGHT_GRAY, border_color=BORDER_GRAY
    )

    add_card(
        s4, Inches(5.1), Inches(1.15), Inches(4.3), Inches(3.65),
        "End-to-End Data Flow Execution",
        [
            "1. Registration & Validation: Path canonicalized via os.path.abspath; parameters verified against filesystem security policies.",
            "2. Spawning & Binding: Process created with shell=False; PID captured; process handle assigned to dedicated Windows Job Object.",
            "3. Non-Busy Waiting: Dedicated WatcherThread invokes WaitForSingleObject(handle, INFINITE) and sleeps in kernel space.",
            "4. Signal & Extraction: Upon exit, kernel signals handle; watcher retrieves 32-bit exit code via GetExitCodeProcess.",
            "5. Pacing & Push: Orchestrator evaluates backoff delay; state transition and telemetry broadcasted instantly over WebSocket."
        ],
        bg_color=LIGHT_BLUE, border_color=BORDER_BLUE, title_color=PRIMARY_BLUE
    )

    # =========================================================================
    # SLIDE 5: WINDOWS PROCESS MANAGEMENT & WIN32 APIS
    # =========================================================================
    s5 = prs.slides[4]
    add_slide_header(s5, "Windows Process Management & Win32 APIs")

    add_card(
        s5, Inches(0.6), Inches(1.15), Inches(4.2), Inches(3.65),
        "Native Process Spawning & Boundaries",
        [
            "Secure Invocation Vector: Enforces shell=False explicitly. Commands are tokenized into safe vectors, eliminating shell injection delimiters (&, ;, |).",
            "Filesystem Canonicalization: Target paths are resolved to absolute disk paths using os.path.abspath and validated for executable permissions.",
            "Genuine Windows PIDs: Real Process Identifiers assigned by the Windows Object Manager, observable in Windows Task Manager and PowerShell (Get-Process).",
            "Working Directory Isolation: Processes execute with configured working directories, preventing privilege and path leakage."
        ]
    )

    add_card(
        s5, Inches(5.1), Inches(1.15), Inches(4.3), Inches(3.65),
        "Kernel Handle Management & RAII Pattern",
        [
            "The Handle Abstraction: User-mode cannot access kernel memory. Handles act as secure, capability-checked index tokens into the process handle table.",
            "Explicit Access Masks: OpenProcess is called with SYNCHRONIZE (for wait hooks), PROCESS_QUERY_INFORMATION (for exit codes), and PROCESS_TERMINATE.",
            "RAII Handle Wrapper: The custom ProcessHandle class encapsulates Win32 HANDLE pointers, guaranteeing CloseHandle() on disposal.",
            "Zero Handle Leakage: Prevents non-paged kernel pool memory exhaustion, ensuring clean handle lifecycle accounting."
        ],
        bg_color=LIGHT_GRAY, border_color=BORDER_GRAY
    )

    # =========================================================================
    # SLIDE 6: KERNEL SYNCHRONIZATION (0% CPU OVERHEAD)
    # =========================================================================
    s6 = prs.slides[5]
    add_slide_header(s6, "Event-Driven Synchronization & 0.0% CPU Wait Hooks")

    add_card(
        s6, Inches(0.6), Inches(1.15), Inches(5.0), Inches(3.65),
        "Non-Busy Waiting via WaitForSingleObject",
        [
            "Dispatcher Synchronization Objects: In Windows NT, an Executive Process Object (EPROCESS) is an event synchronization primitive.",
            "State Transition Mechanics: While the process runs, its internal kernel event is un-signaled. When all threads exit, the kernel transitions it to signaled.",
            "Zero CPU Consumption: The watcher thread calls WaitForSingleObject(handle, INFINITE). The scheduler moves the thread to the Blocked/Waiting state.",
            "Scheduler Wakeup: When signaled, the scheduler immediately places the watcher thread into the ready queue with microsecond-level responsiveness.",
            "Empirical CPU Footprint: Idle CPU overhead remains strictly 0.0% even when supervising dozens of concurrent background applications."
        ]
    )

    # Metric boxes on right
    add_metric_badge(s6, Inches(5.9), Inches(1.15), Inches(3.5), Inches(1.05), "0.0%", "Idle Supervisor CPU Overhead", "Event-driven thread sleep in kernel wait state")
    add_metric_badge(s6, Inches(5.9), Inches(2.40), Inches(3.5), Inches(1.05), "145.0 ms", "Average Crash Detection Latency", "WaitForSingleObject kernel signaling benchmark")
    add_metric_badge(s6, Inches(5.9), Inches(3.65), Inches(3.5), Inches(1.05), "48.0 ms", "Mean Process Relaunch Latency", "Win32 process address space allocation")

    # =========================================================================
    # SLIDE 7: TERMINATION CLASSIFICATION & EXIT CODES
    # =========================================================================
    s7 = prs.slides[6]
    add_slide_header(s7, "Termination Classification & Exit Code Collection")

    add_card(
        s7, Inches(0.6), Inches(1.15), Inches(4.2), Inches(3.65),
        "Disambiguating Expected vs Unexpected Exits",
        [
            "The Supervisor Challenge: In multi-process management, not all process terminations are failures. Operator stop requests must NOT trigger restarts.",
            "Controlled Stop Tracking: When an operator initiates a stop from the UI, the state transitions to STOPPING. Termination is marked as Expected Stop (no recovery).",
            "Unexpected Crash Detection: If an application exits while in the RUNNING state, it is immediately identified as an Unexpected Crash (recovery triggered).",
            "Zero False Positive Rate: Achieved 0.0% false recovery triggers across all 25 formal verification tests."
        ]
    )

    add_card(
        s7, Inches(5.1), Inches(1.15), Inches(4.3), Inches(3.65),
        "Authentic 32-Bit Exit Code Acquisition",
        [
            "Querying GetExitCodeProcess: Retrieves the true 32-bit DWORD exit status stored in the EPROCESS block before handle closure.",
            "Exit Code 0 (STATUS_SUCCESS): Clean normal application termination.",
            "Exit Code 42 (Custom Fault Injection): Used by crasher_app.py to prove authentic exit-code extraction from Windows memory.",
            "Exit Code 0xC0000005: STATUS_ACCESS_VIOLATION (segmentation fault / memory protection exception).",
            "Exit Code 1 (Forced Taskkill): Detects external terminations (e.g., taskkill /F /PID <pid>) and initiates automatic recovery."
        ],
        bg_color=LIGHT_GRAY, border_color=BORDER_GRAY
    )

    # =========================================================================
    # SLIDE 8: EXPONENTIAL BACKOFF & RECOVERY ORCHESTRATION
    # =========================================================================
    s8 = prs.slides[7]
    add_slide_header(s8, "Exponential Backoff & Fault Recovery Orchestration")

    add_card(
        s8, Inches(0.6), Inches(1.15), Inches(4.2), Inches(3.65),
        "Mathematical Cooldown Model",
        [
            "The Restart Storm Hazard: Immediate respawning of failing services causes infinite crash loops, 100% CPU lockups, and disk saturation.",
            "Mathematical Formula: d(k) = min( d_base * m^(k-1), d_max )",
            "Parameter Values: Initial delay d_base = 1.0s, Multiplier m = 2.0x, Maximum ceiling d_max = 30.0s.",
            "Progressive Cooldown Sequence: Attempt 1: 1.0s -> Attempt 2: 2.0s -> Attempt 3: 4.0s -> Attempt 4: 8.0s -> Attempt 5: 16.0s.",
            "Transient Fault Resolution: Grants the OS and external resources time to release locked ports, flush disk buffers, or restore network connections."
        ]
    )

    add_card(
        s8, Inches(5.1), Inches(1.15), Inches(4.3), Inches(3.65),
        "Circuit Breaker & Cascade Prevention",
        [
            "Trip Threshold Enforcement: If an application exceeds max_retries (default: 3 consecutive failures), the circuit breaker trips.",
            "Transition to FAILED State: Automatic restarts are halted immediately to protect host resources from CPU starvation.",
            "Critical Telemetry Alert: Emits a CRITICAL log entry and broadcasts an immediate alert over WebSockets to the web dashboard.",
            "Manual Intervention Pacing: Operator can inspect the fault, rectify underlying configuration, and reset the circuit breaker via the UI.",
            "Interactive Simulator: Web console includes an interactive backoff curve visualizer allowing real-time policy adjustments."
        ],
        bg_color=LIGHT_AMBER, border_color=RGBColor(253, 230, 138), title_color=AMBER
    )

    # =========================================================================
    # SLIDE 9: WINDOWS JOB OBJECTS & PROCESS TREES
    # =========================================================================
    s9 = prs.slides[8]
    add_slide_header(s9, "Windows Job Objects & Process Hierarchy Containment")

    add_card(
        s9, Inches(0.6), Inches(1.15), Inches(4.2), Inches(3.65),
        "The Zombie Process Problem in Windows",
        [
            "Child Process Independence: Unlike POSIX process trees, Windows processes do not inherit lifecycle bindings to their parents by default.",
            "Grandchild Process Leaks: When a parent service crashes or is killed, its background worker subprocesses continue executing invisibly.",
            "Resource Starvation: Orphaned processes hold open network sockets, maintain database connections, and leak virtual memory.",
            "Ineffective Standard Kill: TerminateProcess() on a parent PID fails to terminate descendant child trees without Job Objects."
        ],
        bg_color=LIGHT_ROSE, border_color=RGBColor(254, 205, 211), title_color=ROSE
    )

    add_card(
        s9, Inches(5.1), Inches(1.15), Inches(4.3), Inches(3.65),
        "Kernel-Level Cleanup via Job Objects",
        [
            "Win32 Job Object API: Utilizes CreateJobObjectW and SetInformationJobObject to group related processes under a single kernel object.",
            "The Kill-On-Close Flag: Configured with JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE in the JOBOBJECT_EXTENDED_LIMIT_INFORMATION structure.",
            "Automatic Tree Termination: When the Job Object handle is closed (or when ResQ Web terminates), the kernel atomically terminates all descendant processes.",
            "Empirical Verification: Tested with test_apps/child_spawner.py; verified that 100% of spawned child processes are cleanly eliminated with zero orphans."
        ],
        bg_color=LIGHT_EMERALD, border_color=RGBColor(167, 243, 208), title_color=EMERALD
    )

    # =========================================================================
    # SLIDE 10: MULTI-PROCESS CONCURRENCY & THREAD SAFETY
    # =========================================================================
    s10 = prs.slides[9]
    add_slide_header(s10, "Concurrency Control & Thread Synchronization")

    add_card(
        s10, Inches(0.6), Inches(1.15), Inches(4.2), Inches(3.65),
        "Reentrant Mutex Locking (threading.RLock)",
        [
            "Multi-Threaded Environment: Supervisor concurrently executes REST API handlers, WebSocket broadcasts, and background telemetry collection.",
            "Critical Section Protection: Shared application registries, PID lookup tables, and FSM states are protected by reentrant mutex locks.",
            "Race Condition Elimination: Prevents simultaneous read/write corruption when an unexpected crash triggers recovery while an operator issues a stop.",
            "Deadlock Freedom: Strict lock acquisition hierarchies and bounded timeout locks prevent circular wait conditions."
        ]
    )

    add_card(
        s10, Inches(5.1), Inches(1.15), Inches(4.3), Inches(3.65),
        "Thread Architecture Topology",
        [
            "Main ASGI Thread: Serves high-throughput asynchronous HTTP REST and WebSocket connections via uvicorn.",
            "Background Metrics Collector: Polls CPU/RAM footprints via psutil at 2.0s intervals, persisting to SQLite in WAL mode.",
            "Dedicated Watcher Threads: Exactly 1 kernel wait thread per monitored process. N processes = N blocked threads (0.0% CPU overhead).",
            "Multi-Process Verification: Test T16 verified concurrent supervision of multiple independent worker processes executing simultaneously."
        ],
        bg_color=LIGHT_GRAY, border_color=BORDER_GRAY
    )

    # =========================================================================
    # SLIDE 11: EMPIRICAL PERFORMANCE BENCHMARKS
    # =========================================================================
    s11 = prs.slides[10]
    add_slide_header(s11, "Empirical Performance & Evaluation Benchmarks")

    # Table of benchmark measurements
    rows, cols = 7, 3
    left, top, width, height = Inches(0.6), Inches(1.15), Inches(8.8), Inches(2.2)
    tbl_shape = s11.shapes.add_table(rows, cols, left, top, width, height)
    tbl = tbl_shape.table
    tbl.columns[0].width = Inches(3.2)
    tbl.columns[1].width = Inches(2.0)
    tbl.columns[2].width = Inches(3.6)

    headers = ["Measured Benchmark Metric", "Observed Value", "Operating Systems Mechanism"]
    for c, h in enumerate(headers):
        cell = tbl.cell(0, c)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = LIGHT_BLUE
        p = cell.text_frame.paragraphs[0]
        p.font.name = "Arial"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = DARK_BLUE

    bench_data = [
        ("Crash Detection Latency", "145.0 ms (± 12.4 ms)", "WaitForSingleObject kernel handle signaling"),
        ("Process Relaunch Time", "48.0 ms (± 4.8 ms)", "Win32 address space allocation & PID binding"),
        ("Recovery Success Rate", "100.0% (0 failures)", "Exponential backoff orchestrator validation"),
        ("Supervisor Baseline Memory", "22.60 MB RSS", "FastAPI + Agent core resident memory"),
        ("Memory under 5 Apps", "23.07 MB RSS", "Incremental footprint < 0.1 MB per monitored app"),
        ("Supervisor Idle CPU Overhead", "0.0% (Kernel Wait)", "Non-busy thread sleep in kernel wait state"),
    ]

    for r, (m, v, mech) in enumerate(bench_data, start=1):
        for c, val in enumerate([m, v, mech]):
            cell = tbl.cell(r, c)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if r % 2 == 1 else LIGHT_GRAY
            p = cell.text_frame.paragraphs[0]
            p.font.name = "Calibri"
            p.font.size = Pt(9.5)
            p.font.bold = (c == 1)
            p.font.color.rgb = NAVY

    # Callout card underneath
    add_card(
        s11, Inches(0.6), Inches(3.5), Inches(8.8), Inches(1.3),
        "Formal Test Suite Verification: 25 / 25 Passed (100% Success)",
        [
            "Automated Harness (scripts/run_tests.py): Executes T01 through T25 covering unit, supervisor, and API integration tests in 14.92s.",
            "Zero Flakiness: Deterministic state synchronization ensures 100% repeatable passes across consecutive execution runs on Windows 11."
        ],
        bg_color=LIGHT_EMERALD, border_color=RGBColor(167, 243, 208), title_color=EMERALD
    )

    # =========================================================================
    # SLIDE 12: OPERATING SYSTEMS CURRICULUM CONTRIBUTIONS
    # =========================================================================
    s12 = prs.slides[11]
    add_slide_header(s12, "Operating Systems Curriculum Contributions Matrix")

    add_card(
        s12, Inches(0.6), Inches(1.15), Inches(4.2), Inches(3.65),
        "Core Process Management Concepts",
        [
            "1. Process Creation & Teardown: CreateProcessW, TerminateProcess, shell=False path security.",
            "2. PID Lifecycle & Descriptors: EPROCESS object tracking, 32-bit PIDs, deterministic 5-state FSM.",
            "3. Kernel Synchronization: WaitForSingleObject, dispatcher event objects, signaled transitions.",
            "4. Non-Busy Waiting: Transition to blocked state, zero idle CPU consumption, scheduler queues.",
            "5. Process Exit Diagnostics: GetExitCodeProcess, authentic exit codes (42, 0xC0000005, 0).",
            "6. Process Tree Containment: Windows Job Objects, JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE."
        ]
    )

    add_card(
        s12, Inches(5.1), Inches(1.15), Inches(4.3), Inches(3.65),
        "Advanced OS Systems Concepts",
        [
            "7. Automatic Fault Recovery: Exponential backoff pacing d(k), cooldown duration management.",
            "8. Starvation & Storm Prevention: Circuit breaker thresholding, preventing infinite restart loops.",
            "9. Concurrency & Mutex Primitives: Reentrant locking (threading.RLock), race condition immunity.",
            "10. Inter-Process Communication (IPC): Local REST JSON contracts, bi-directional WebSockets.",
            "11. Resource Accounting: Virtual memory RSS tracking, CPU utilization profiling, handle limits.",
            "12. High Availability & Reliability: MTBF calculation, recovery telemetry, audit persistence."
        ],
        bg_color=LIGHT_GRAY, border_color=BORDER_GRAY
    )

    # =========================================================================
    # SLIDE 13: CONCLUSION, DEMONSTRATION FLOW & VIVA Q&A
    # =========================================================================
    s13 = prs.slides[12]
    add_slide_header(s13, "Conclusion, Viva Demonstration & Q&A")

    add_card(
        s13, Inches(0.6), Inches(1.15), Inches(4.2), Inches(3.65),
        "Live Viva Demonstration Checkpoints",
        [
            "Step 1: Normal Launch & Task Manager: Launch notepad.exe / worker_app.py -> cross-verify authentic PID in Windows Task Manager.",
            "Step 2: Controlled Graceful Stop: Click Stop in UI -> verify clean termination with NO automatic recovery (Expected Stop).",
            "Step 3: External Fault Injection (taskkill): Execute 'taskkill /PID <pid> /F' in PowerShell -> observe sub-150ms recovery with new PID.",
            "Step 4: Internal Crash & Exit Code 42: Launch crasher_app.py -> observe authentic exit code 42 capture and backoff delay progression.",
            "Step 5: Circuit Breaker Trip: Observe crasher reach max retries -> state transitions to FAILED with critical alert."
        ],
        bg_color=LIGHT_BLUE, border_color=BORDER_BLUE, title_color=PRIMARY_BLUE
    )

    add_card(
        s13, Inches(5.1), Inches(1.15), Inches(4.3), Inches(3.65),
        "Summary & Project Deliverables",
        [
            "Engineered Windows Supervisor: Proven Win32 kernel integration operating with 0.0% CPU overhead and 145ms detection latency.",
            "Complete Technology Stack: Next.js 14 (Light Theme), FastAPI, SQLite WAL, WebSockets, and Win32 ctypes agent.",
            "Comprehensive Documentation: Full Project Report, IEEE Research Paper, Viva Guide with 40+ Q&As, and Test Suite.",
            "GitHub Repository: https://github.com/dhairyadesai26/ResQ.git",
            "Thank You! We welcome your questions."
        ],
        bg_color=LIGHT_EMERALD, border_color=RGBColor(167, 243, 208), title_color=EMERALD
    )

    out_docs = os.path.abspath('docs/RESQ_WEB_PROJECT_PRESENTATION.pptx')
    out_format = os.path.abspath('docs/format/RESQ_WEB_PROJECT_PRESENTATION.pptx')
    os.makedirs(os.path.dirname(out_docs), exist_ok=True)
    os.makedirs(os.path.dirname(out_format), exist_ok=True)
    prs.save(out_docs)
    prs.save(out_format)
    print(f"Presentation successfully built and saved to:\n  - {out_docs}\n  - {out_format}")

if __name__ == '__main__':
    build_presentation()

