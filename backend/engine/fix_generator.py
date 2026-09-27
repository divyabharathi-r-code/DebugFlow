"""
fix_generator.py
----------------
Generate a proposed minimal fix for a detected bug — entirely deterministic.

This module does NOT modify the user's source file. It only returns a proposed
change as structured data, leaving the decision to apply it to the user.

Public API
----------
generate_fix(source: str, root_cause_result: dict | RootCauseResult) -> FixResult
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from typing import Optional

from engine.root_cause import RootCauseResult


# ── Result model ──────────────────────────────────────────────────────────────

@dataclass
class FixResult:
    """A proposed fix for a detected bug."""
    explanation: str            # Human-readable description of what to change and why
    proposed_change: str        # Short natural-language description of the change
    original_code: str          # The original code snippet (or full source)
    fixed_code: str             # The proposed fixed code snippet (or full source)
    diff: str                   # Unified diff between original and fixed code
    fix_available: bool = True  # False when the engine cannot suggest a fix

    def to_dict(self) -> dict:
        return {
            "explanation": self.explanation,
            "proposed_change": self.proposed_change,
            "original_code": self.original_code,
            "fixed_code": self.fixed_code,
            "diff": self.diff,
            "fix_available": self.fix_available,
        }


# ── Diff helper ───────────────────────────────────────────────────────────────

def _make_diff(original: str, fixed: str, filename: str = "source.py") -> str:
    """Return a unified diff string between two code strings."""
    original_lines = original.splitlines(keepends=True)
    fixed_lines = fixed.splitlines(keepends=True)
    diff = difflib.unified_diff(
        original_lines,
        fixed_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm="",
    )
    return "\n".join(diff)


def _no_fix(source: str, reason: str) -> FixResult:
    """Return a FixResult indicating no automatic fix is available."""
    return FixResult(
        explanation=reason,
        proposed_change="No automatic fix available.",
        original_code=source,
        fixed_code=source,
        diff="",
        fix_available=False,
    )


# ── Fix strategies ────────────────────────────────────────────────────────────

def _fix_name_error(source: str, rc: RootCauseResult) -> FixResult:
    """
    NameError: name 'X' is not defined
    Strategy: Check if 'X' looks like a common builtin that was shadowed,
    or insert a comment stub declaring the variable before first use.
    """
    # Extract the undefined name from the error message
    m = re.search(r"name '(.+?)' is not defined", rc.error_message)
    if not m:
        return _no_fix(source, "Could not extract the undefined name from the error message.")

    undefined_name = m.group(1)
    lines = source.splitlines()

    if rc.affected_line is None or rc.affected_line > len(lines):
        return _no_fix(source, "Could not locate the affected line in the source.")

    affected_idx = rc.affected_line - 1  # 0-based
    affected_line_text = lines[affected_idx]

    # Determine indentation of the affected line
    indent = len(affected_line_text) - len(affected_line_text.lstrip())
    stub = " " * indent + f"{undefined_name} = None  # TODO: assign a proper value"

    # Insert the stub one line before the error line
    fixed_lines = lines[:affected_idx] + [stub] + lines[affected_idx:]
    fixed_source = "\n".join(fixed_lines)

    return FixResult(
        explanation=(
            f"'{undefined_name}' is used on line {rc.affected_line} but was never assigned. "
            "A stub assignment has been inserted above that line. "
            "Replace `None` with the correct value."
        ),
        proposed_change=f"Insert `{undefined_name} = None  # TODO: assign a proper value` before line {rc.affected_line}.",
        original_code=source,
        fixed_code=fixed_source,
        diff=_make_diff(source, fixed_source),
    )


def _fix_index_error(source: str, rc: RootCauseResult) -> FixResult:
    """
    IndexError: list index out of range
    Strategy: Wrap the problematic access in a bounds check.
    """
    if rc.affected_line is None:
        return _no_fix(source, "Cannot locate the affected line for IndexError fix.")

    lines = source.splitlines()
    affected_idx = rc.affected_line - 1
    if affected_idx >= len(lines):
        return _no_fix(source, "Affected line number is out of bounds in source.")

    affected_line_text = lines[affected_idx]
    indent = " " * (len(affected_line_text) - len(affected_line_text.lstrip()))

    # Look for subscript patterns like: var[idx]
    subscript_re = re.compile(r'(\w+)\[(\w+)\]')
    sub_match = subscript_re.search(affected_line_text)
    if sub_match:
        seq_name = sub_match.group(1)
        idx_name = sub_match.group(2)
        guard = f"{indent}if {idx_name} < len({seq_name}):"
        guarded_line = f"{indent}    {affected_line_text.strip()}"
        else_line = f"{indent}else:"
        else_body = f'{indent}    pass  # TODO: handle out-of-range index'
        new_lines = (
            lines[:affected_idx]
            + [guard, guarded_line, else_line, else_body]
            + lines[affected_idx + 1:]
        )
    else:
        # Generic: just add a comment
        comment = f"{indent}# WARNING: potential IndexError on the next line — check bounds"
        new_lines = lines[:affected_idx] + [comment] + lines[affected_idx:]

    fixed_source = "\n".join(new_lines)
    return FixResult(
        explanation=(
            f"Line {rc.affected_line} accesses a sequence with an index that may be out of range. "
            "The fix wraps the access in a bounds check."
        ),
        proposed_change="Wrap the index access in a bounds-check guard.",
        original_code=source,
        fixed_code=fixed_source,
        diff=_make_diff(source, fixed_source),
    )


def _fix_type_error_operand(source: str, rc: RootCauseResult) -> FixResult:
    """
    TypeError: unsupported operand type(s) for X: 'Y' and 'Z'
    Strategy: Add int()/str() cast suggestion as a comment.
    """
    if rc.affected_line is None:
        return _no_fix(source, "Cannot locate the affected line for TypeError fix.")

    lines = source.splitlines()
    affected_idx = rc.affected_line - 1
    if affected_idx >= len(lines):
        return _no_fix(source, "Affected line number is out of bounds in source.")

    indent = " " * (len(lines[affected_idx]) - len(lines[affected_idx].lstrip()))
    comment = (
        f"{indent}# FIX: ensure both operands are the same type, e.g. use int() or str()"
    )
    new_lines = lines[:affected_idx] + [comment] + lines[affected_idx:]
    fixed_source = "\n".join(new_lines)

    return FixResult(
        explanation=(
            "A TypeError occurred because two incompatible types were used together. "
            "Convert the operands to the same type (e.g. int(x) + int(y) or str(x) + str(y))."
        ),
        proposed_change="Ensure operands share the same type before the operation.",
        original_code=source,
        fixed_code=fixed_source,
        diff=_make_diff(source, fixed_source),
    )


def _fix_zero_division(source: str, rc: RootCauseResult) -> FixResult:
    """
    ZeroDivisionError
    Strategy: Wrap in a conditional guard.
    """
    if rc.affected_line is None:
        return _no_fix(source, "Cannot locate the affected line for ZeroDivisionError fix.")

    lines = source.splitlines()
    affected_idx = rc.affected_line - 1
    if affected_idx >= len(lines):
        return _no_fix(source, "Affected line number is out of bounds in source.")

    affected_text = lines[affected_idx]
    indent = " " * (len(affected_text) - len(affected_text.lstrip()))

    # Try to detect the divisor name
    div_re = re.compile(r'/\s*(\w+)')
    div_match = div_re.search(affected_text)
    if div_match:
        divisor = div_match.group(1)
        guard = f"{indent}if {divisor} != 0:"
        guarded = f"{indent}    {affected_text.strip()}"
        else_block = f"{indent}else:"
        else_body = f'{indent}    pass  # TODO: handle division by zero'
        new_lines = (
            lines[:affected_idx]
            + [guard, guarded, else_block, else_body]
            + lines[affected_idx + 1:]
        )
    else:
        comment = f"{indent}# FIX: guard against division by zero before this line"
        new_lines = lines[:affected_idx] + [comment] + lines[affected_idx:]

    fixed_source = "\n".join(new_lines)
    return FixResult(
        explanation=(
            f"Line {rc.affected_line} performs a division that may divide by zero. "
            "The fix adds a guard to check the divisor is non-zero."
        ),
        proposed_change="Add `if divisor != 0:` guard before the division.",
        original_code=source,
        fixed_code=fixed_source,
        diff=_make_diff(source, fixed_source),
    )


def _fix_value_error_int(source: str, rc: RootCauseResult) -> FixResult:
    """
    ValueError: invalid literal for int()
    Strategy: Wrap conversion in try/except.
    """
    if rc.affected_line is None:
        return _no_fix(source, "Cannot locate the affected line for ValueError fix.")

    lines = source.splitlines()
    affected_idx = rc.affected_line - 1
    if affected_idx >= len(lines):
        return _no_fix(source, "Affected line number is out of bounds in source.")

    affected_text = lines[affected_idx]
    indent = " " * (len(affected_text) - len(affected_text.lstrip()))

    try_block = [
        f"{indent}try:",
        f"{indent}    {affected_text.strip()}",
        f"{indent}except ValueError:",
        f'{indent}    pass  # TODO: handle invalid integer conversion',
    ]
    new_lines = lines[:affected_idx] + try_block + lines[affected_idx + 1:]
    fixed_source = "\n".join(new_lines)

    return FixResult(
        explanation=(
            "int() was called with a string that cannot be parsed as an integer. "
            "The fix wraps the conversion in a try/except ValueError block."
        ),
        proposed_change="Wrap `int(...)` call in `try/except ValueError`.",
        original_code=source,
        fixed_code=fixed_source,
        diff=_make_diff(source, fixed_source),
    )


# ── Dispatch table ────────────────────────────────────────────────────────────

_FIXERS: dict[str, list[tuple[Optional[str], callable]]] = {
    "NameError": [(None, _fix_name_error)],
    "IndexError": [(None, _fix_index_error)],
    "TypeError": [
        (r"unsupported operand", _fix_type_error_operand),
    ],
    "ZeroDivisionError": [(None, _fix_zero_division)],
    "ValueError": [
        (r"invalid literal for int", _fix_value_error_int),
    ],
}


# ── Public API ────────────────────────────────────────────────────────────────

def generate_fix(
    source: str,
    root_cause: "RootCauseResult | dict",
) -> FixResult:
    """
    Generate a proposed minimal fix.

    Parameters
    ----------
    source : str
        The Python source code.
    root_cause : RootCauseResult or dict
        The result from root_cause.analyze().  May be passed as a dict
        (e.g. when coming from JSON deserialization).

    Returns
    -------
    FixResult
        A proposed fix. Does NOT modify the source file.
    """
    # Accept both RootCauseResult objects and plain dicts
    if isinstance(root_cause, dict):
        rc = RootCauseResult(
            error_type=root_cause.get("error_type", ""),
            error_message=root_cause.get("error_message", ""),
            affected_function=root_cause.get("affected_function"),
            affected_line=root_cause.get("affected_line"),
            affected_file=root_cause.get("affected_file"),
            root_cause=root_cause.get("root_cause", ""),
            explanation=root_cause.get("explanation", ""),
            confidence=root_cause.get("confidence", 0.0),
        )
    else:
        rc = root_cause

    fixers = _FIXERS.get(rc.error_type, [])
    for msg_pattern, fixer_fn in fixers:
        if msg_pattern is None or re.search(msg_pattern, rc.error_message, re.IGNORECASE):
            return fixer_fn(source, rc)

    # No specific fixer — return a general suggestion
    return FixResult(
        explanation=(
            f"Detected: {rc.error_type}: {rc.error_message}\n"
            f"Root cause: {rc.root_cause}\n\n"
            f"{rc.explanation}"
        ),
        proposed_change="Review the explanation above and apply the fix manually.",
        original_code=source,
        fixed_code=source,
        diff="",
        fix_available=False,
    )
