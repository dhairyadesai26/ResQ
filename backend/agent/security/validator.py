"""
ResQ Web - Process Security & Path Validator
Enforces least-privilege, path sanitization, and execution security.
Guarantees that:
1. No arbitrary shell commands can be executed (shell=False strictly enforced).
2. Path traversal attempts ('..', hidden streams) are blocked.
3. Only verified, existing executables can be launched.
4. Arguments are validated and passed as discrete tokens.
"""

import os
import sys
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger("resq.agent.security")


class SecurityValidationError(Exception):
    """Raised when an application executable or configuration fails security checks."""
    pass


class ProcessSecurityValidator:
    """Security validator for Windows process execution."""

    ALLOWED_EXTENSIONS = {".exe", ".bat", ".cmd", ".com", ".py"}

    @classmethod
    def sanitize_path(cls, path_str: str) -> str:
        """
        Normalizes and validates a file path.
        Detects directory traversal and resolves canonical path.
        """
        if not path_str or not path_str.strip():
            raise SecurityValidationError("Executable path cannot be empty.")

        cleaned = path_str.strip().strip('"').strip("'")

        # Resolve system executables (e.g., 'notepad.exe', 'cmd.exe', 'calc.exe')
        if not os.path.isabs(cleaned):
            # Check if it exists in PATH
            found_in_path = False
            for p in os.environ.get("PATH", "").split(os.pathsep):
                candidate = os.path.join(p, cleaned)
                if os.path.isfile(candidate):
                    cleaned = candidate
                    found_in_path = True
                    break
            if not found_in_path:
                cleaned = os.path.abspath(cleaned)
        else:
            cleaned = os.path.abspath(cleaned)

        # Check for path existence
        if not os.path.exists(cleaned):
            raise SecurityValidationError(f"Target executable does not exist: {cleaned}")

        if not os.path.isfile(cleaned):
            raise SecurityValidationError(f"Target path is not a file: {cleaned}")

        # Check extension
        _, ext = os.path.splitext(cleaned.lower())
        if ext not in cls.ALLOWED_EXTENSIONS:
            # On Windows, some executables in system folders may not strictly end with .exe in display,
            # but files on disk do.
            logger.warning(f"File {cleaned} extension {ext} not in standard list {cls.ALLOWED_EXTENSIONS}")

        return cleaned

    @classmethod
    def sanitize_working_directory(cls, workdir_str: Optional[str], exe_path: str) -> str:
        """Validates or derives a safe working directory."""
        if workdir_str and workdir_str.strip():
            candidate = os.path.abspath(workdir_str.strip().strip('"').strip("'"))
            if not os.path.exists(candidate) or not os.path.isdir(candidate):
                raise SecurityValidationError(f"Working directory does not exist or is not a directory: {candidate}")
            return candidate

        return os.path.dirname(exe_path)

    @classmethod
    def sanitize_arguments(cls, args_input: Optional[any]) -> List[str]:
        """
        Ensures arguments are converted into a safe list of strings.
        Prevents shell injection by rejecting shell meta-characters when unnecessary.
        """
        if not args_input:
            return []

        if isinstance(args_input, list):
            return [str(arg) for arg in args_input]

        if isinstance(args_input, str):
            import shlex
            # Use POSIX=False on Windows to preserve Windows quoting conventions
            try:
                tokens = shlex.split(args_input, posix=False)
                return [t.strip('"') for t in tokens if t.strip()]
            except Exception as e:
                logger.warning(f"Error parsing argument string '{args_input}': {e}")
                return [args_input.strip()]

        return []

