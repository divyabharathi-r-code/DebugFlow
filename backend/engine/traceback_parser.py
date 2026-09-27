"""
traceback_parser.py
-------------------
Parse a Python traceback string into structured data.

Supports the standard Python traceback format:

    Traceback (most recent call last):
      File "path/to/file.py", line 10, in some_function
        problematic_code()
    ExceptionType: error message

Returns a ParsedTraceback dict with fields:
  - exception_type  (str)
  - error_message   (str)
  - frames          (list of FrameInfo dicts)
  - last_frame      (FrameInfo | None) — the innermost relevant frame
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class FrameInfo:
    """One entry from the traceback call stack."""
    filename: str
    lineno: int
    function: str
    source_line: Optional[str] = None   # the actual code line shown in the tb


@dataclass
class ParsedTraceback:
    """Structured representation of a Python traceback."""
    exception_type: str = ""
    error_message: str = ""
    frames: list[FrameInfo] = field(default_factory=list)
    raw: str = ""

    @property
    def last_frame(self) -> Optional[FrameInfo]:
        """Return the innermost (most relevant) frame, if any."""
        return self.frames[-1] if self.frames else None

    def to_dict(self) -> dict:
        return {
            "exception_type": self.exception_type,
            "error_message": self.error_message,
            "frames": [
                {
                    "filename": f.filename,
                    "lineno": f.lineno,
                    "function": f.function,
                    "source_line": f.source_line,
                }
                for f in self.frames
            ],
            "last_frame": (
                {
                    "filename": self.last_frame.filename,
                    "lineno": self.last_frame.lineno,
                    "function": self.last_frame.function,
                    "source_line": self.last_frame.source_line,
                }
                if self.last_frame
                else None
            ),
        }


# ── Regex patterns ─────────────────────────────────────────────────────────────

# Matches:  File "foo.py", line 42, in bar
_FRAME_RE = re.compile(
    r'File "(?P<filename>[^"]+)",\s+line\s+(?P<lineno>\d+),\s+in\s+(?P<function>\S+)'
)

# Matches the last line: ExceptionType: message  (or just ExceptionType)
_EXCEPTION_RE = re.compile(
    r'^(?P<exc_type>[A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception|Warning|KeyboardInterrupt|StopIteration|GeneratorExit|BaseException|[A-Z][a-z]+)*)\s*:\s*(?P<msg>.+)$'
)

# Fallback: bare exception name with no colon
_BARE_EXCEPTION_RE = re.compile(r'^(?P<exc_type>[A-Za-z_][A-Za-z0-9_.]+)$')


# ── Public API ─────────────────────────────────────────────────────────────────

def parse_traceback(traceback_text: str) -> ParsedTraceback:
    """
    Parse a raw Python traceback string.

    Parameters
    ----------
    traceback_text : str
        The full traceback as a string (copied from a terminal or pytest output).

    Returns
    -------
    ParsedTraceback
        Structured object with exception type, message, and call-stack frames.
    """
    result = ParsedTraceback(raw=traceback_text.strip())
    lines = traceback_text.splitlines()

    i = 0
    while i < len(lines):
        line = lines[i]
        frame_match = _FRAME_RE.search(line)
        if frame_match:
            filename = frame_match.group("filename")
            lineno = int(frame_match.group("lineno"))
            function = frame_match.group("function")
            # The next line (if present and indented) is the source code snippet
            source_line: Optional[str] = None
            if i + 1 < len(lines) and lines[i + 1].startswith("    ") and not _FRAME_RE.search(lines[i + 1]):
                source_line = lines[i + 1].strip()
                i += 1  # consume the source line too
            result.frames.append(FrameInfo(filename=filename, lineno=lineno, function=function, source_line=source_line))
        else:
            # Try to match the exception line (usually the last meaningful line)
            stripped = line.strip()
            exc_match = _EXCEPTION_RE.match(stripped)
            if exc_match:
                result.exception_type = exc_match.group("exc_type")
                result.error_message = exc_match.group("msg").strip()
            else:
                bare = _BARE_EXCEPTION_RE.match(stripped)
                if bare:
                    result.exception_type = bare.group("exc_type")
                    result.error_message = ""
        i += 1

    return result
