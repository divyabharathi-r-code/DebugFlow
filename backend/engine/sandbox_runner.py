"""
sandbox_runner.py
-----------------
Run Python test files safely using subprocess.

Design principles
-----------------
- NEVER uses shell=True (prevents shell-injection attacks).
- Runs with a configurable timeout (default 30 s) to stop runaway processes.
- Captures stdout, stderr, and return code.
- Writes test code to a temporary file — never exec()s arbitrary strings.
- Returns structured output suitable for later replacement with a
  stronger container-based sandbox.

Public API
----------
run_tests(test_code: str, timeout: int = 30) -> SandboxResult
run_file(filepath: str, timeout: int = 30) -> SandboxResult
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ── Result model ──────────────────────────────────────────────────────────────

@dataclass
class SandboxResult:
    """Result of running a test file in the sandbox."""
    returncode: int
    stdout: str
    stderr: str
    passed: bool                     # True when returncode == 0
    timed_out: bool = False
    tests_total: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    tests_errors: int = 0
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "passed": self.passed,
            "timed_out": self.timed_out,
            "tests_total": self.tests_total,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "tests_errors": self.tests_errors,
            "summary": self.summary,
        }


# ── pytest output parser ──────────────────────────────────────────────────────

def _parse_pytest_output(stdout: str, stderr: str) -> dict:
    """
    Extract numeric test counts from pytest's summary line.

    Handles lines like:
      "5 passed", "3 failed, 2 passed", "1 error", "2 passed, 1 warning"
    """
    combined = stdout + "\n" + stderr
    totals = {"passed": 0, "failed": 0, "error": 0}

    # Match patterns like "3 passed" or "1 failed" in the summary line
    for key in totals:
        m = re.search(rf'(\d+)\s+{key}', combined)
        if m:
            totals[key] = int(m.group(1))

    total = totals["passed"] + totals["failed"] + totals["error"]
    return {
        "tests_total": total,
        "tests_passed": totals["passed"],
        "tests_failed": totals["failed"],
        "tests_errors": totals["error"],
    }


def _build_summary(result: SandboxResult) -> str:
    """Build a one-line human-readable summary."""
    if result.timed_out:
        return "Test run timed out."
    if result.tests_total == 0:
        if result.passed:
            return "Script ran successfully (no pytest tests detected)."
        return "Script exited with errors (no pytest tests detected)."
    parts = []
    if result.tests_passed:
        parts.append(f"{result.tests_passed} passed")
    if result.tests_failed:
        parts.append(f"{result.tests_failed} failed")
    if result.tests_errors:
        parts.append(f"{result.tests_errors} error(s)")
    return ", ".join(parts) + f" — {'PASS' if result.passed else 'FAIL'}"


# ── Core execution ────────────────────────────────────────────────────────────

def _run_python_file(filepath: str, timeout: int) -> SandboxResult:
    """
    Execute a Python file using the current interpreter and pytest.

    Uses sys.executable so it always stays in the same virtual environment.
    Never uses shell=True.
    """
    cmd = [sys.executable, "-m", "pytest", filepath, "-v", "--tb=short", "--no-header"]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,  # explicit — never True
        )
    except subprocess.TimeoutExpired:
        return SandboxResult(
            returncode=-1,
            stdout="",
            stderr=f"Test run timed out after {timeout} seconds.",
            passed=False,
            timed_out=True,
            summary=f"Test run timed out after {timeout} seconds.",
        )
    except FileNotFoundError as exc:
        return SandboxResult(
            returncode=-1,
            stdout="",
            stderr=str(exc),
            passed=False,
            summary=f"Could not start Python: {exc}",
        )

    counts = _parse_pytest_output(proc.stdout, proc.stderr)
    passed = proc.returncode == 0

    result = SandboxResult(
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        passed=passed,
        tests_total=counts["tests_total"],
        tests_passed=counts["tests_passed"],
        tests_failed=counts["tests_failed"],
        tests_errors=counts["tests_errors"],
    )
    result.summary = _build_summary(result)
    return result


# ── Public API ────────────────────────────────────────────────────────────────

def run_tests(test_code: str, timeout: int = 30) -> SandboxResult:
    """
    Write `test_code` to a temporary file and run it with pytest.

    Parameters
    ----------
    test_code : str
        Python test source code (pytest style).
    timeout : int
        Maximum seconds to wait for the test run (default 30).

    Returns
    -------
    SandboxResult
    """
    # Write to a secure temporary file
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        prefix="debugflow_test_",
        delete=False,
        encoding="utf-8",
    ) as tmp:
        tmp.write(test_code)
        tmp_path = tmp.name

    try:
        return _run_python_file(tmp_path, timeout)
    finally:
        # Always clean up the temporary file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def run_file(filepath: str, timeout: int = 30) -> SandboxResult:
    """
    Run an existing Python test file with pytest.

    Parameters
    ----------
    filepath : str
        Absolute or relative path to an existing .py test file.
    timeout : int
        Maximum seconds to wait (default 30).

    Returns
    -------
    SandboxResult
    """
    if not Path(filepath).is_file():
        return SandboxResult(
            returncode=-1,
            stdout="",
            stderr=f"File not found: {filepath}",
            passed=False,
            summary=f"File not found: {filepath}",
        )
    return _run_python_file(filepath, timeout)
