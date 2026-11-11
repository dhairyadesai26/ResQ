"""
ResQ Web - Controlled Fault Injection Application
Simulates unexpected process termination (crash, segmentation fault, unhandled exception).
Used to rigorously test detection latency, exit code capture, and automatic recovery.
"""

import os
import sys
import time
import argparse

def main():
    parser = argparse.ArgumentParser(description="Fault Injection Test Program")
    parser.add_argument("--crash-after", type=float, default=4.0, help="Seconds before crash")
    parser.add_argument("--exit-code", type=int, default=42, help="Process exit code on crash")
    parser.add_argument("--crash-mode", choices=["exit", "exception", "abort"], default="exit",
                        help="How to simulate the fault")
    args, unknown = parser.parse_known_args()

    pid = os.getpid()
    sys.stdout.write(f"[{time.strftime('%X')}] [CRASHER TEST] Process started. PID: {pid}\n")
    sys.stdout.write(f"[{time.strftime('%X')}] Scheduled to crash in {args.crash_after}s with exit code {args.exit_code} (Mode: {args.crash_mode})\n")
    sys.stdout.flush()

    start_time = time.time()
    while time.time() - start_time < args.crash_after:
        remaining = args.crash_after - (time.time() - start_time)
        sys.stdout.write(f"[{time.strftime('%X')}] PID {pid} running... crash in {remaining:.1f}s\n")
        sys.stdout.flush()
        time.sleep(min(1.0, max(0.1, remaining)))

    sys.stderr.write(f"[{time.strftime('%X')}] FATAL FAULT TRIGGERED in PID {pid}! Simulating unhandled crash.\n")
    sys.stderr.flush()

    if args.crash_mode == "abort":
        os.abort()
    elif args.crash_mode == "exception":
        raise RuntimeError(f"Simulated unhandled exception causing process crash (PID: {pid})")
    else:
        # Hard exit bypassing cleanup handlers to simulate actual crash
        os._exit(args.exit_code)

if __name__ == "__main__":
    main()

