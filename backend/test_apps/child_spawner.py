"""
ResQ Web - Child Process Spawner Test Program
Spawns background child processes to test Windows Job Object management.
Verifies that when the parent process is terminated or recovered, all child
processes are cleaned up automatically without leaving zombie/orphaned processes.
"""

import os
import sys
import time
import subprocess

def main():
    pid = os.getpid()
    sys.stdout.write(f"[{time.strftime('%X')}] [CHILD SPAWNER] Parent process started. PID: {pid}\n")
    sys.stdout.flush()

    python_exe = sys.executable
    script_path = os.path.join(os.path.dirname(__file__), "worker_app.py")

    children = []
    for i in range(2):
        child = subprocess.Popen([python_exe, script_path, f"JobChild_{i+1}", "2.0"])
        children.append(child)
        sys.stdout.write(f"[{time.strftime('%X')}] Spawned Child #{i+1} with PID: {child.pid}\n")
        sys.stdout.flush()

    try:
        iteration = 0
        while True:
            iteration += 1
            alive_count = sum(1 for c in children if c.poll() is None)
            sys.stdout.write(f"[{time.strftime('%X')}] Spawner active (PID {pid}), {alive_count} children alive\n")
            sys.stdout.flush()
            time.sleep(1.0)
    finally:
        for c in children:
            if c.poll() is None:
                c.terminate()

if __name__ == "__main__":
    main()

