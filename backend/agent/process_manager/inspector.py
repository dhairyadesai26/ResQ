"""
ResQ Web - Real-Time Process Resource Inspector
Leverages psutil and Win32 interfaces to sample actual runtime metrics:
- Process CPU utilization (%)
- Working Set (Physical RAM in bytes)
- Thread count
- Handle count (Windows specific)
- Disk I/O activity
"""

import sys
import psutil
from dataclasses import dataclass
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger("resq.agent.inspector")


@dataclass
class ProcessMetrics:
    pid: int
    is_running: bool
    cpu_percent: float
    memory_rss: int
    memory_vms: int
    memory_percent: float
    num_threads: int
    num_handles: int
    status: str
    create_time: float


class ProcessInspector:
    """Inspects live Windows process states and resource utilization."""

    @classmethod
    def inspect(cls, pid: int) -> Optional[ProcessMetrics]:
        """Collects metrics for a specific PID."""
        try:
            if not psutil.pid_exists(pid):
                return None

            proc = psutil.Process(pid)
            if not proc.is_running() or proc.status() == psutil.STATUS_ZOMBIE:
                return None

            # Get metrics safely
            with proc.oneshot():
                cpu_pct = proc.cpu_percent(interval=None)
                mem_info = proc.memory_info()
                mem_pct = proc.memory_percent()
                threads_cnt = proc.num_threads()
                status_str = proc.status()
                create_t = proc.create_time()

                handles_cnt = 0
                if sys.platform == "win32":
                    try:
                        handles_cnt = proc.num_handles()
                    except Exception:
                        handles_cnt = 0

            return ProcessMetrics(
                pid=pid,
                is_running=True,
                cpu_percent=round(cpu_pct, 2),
                memory_rss=mem_info.rss,
                memory_vms=mem_info.vms,
                memory_percent=round(mem_pct, 2),
                num_threads=threads_cnt,
                num_handles=handles_cnt,
                status=status_str,
                create_time=create_t,
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None
        except Exception as e:
            logger.debug(f"Inspector error on PID {pid}: {e}")
            return None

    @classmethod
    def get_system_metrics(cls) -> Dict[str, Any]:
        """Collects system-wide CPU and Memory statistics."""
        vm = psutil.virtual_memory()
        cpu_pct = psutil.cpu_percent(interval=None)
        cpu_count = psutil.cpu_count(logical=True)

        return {
            "cpu_percent": round(cpu_pct, 1),
            "cpu_count": cpu_count,
            "memory_total": vm.total,
            "memory_available": vm.available,
            "memory_used": vm.used,
            "memory_percent": round(vm.percent, 1),
        }

