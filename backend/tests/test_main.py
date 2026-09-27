"""
Smoke / integration tests for the FastAPI backend.
Verifies that the app starts, health endpoint works, and all routes
return the correct top-level shape with the real engine wired up.
"""

from fastapi.testclient import TestClient
import sys
import os

# Allow imports from backend/ when running pytest from the repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app

client = TestClient(app)

BUGGY_SOURCE = """\
def calculate_average(numbers):
    total = sum(numbers)
    count = len(numbers)
    return total / count
"""

ZERO_DIV_TRACEBACK = """\
Traceback (most recent call last):
  File "demo/buggy_sample.py", line 4, in calculate_average
    return total / count
ZeroDivisionError: division by zero
"""

PASSING_TEST_CODE = """\
def test_addition():
    assert 1 + 1 == 2
"""


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_returns_ok():
    response = client.post(
        "/analyze",
        json={"code": BUGGY_SOURCE, "error": ZERO_DIV_TRACEBACK},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "root_cause" in body
    assert "traceback" in body
    assert body["root_cause"]["error_type"] == "ZeroDivisionError"


def test_analyze_root_cause_confidence():
    response = client.post(
        "/analyze",
        json={"code": BUGGY_SOURCE, "error": ZERO_DIV_TRACEBACK},
    )
    rc = response.json()["root_cause"]
    assert rc["confidence"] >= 0.9


def test_fix_returns_ok():
    # First analyze, then ask for a fix
    analyze_resp = client.post(
        "/analyze",
        json={"code": BUGGY_SOURCE, "error": ZERO_DIV_TRACEBACK},
    )
    root_cause = analyze_resp.json()["root_cause"]

    fix_resp = client.post(
        "/fix",
        json={"code": BUGGY_SOURCE, "analysis": root_cause},
    )
    assert fix_resp.status_code == 200
    body = fix_resp.json()
    assert body["status"] == "ok"
    assert "diff" in body
    assert "fixed_code" in body
    assert "original_code" in body


def test_fix_does_not_auto_modify_source():
    """The fix endpoint must never modify the user's source automatically."""
    analyze_resp = client.post(
        "/analyze",
        json={"code": BUGGY_SOURCE, "error": ZERO_DIV_TRACEBACK},
    )
    root_cause = analyze_resp.json()["root_cause"]
    fix_resp = client.post(
        "/fix",
        json={"code": BUGGY_SOURCE, "analysis": root_cause},
    )
    # original_code must be returned unchanged
    assert fix_resp.json()["original_code"] == BUGGY_SOURCE


def test_run_tests_passing():
    response = client.post(
        "/run-tests",
        json={"test_code": PASSING_TEST_CODE},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["passed"] is True
    assert body["tests_passed"] >= 1


def test_run_tests_failing():
    failing_code = "def test_fail():\n    assert 1 == 2\n"
    response = client.post(
        "/run-tests",
        json={"test_code": failing_code},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is False


def test_report_stub():
    """Report endpoint (still stub) should still return 200."""
    response = client.post(
        "/report",
        json={"analysis": {}, "fix": {}, "test_result": {}},
    )
    assert response.status_code == 200
