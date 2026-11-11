"""
ResQ Web - Native Windows Process Management Interface
Encapsulates Win32 kernel32 API calls via ctypes and pywin32.
Demonstrates low-level OS mechanisms:
- Real Process Handles (OpenProcess, CloseHandle)
- Process Synchronization (WaitForSingleObject)
- Process Exit Codes (GetExitCodeProcess)
- Controlled Process Termination (TerminateProcess)
- Windows Job Objects (CreateJobObjectW, SetInformationJobObject, AssignProcessToJobObject)
"""

import sys
import ctypes
from ctypes import wintypes
from typing import Optional, Tuple
import logging

logger = logging.getLogger("resq.agent.win32")

# Check if running on Windows
IS_WINDOWS = sys.platform == "win32"

# Windows Process Access Rights Constants
PROCESS_TERMINATE = 0x0001
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
SYNCHRONIZE = 0x00100000
STANDARD_RIGHTS_REQUIRED = 0x000F0000

# Standard Wait Constants
WAIT_OBJECT_0 = 0x00000000
WAIT_TIMEOUT = 0x00000102
WAIT_FAILED = 0xFFFFFFFF
INFINITE = 0xFFFFFFFF

# Exit Code Constants
STILL_ACTIVE = 259  # 0x00000103

# Job Object Limit Constants
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JobObjectExtendedLimitInformation = 9

if IS_WINDOWS:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    # Function prototypes
    OpenProcess = kernel32.OpenProcess
    OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    OpenProcess.restype = wintypes.HANDLE

    CloseHandle = kernel32.CloseHandle
    CloseHandle.argtypes = [wintypes.HANDLE]
    CloseHandle.restype = wintypes.BOOL

    WaitForSingleObject = kernel32.WaitForSingleObject
    WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    WaitForSingleObject.restype = wintypes.DWORD

    GetExitCodeProcess = kernel32.GetExitCodeProcess
    GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    GetExitCodeProcess.restype = wintypes.BOOL

    TerminateProcess = kernel32.TerminateProcess
    TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    TerminateProcess.restype = wintypes.BOOL

    CreateJobObjectW = kernel32.CreateJobObjectW
    CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
    CreateJobObjectW.restype = wintypes.HANDLE

    AssignProcessToJobObject = kernel32.AssignProcessToJobObject
    AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    AssignProcessToJobObject.restype = wintypes.BOOL

    # Job object struct definitions
    class IO_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_uint64),
            ("WriteOperationCount", ctypes.c_uint64),
            ("OtherOperationCount", ctypes.c_uint64),
            ("ReadTransferCount", ctypes.c_uint64),
            ("WriteTransferCount", ctypes.c_uint64),
            ("OtherTransferCount", ctypes.c_uint64),
        ]

    class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", wintypes.LARGE_INTEGER),
            ("PerJobUserTimeLimit", wintypes.LARGE_INTEGER),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.POINTER(ctypes.c_ulong)),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    SetInformationJobObject = kernel32.SetInformationJobObject
    SetInformationJobObject.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
    ]
    SetInformationJobObject.restype = wintypes.BOOL


def open_process_handle(pid: int, access_flags: Optional[int] = None) -> Optional[int]:
    """
    Acquires an actual Windows kernel handle for the process identified by PID.
    Uses PROCESS_QUERY_INFORMATION | SYNCHRONIZE | PROCESS_TERMINATE by default.
    """
    if not IS_WINDOWS:
        return None

    if access_flags is None:
        access_flags = PROCESS_QUERY_INFORMATION | SYNCHRONIZE | PROCESS_TERMINATE

    handle = OpenProcess(access_flags, False, pid)
    if not handle:
        error_code = ctypes.get_last_error()
        logger.debug(f"OpenProcess failed for PID {pid} with Win32 error: {error_code}")
        return None
    return handle


def close_process_handle(handle: Optional[int]) -> bool:
    """Closes an open Windows process or job handle."""
    if not IS_WINDOWS or not handle:
        return True
    try:
        success = CloseHandle(handle)
        return bool(success)
    except Exception as e:
        logger.warning(f"Error closing handle {handle}: {e}")
        return False


def wait_for_process_handle(handle: int, timeout_ms: int = 500) -> Tuple[bool, int]:
    """
    Performs a non-busy wait on the Windows process handle using WaitForSingleObject.
    Returns (exited: bool, wait_result: int).
    """
    if not IS_WINDOWS or not handle:
        return (True, WAIT_FAILED)

    result = WaitForSingleObject(handle, timeout_ms)
    if result == WAIT_OBJECT_0:
        return (True, result)
    elif result == WAIT_TIMEOUT:
        return (False, result)
    else:
        return (False, result)


def get_process_exit_code_native(handle: int) -> Optional[int]:
    """
    Queries the actual exit code from the Windows kernel using GetExitCodeProcess.
    Returns None if the process is still running (STILL_ACTIVE).
    """
    if not IS_WINDOWS or not handle:
        return None

    exit_code = wintypes.DWORD()
    success = GetExitCodeProcess(handle, ctypes.byref(exit_code))
    if not success:
        error_code = ctypes.get_last_error()
        logger.debug(f"GetExitCodeProcess failed for handle {handle}: {error_code}")
        return None

    if exit_code.value == STILL_ACTIVE:
        return None
    return int(exit_code.value)


def terminate_process_native(handle: int, exit_code: int = 1) -> bool:
    """
    Terminates the specified process using Win32 TerminateProcess.
    This provides an authoritative stop even when standard SIGTERM is ignored.
    """
    if not IS_WINDOWS or not handle:
        return False

    success = TerminateProcess(handle, exit_code)
    return bool(success)


def create_job_object_with_kill_on_close(name: Optional[str] = None) -> Optional[int]:
    """
    Creates a Windows Job Object configured with JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE.
    This ensures that when ResQ Web stops managing an application or the supervisor closes,
    all descendant processes spawned by that application are cleanly terminated.
    """
    if not IS_WINDOWS:
        return None

    job = CreateJobObjectW(None, name)
    if not job:
        error_code = ctypes.get_last_error()
        logger.error(f"Failed to create Job Object: {error_code}")
        return None

    info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE

    success = SetInformationJobObject(
        job,
        JobObjectExtendedLimitInformation,
        ctypes.byref(info),
        ctypes.sizeof(info),
    )
    if not success:
        error_code = ctypes.get_last_error()
        logger.warning(f"Failed to configure Job Object limits: {error_code}")

    return job


def assign_process_to_job_native(job_handle: int, process_handle: int) -> bool:
    """Assigns an active process to a Windows Job Object."""
    if not IS_WINDOWS or not job_handle or not process_handle:
        return False

    success = AssignProcessToJobObject(job_handle, process_handle)
    if not success:
        error_code = ctypes.get_last_error()
        logger.debug(f"AssignProcessToJobObject failed: {error_code}")
        return False
    return True

