"""
root_cause.py
-------------
Combine traceback data + AST analysis to produce a structured root-cause
analysis — entirely deterministic, no external AI API required.

The analysis works by matching the exception type (and optionally the error
message) against a lookup table of known patterns, then enriching the result
with file/line/function context from the traceback and AST.

Public API
----------
analyze(source: str, traceback_text: str) -> RootCauseResult
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from engine.traceback_parser import parse_traceback, ParsedTraceback
from engine.ast_analyzer import analyze_source, find_context_at_line, SourceAnalysis


# ── Result model ──────────────────────────────────────────────────────────────

@dataclass
class RootCauseResult:
    """Structured root-cause analysis."""
    error_type: str
    error_message: str
    affected_function: Optional[str]
    affected_line: Optional[int]
    affected_file: Optional[str]
    root_cause: str          # short one-liner cause
    explanation: str         # detailed human-readable explanation
    confidence: float        # 0.0 – 1.0

    def to_dict(self) -> dict:
        return {
            "error_type": self.error_type,
            "error_message": self.error_message,
            "affected_function": self.affected_function,
            "affected_line": self.affected_line,
            "affected_file": self.affected_file,
            "root_cause": self.root_cause,
            "explanation": self.explanation,
            "confidence": self.confidence,
        }


# ── Pattern database ──────────────────────────────────────────────────────────
# Each entry: (exception_type, optional_message_regex, root_cause, explanation, confidence)

_PATTERNS: list[tuple[str, Optional[str], str, str, float]] = [
    # ── NameError ─────────────────────────────────────────────────────────────
    (
        "NameError",
        r"name '(?P<name>.+)' is not defined",
        "Undefined variable or name",
        "A variable or function called '{name}' is used before it is defined. "
        "Check for typos, missing imports, or incorrect scope.",
        0.92,
    ),
    (
        "NameError",
        None,
        "Undefined name",
        "A name (variable, function, or class) is referenced before being defined. "
        "Check spelling, scope, and imports.",
        0.75,
    ),
    # ── AttributeError ────────────────────────────────────────────────────────
    (
        "AttributeError",
        r"'(?P<obj_type>.+)' object has no attribute '(?P<attr>.+)'",
        "Attribute does not exist on object",
        "You are trying to access attribute '{attr}' on a '{obj_type}' object, "
        "but that attribute does not exist. Check the object's type and spelling.",
        0.90,
    ),
    (
        "AttributeError",
        r"'NoneType' object has no attribute",
        "None returned where object expected",
        "An expression evaluated to None and you tried to access a method or "
        "attribute on it. Check that the function/method returns a value and "
        "that you are not missing a return statement.",
        0.88,
    ),
    (
        "AttributeError",
        None,
        "Attribute error",
        "An attribute access failed. The object may be the wrong type or None.",
        0.65,
    ),
    # ── TypeError ─────────────────────────────────────────────────────────────
    (
        "TypeError",
        r"unsupported operand type\(s\) for (?P<op>.+): '(?P<t1>.+)' and '(?P<t2>.+)'",
        "Incompatible types in operation",
        "Operator '{op}' cannot be applied to types '{t1}' and '{t2}'. "
        "Ensure both operands are the same compatible type (e.g. both int, both str).",
        0.91,
    ),
    (
        "TypeError",
        r"(?P<func>.+)\(\) takes (?P<exp>.+) argument",
        "Wrong number of arguments",
        "Function '{func}' was called with the wrong number of arguments. "
        "Check the function signature and the call site.",
        0.88,
    ),
    (
        "TypeError",
        r"'(?P<obj_type>.+)' object is not iterable",
        "Non-iterable used in iteration",
        "'{obj_type}' is not iterable. Only sequences (list, tuple, str, etc.) "
        "or objects implementing __iter__ can be used in a for-loop or unpacking.",
        0.87,
    ),
    (
        "TypeError",
        r"'(?P<obj_type>.+)' object is not callable",
        "Non-callable object called",
        "You are trying to call '{obj_type}' as if it were a function. "
        "Check that the name refers to a function, not a variable holding a value.",
        0.87,
    ),
    (
        "TypeError",
        None,
        "Type mismatch",
        "An operation was attempted on an incompatible type. Review the types "
        "of the variables involved.",
        0.65,
    ),
    # ── IndexError ────────────────────────────────────────────────────────────
    (
        "IndexError",
        r"list index out of range",
        "List index out of range",
        "You are accessing an index that does not exist in the list. "
        "Check the list length and the index value, especially in loops.",
        0.93,
    ),
    (
        "IndexError",
        None,
        "Sequence index out of range",
        "An index access went beyond the sequence's length.",
        0.80,
    ),
    # ── KeyError ──────────────────────────────────────────────────────────────
    (
        "KeyError",
        r"'?(?P<key>[^']+)'?",
        "Missing dictionary key",
        "Key '{key}' does not exist in the dictionary. "
        "Use dict.get(key) for a safe lookup or check with 'key in dict'.",
        0.88,
    ),
    (
        "KeyError",
        None,
        "Missing dictionary key",
        "The key you are looking up does not exist in the dictionary.",
        0.75,
    ),
    # ── ValueError ────────────────────────────────────────────────────────────
    (
        "ValueError",
        r"invalid literal for int\(\) with base \d+: '(?P<val>.+)'",
        "Cannot convert string to integer",
        "The string '{val}' cannot be converted to an integer. "
        "Ensure the string contains only digits (and optionally a sign).",
        0.93,
    ),
    (
        "ValueError",
        None,
        "Invalid value",
        "A function received an argument with the right type but an inappropriate value.",
        0.65,
    ),
    # ── ZeroDivisionError ─────────────────────────────────────────────────────
    (
        "ZeroDivisionError",
        None,
        "Division by zero",
        "An expression divides (or takes modulo) by zero. "
        "Add a guard: 'if divisor != 0:' before the operation.",
        0.95,
    ),
    # ── ImportError / ModuleNotFoundError ─────────────────────────────────────
    (
        "ModuleNotFoundError",
        r"No module named '(?P<mod>.+)'",
        "Missing Python module",
        "Module '{mod}' is not installed or not on sys.path. "
        "Install it with: pip install {mod}",
        0.95,
    ),
    (
        "ImportError",
        r"cannot import name '(?P<name>.+)' from '(?P<mod>.+)'",
        "Name not found in module",
        "'{name}' does not exist in module '{mod}'. "
        "Check the module's public API for the correct name.",
        0.90,
    ),
    (
        "ImportError",
        None,
        "Import failed",
        "An import statement failed. Check module name, installation, and sys.path.",
        0.70,
    ),
    # ── SyntaxError ───────────────────────────────────────────────────────────
    (
        "SyntaxError",
        None,
        "Python syntax error",
        "The code contains invalid Python syntax. "
        "Common causes: missing colon, unmatched brackets, bad indentation.",
        0.95,
    ),
    # ── IndentationError ──────────────────────────────────────────────────────
    (
        "IndentationError",
        None,
        "Incorrect indentation",
        "A line is indented at the wrong level. "
        "Python uses indentation to define blocks — use consistent spaces (4 per level).",
        0.95,
    ),
    # ── RecursionError ────────────────────────────────────────────────────────
    (
        "RecursionError",
        None,
        "Infinite recursion",
        "A function called itself too many times (exceeded Python's recursion limit). "
        "Check for a missing base case in a recursive function.",
        0.93,
    ),
    # ── FileNotFoundError ─────────────────────────────────────────────────────
    (
        "FileNotFoundError",
        r"\[Errno 2\] No such file or directory: '(?P<path>.+)'",
        "File not found",
        "The file or directory '{path}' does not exist. "
        "Check the path, working directory, and whether the file was created.",
        0.95,
    ),
    (
        "FileNotFoundError",
        None,
        "File not found",
        "A file operation failed because the path does not exist.",
        0.80,
    ),
    # ── AssertionError ────────────────────────────────────────────────────────
    (
        "AssertionError",
        None,
        "Assertion failed",
        "An assert statement evaluated to False. "
        "The condition the code assumed to be true was not met.",
        0.85,
    ),
    # ── StopIteration ─────────────────────────────────────────────────────────
    (
        "StopIteration",
        None,
        "Iterator exhausted",
        "next() was called on an iterator that has no more items. "
        "Check loop logic or use a default value: next(it, default).",
        0.80,
    ),
    # ── OverflowError ─────────────────────────────────────────────────────────
    (
        "OverflowError",
        None,
        "Numeric overflow",
        "A numeric operation produced a value too large to represent. "
        "Consider using Python's arbitrary-precision integers or reducing the input.",
        0.85,
    ),
    # ── MemoryError ───────────────────────────────────────────────────────────
    (
        "MemoryError",
        None,
        "Out of memory",
        "The program ran out of available memory. "
        "This can happen with very large data structures or infinite loops building a list.",
        0.80,
    ),
    # ── Exception (generic fallback) ──────────────────────────────────────────
    (
        "Exception",
        None,
        "Unhandled exception",
        "An exception was raised and not caught. "
        "Review the traceback to find the specific cause.",
        0.40,
    ),
]


def _match_patterns(
    exc_type: str, message: str
) -> tuple[str, str, float]:
    """
    Return (root_cause, explanation, confidence) for the best matching pattern.
    Substitutes named capture groups into the explanation template.
    """
    for pattern_type, msg_re, cause, explanation, confidence in _PATTERNS:
        if pattern_type != exc_type:
            continue
        if msg_re is None:
            # Generic match for this exception type — but keep searching for a
            # more specific match first.
            generic_cause, generic_explanation, generic_confidence = cause, explanation, confidence
            continue
        m = re.search(msg_re, message)
        if m:
            groups = m.groupdict()
            # Fill in named groups into the explanation template
            try:
                filled = explanation.format(**groups)
            except KeyError:
                filled = explanation
            return cause, filled, confidence
    else:
        # Fall through: use last generic match for this type, or ultimate fallback
        pass

    # Try generic match (second pass — find first generic entry for this type)
    for pattern_type, msg_re, cause, explanation, confidence in _PATTERNS:
        if pattern_type == exc_type and msg_re is None:
            return cause, explanation, confidence

    # Ultimate fallback
    return (
        f"Unhandled {exc_type}",
        f"A {exc_type} was raised: {message}",
        0.30,
    )


# ── Public API ────────────────────────────────────────────────────────────────

def analyze(source: str, traceback_text: str) -> RootCauseResult:
    """
    Produce a structured root-cause analysis.

    Parameters
    ----------
    source : str
        The Python source code being debugged (may be empty "").
    traceback_text : str
        The raw Python traceback string.

    Returns
    -------
    RootCauseResult
    """
    tb: ParsedTraceback = parse_traceback(traceback_text)
    ast_info: SourceAnalysis = analyze_source(source) if source.strip() else SourceAnalysis()

    # Determine affected location from traceback's innermost frame
    affected_function: Optional[str] = None
    affected_line: Optional[int] = None
    affected_file: Optional[str] = None

    if tb.last_frame:
        affected_line = tb.last_frame.lineno
        affected_file = tb.last_frame.filename
        # If the frame says "<module>" fall back to AST context
        if tb.last_frame.function and tb.last_frame.function != "<module>":
            affected_function = tb.last_frame.function
        elif source.strip() and affected_line:
            ctx = find_context_at_line(source, affected_line)
            affected_function = ctx.enclosing_function

    # Pattern-match against exception type + message
    root_cause, explanation, confidence = _match_patterns(
        tb.exception_type, tb.error_message
    )

    # Boost confidence slightly when AST also confirms the function is present
    if affected_function and any(f.name == affected_function for f in ast_info.functions):
        confidence = min(1.0, confidence + 0.03)

    return RootCauseResult(
        error_type=tb.exception_type or "UnknownError",
        error_message=tb.error_message,
        affected_function=affected_function,
        affected_line=affected_line,
        affected_file=affected_file,
        root_cause=root_cause,
        explanation=explanation,
        confidence=round(confidence, 2),
    )
