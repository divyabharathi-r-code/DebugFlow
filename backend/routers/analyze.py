"""
POST /analyze
Accepts user-submitted Python source code and a traceback/error string.
Returns a full structured debugging analysis (traceback parse + AST + root cause).
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Any

from engine.traceback_parser import parse_traceback
from engine.ast_analyzer import analyze_source, find_context_at_line
from engine.root_cause import analyze as analyze_root_cause

router = APIRouter()


# ── Request / Response models ──────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    """
    Payload for POST /analyze.

    code : str  — the Python source code being debugged (may be empty)
    error : str — the raw traceback / error string
    """
    code: str
    error: str


class AnalyzeResponse(BaseModel):
    status: str
    traceback: dict
    ast: dict
    root_cause: dict


# ── Route ─────────────────────────────────────────────────────────────────────

@router.post("", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    """
    Analyze Python source code and a traceback.

    Steps:
      1. Parse the traceback into structured frames.
      2. Perform AST analysis of the source code.
      3. Derive root-cause analysis by combining both.
    """
    tb = parse_traceback(payload.error)
    ast_info = analyze_source(payload.code) if payload.code.strip() else None

    # If AST analysis found the affected line, add context snippet
    ast_dict: dict = ast_info.to_dict() if ast_info else {}
    if ast_info and tb.last_frame and tb.last_frame.lineno:
        ctx = find_context_at_line(payload.code, tb.last_frame.lineno)
        ast_dict["line_context"] = {
            "lineno": ctx.lineno,
            "enclosing_function": ctx.enclosing_function,
            "enclosing_function_start": ctx.enclosing_function_start,
            "is_in_function": ctx.is_in_function,
            "snippet": ctx.snippet,
        }

    rc = analyze_root_cause(payload.code, payload.error)

    return AnalyzeResponse(
        status="ok",
        traceback=tb.to_dict(),
        ast=ast_dict,
        root_cause=rc.to_dict(),
    )
