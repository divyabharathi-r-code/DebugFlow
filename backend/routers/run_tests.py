"""
POST /run-tests
Accepts a test code string, writes it to a temporary file, and runs it
with pytest in a subprocess sandbox.
Returns pass/fail information and captured output.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from engine.sandbox_runner import run_tests

router = APIRouter()


# ── Request / Response models ──────────────────────────────────────────────────

class RunTestsRequest(BaseModel):
    """
    Payload for POST /run-tests.

    test_code : str — pytest-compatible Python test source code
    timeout   : int — maximum seconds to allow (default 30)
    """
    test_code: str
    timeout: int = 30


class RunTestsResponse(BaseModel):
    status: str
    passed: bool
    timed_out: bool
    returncode: int
    stdout: str
    stderr: str
    tests_total: int
    tests_passed: int
    tests_failed: int
    tests_errors: int
    summary: str


# ── Route ─────────────────────────────────────────────────────────────────────

@router.post("", response_model=RunTestsResponse)
def run_tests_endpoint(payload: RunTestsRequest) -> RunTestsResponse:
    """
    Run a pytest test string in the sandbox and return results.

    The test code is written to a temporary file and executed via subprocess.
    shell=True is never used.
    """
    result = run_tests(payload.test_code, timeout=payload.timeout)

    return RunTestsResponse(
        status="ok",
        passed=result.passed,
        timed_out=result.timed_out,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
        tests_total=result.tests_total,
        tests_passed=result.tests_passed,
        tests_failed=result.tests_failed,
        tests_errors=result.tests_errors,
        summary=result.summary,
    )
