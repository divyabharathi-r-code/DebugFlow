"""
POST /fix
Accepts Python source code and a root-cause analysis dict.
Returns a proposed minimal fix and unified diff.
Does NOT automatically modify the user's source file.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Any

from engine.fix_generator import generate_fix

router = APIRouter()


# ── Request / Response models ──────────────────────────────────────────────────

class FixRequest(BaseModel):
    """
    Payload for POST /fix.

    code     : str  — the Python source code to fix
    analysis : dict — the root_cause dict from POST /analyze response
    """
    code: str
    analysis: dict


class FixResponse(BaseModel):
    status: str
    explanation: str
    proposed_change: str
    original_code: str
    fixed_code: str
    diff: str
    fix_available: bool


# ── Route ─────────────────────────────────────────────────────────────────────

@router.post("", response_model=FixResponse)
def fix(payload: FixRequest) -> FixResponse:
    """
    Generate a proposed fix based on root-cause analysis.

    The response contains the proposed fixed code and a diff.
    The original file is NEVER modified automatically.
    """
    result = generate_fix(payload.code, payload.analysis)

    return FixResponse(
        status="ok",
        explanation=result.explanation,
        proposed_change=result.proposed_change,
        original_code=result.original_code,
        fixed_code=result.fixed_code,
        diff=result.diff,
        fix_available=result.fix_available,
    )
