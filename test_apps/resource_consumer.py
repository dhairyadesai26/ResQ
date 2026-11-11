"""
ResQ Web - Resource Consumer Test Program
Periodically loads memory buffers and does math computations to test
live CPU and memory tracking in ResQ Web.
"""

import os
import sys
import time

def main():
    pid = os.getpid()
    sys.stdout.write(f"[{time.strftime('%X')}] [RESOURCE CONSUMER] Started. PID: {pid}\n")
    sys.stdout.flush()

    buffers = []
    try:
        for cycle in range(1, 1000):
            # Allocate ~15 MB
            buffers.append(bytearray(15 * 1024 * 1024))
            if len(buffers) > 5:
                buffers.pop(0)  # Keep steady memory footprint around 60-75 MB

            # Brief CPU burst
            total = 0
            for i in range(1_000_000):
                total += i % 7

            sys.stdout.write(f"[{time.strftime('%X')}] Cycle #{cycle} completed (Active buffers: {len(buffers)})\n")
            sys.stdout.flush()
            time.sleep(1.0)
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()

