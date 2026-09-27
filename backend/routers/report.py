"""
POST /report
Assembles a final debugging session report from analysis, fix, and test results.
Returns a stub report — assembly logic will be wired in a later task.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ReportRequest(BaseModel):
    analysis: dict
    fix: dict
    test_result: dict


class ReportResponse(BaseModel):
    status: str
    message: str


@router.post("", response_model=ReportResponse)
def report(payload: ReportRequest) -> ReportResponse:
    """Stub: receive pipeline results, return placeholder report."""
    return ReportResponse(
        status="stub",
        message="Report generation not yet implemented.",
    )
