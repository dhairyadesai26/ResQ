"""
ResQ Web - Test Worker Application
Simulates a stable, well-behaved Windows service or background worker.
Demonstrates clean lifecycle, heartbeats, and graceful termination.
"""

import os
import sys
import time
import signal

def handle_signal(sig, frame):
    sys.stdout.write(f"[{time.strftime('%X')}] Worker (PID: {os.getpid()}) received termination signal {sig}. Exiting cleanly with code 0.\n")
    sys.stdout.flush()
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    app_name = sys.argv[1] if len(sys.argv) > 1 else "DefaultWorker"
    interval = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0

    pid = os.getpid()
    sys.stdout.write(f"[{time.strftime('%X')}] [ResQ Test App] {app_name} started successfully. PID: {pid}\n")
    sys.stdout.flush()

    iteration = 0
    try:
        while True:
            iteration += 1
            sys.stdout.write(f"[{time.strftime('%X')}] Heartbeat #{iteration} - Process alive (PID: {pid})\n")
            sys.stdout.flush()
            time.sleep(interval)
    except KeyboardInterrupt:
        sys.stdout.write(f"[{time.strftime('%X')}] KeyboardInterrupt received. Exiting.\n")
        sys.stdout.flush()
        sys.exit(0)

if __name__ == "__main__":
    main()

