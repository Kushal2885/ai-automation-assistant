"""
code_executor.py
----------------
Safely executes AI-generated Python code in an isolated subprocess.

Safety strategy (prototype-grade):
  1. Pattern scanning  — block dangerous calls before execution even starts.
  2. Subprocess isolation — code runs in a child process, not via exec() in
     the main app. A crash or exception cannot affect Streamlit.
  3. Timeout enforcement — kills the process after EXECUTION_TIMEOUT seconds,
     preventing infinite loops.
  4. stdout/stderr capture — output is returned as a string, never written
     directly to the terminal.

NOTE: For a production system, use Docker or gVisor for full sandboxing.
"""

import subprocess
import sys
import tempfile
import os
import re

# How long (in seconds) to allow code to run before killing it
EXECUTION_TIMEOUT = 10

# Patterns that indicate dangerous operations — refuse to execute if found.
# Each entry is a (regex_pattern, human_readable_reason) tuple.
BLOCKED_PATTERNS = [
    # File system writes / deletes
    (r"\bopen\s*\(.*['\"]w['\"]", "writing to files"),
    (r"\bopen\s*\(.*['\"]a['\"]", "appending to files"),
    (r"\bos\.remove\b", "deleting files (os.remove)"),
    (r"\bos\.unlink\b", "deleting files (os.unlink)"),
    (r"\bshutil\.rmtree\b", "deleting directories (shutil.rmtree)"),
    (r"\bshutil\.move\b", "moving files (shutil.move)"),
    (r"\bshutil\.copy\b", "copying files (shutil.copy)"),
    # Shell / system access
    (r"\bos\.system\b", "running shell commands (os.system)"),
    (r"\bos\.popen\b", "running shell commands (os.popen)"),
    (r"\bsubprocess\b", "spawning subprocesses"),
    (r"\beval\s*\(", "dynamic code evaluation (eval)"),
    (r"\bexec\s*\(", "dynamic code execution (exec)"),
    # Network access
    (r"\bimport\s+requests\b", "network requests (requests)"),
    (r"\bimport\s+urllib\b", "network requests (urllib)"),
    (r"\bimport\s+socket\b", "raw network sockets"),
    (r"\bimport\s+http\b", "HTTP connections"),
    (r"\bimport\s+ftplib\b", "FTP connections"),
    (r"\bimport\s+smtplib\b", "sending emails (smtplib)"),
    # System introspection / privilege escalation
    (r"\b__import__\s*\(", "dynamic imports (__import__)"),
    (r"\bimport\s+ctypes\b", "low-level C bindings (ctypes)"),
    (r"\bimport\s+multiprocessing\b", "spawning processes (multiprocessing)"),
    (r"\bimport\s+threading\b", "threading"),
]


def check_for_dangerous_patterns(code: str) -> tuple[bool, str]:
    """
    Scan the code string for dangerous patterns.

    Returns:
        (is_safe, reason) — if is_safe is False, reason explains what was found.
    """
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            return False, reason
    return True, ""


def execute_code(code: str) -> dict:
    """
    Execute a Python code string safely in a subprocess.

    Args:
        code: A string of Python source code to run.

    Returns:
        A dict with keys:
            'success'  (bool)   — True if code ran without error
            'stdout'   (str)    — Captured standard output
            'stderr'   (str)    — Captured standard error / exception text
            'blocked'  (bool)   — True if execution was refused due to safety
            'message'  (str)    — Human-readable status message
    """
    result = {
        "success": False,
        "stdout": "",
        "stderr": "",
        "blocked": False,
        "message": "",
    }

    # --- Step 1: Safety scan ---
    is_safe, danger_reason = check_for_dangerous_patterns(code)
    if not is_safe:
        result["blocked"] = True
        result["message"] = (
            f"Execution blocked for safety: the code contains {danger_reason}. "
            "This operation is not allowed in the sandbox."
        )
        return result

    # --- Step 2: Write code to a temp file ---
    # Using a temp file is cleaner than passing code via stdin —
    # it avoids shell escaping issues and gives proper tracebacks with line numbers.
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
            encoding="utf-8"
        ) as tmp:
            tmp.write(code)
            tmp_path = tmp.name
    except Exception as e:
        result["message"] = f"Failed to create temporary file: {str(e)}"
        return result

    # --- Step 3: Run in subprocess ---
    try:
        proc = subprocess.run(
            [sys.executable, tmp_path],   # Use the same Python interpreter running Streamlit
            capture_output=True,           # Capture both stdout and stderr
            text=True,                     # Decode output as UTF-8 text
            timeout=EXECUTION_TIMEOUT,     # Kill after timeout seconds
        )

        result["stdout"] = proc.stdout.strip()
        result["stderr"] = proc.stderr.strip()
        result["success"] = proc.returncode == 0

        if result["success"]:
            result["message"] = "Code executed successfully."
        else:
            result["message"] = "Code ran but exited with an error. See the error output below."

    except subprocess.TimeoutExpired:
        result["message"] = (
            f"Execution timed out after {EXECUTION_TIMEOUT} seconds. "
            "The code may contain an infinite loop or a very slow operation."
        )

    except Exception as e:
        result["message"] = f"Unexpected error during execution: {str(e)}"

    finally:
        # Always clean up the temp file
        try:
            os.unlink(tmp_path)
        except Exception:
            pass  # Not critical if cleanup fails

    return result
