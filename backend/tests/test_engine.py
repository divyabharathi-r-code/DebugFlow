"""
test_engine.py
--------------
Unit tests for all five DebugFlow engine modules:
  - traceback_parser
  - ast_analyzer
  - root_cause
  - fix_generator
  - sandbox_runner

Run from the backend/ directory with:
    pytest tests/test_engine.py -v
"""

import sys
import os
import pytest

# Ensure the backend package root is on the path when running from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from engine.traceback_parser import parse_traceback, FrameInfo
from engine.ast_analyzer import analyze_source, find_context_at_line
from engine.root_cause import analyze as analyze_root_cause
from engine.fix_generator import generate_fix
from engine.sandbox_runner import run_tests as sandbox_run_tests


# ═══════════════════════════════════════════════════════════════════════════════
# traceback_parser tests
# ═══════════════════════════════════════════════════════════════════════════════

SAMPLE_TRACEBACK = """\
Traceback (most recent call last):
  File "demo/buggy_sample.py", line 23, in calculate_average
    return total / count
ZeroDivisionError: division by zero
"""

NAMEERROR_TRACEBACK = """\
Traceback (most recent call last):
  File "demo/buggy_sample.py", line 31, in get_item
    return f"Found: {reslt}"
NameError: name 'reslt' is not defined
"""

INDEX_TRACEBACK = """\
Traceback (most recent call last):
  File "demo/buggy_sample.py", line 37, in first_element
    return items[0]
IndexError: list index out of range
"""

MULTIFRAME_TRACEBACK = """\
Traceback (most recent call last):
  File "main.py", line 5, in <module>
    result = outer()
  File "main.py", line 3, in outer
    return inner()
  File "main.py", line 1, in inner
    return 1 / 0
ZeroDivisionError: division by zero
"""


class TestTracebackParser:

    def test_extracts_exception_type(self):
        result = parse_traceback(SAMPLE_TRACEBACK)
        assert result.exception_type == "ZeroDivisionError"

    def test_extracts_error_message(self):
        result = parse_traceback(SAMPLE_TRACEBACK)
        assert result.error_message == "division by zero"

    def test_extracts_frames(self):
        result = parse_traceback(SAMPLE_TRACEBACK)
        assert len(result.frames) == 1
        frame = result.frames[0]
        assert frame.filename == "demo/buggy_sample.py"
        assert frame.lineno == 23
        assert frame.function == "calculate_average"

    def test_last_frame_is_innermost(self):
        result = parse_traceback(MULTIFRAME_TRACEBACK)
        assert len(result.frames) == 3
        assert result.last_frame.function == "inner"
        assert result.last_frame.lineno == 1

    def test_source_line_captured(self):
        result = parse_traceback(SAMPLE_TRACEBACK)
        assert result.frames[0].source_line == "return total / count"

    def test_name_error(self):
        result = parse_traceback(NAMEERROR_TRACEBACK)
        assert result.exception_type == "NameError"
        assert "reslt" in result.error_message

    def test_index_error(self):
        result = parse_traceback(INDEX_TRACEBACK)
        assert result.exception_type == "IndexError"
        assert result.last_frame.function == "first_element"
        assert result.last_frame.lineno == 37

    def test_empty_string(self):
        result = parse_traceback("")
        assert result.exception_type == ""
        assert result.frames == []

    def test_to_dict_structure(self):
        result = parse_traceback(SAMPLE_TRACEBACK)
        d = result.to_dict()
        assert "exception_type" in d
        assert "error_message" in d
        assert "frames" in d
        assert "last_frame" in d
        assert d["last_frame"]["lineno"] == 23


# ═══════════════════════════════════════════════════════════════════════════════
# ast_analyzer tests
# ═══════════════════════════════════════════════════════════════════════════════

SAMPLE_SOURCE = """\
import os
from sys import argv

def greet(name: str) -> str:
    return f"Hello, {name}"

def add(a, b):
    return a + b

x = 10
"""

BUGGY_SOURCE = """\
def calculate_average(numbers):
    total = sum(numbers)
    count = len(numbers)
    return total / count

def get_item(data, key):
    result = data.get(key, "unknown")
    return f"Found: {reslt}"

def first_element(items):
    return items[0]
"""

SYNTAX_ERROR_SOURCE = "def bad_func(\n    print('oops')"


class TestAstAnalyzer:

    def test_extracts_functions(self):
        analysis = analyze_source(SAMPLE_SOURCE)
        names = [f.name for f in analysis.functions]
        assert "greet" in names
        assert "add" in names

    def test_function_args(self):
        analysis = analyze_source(SAMPLE_SOURCE)
        greet = next(f for f in analysis.functions if f.name == "greet")
        assert "name" in greet.args

    def test_function_line_numbers(self):
        analysis = analyze_source(SAMPLE_SOURCE)
        greet = next(f for f in analysis.functions if f.name == "greet")
        assert greet.start_line == 4
        assert greet.end_line >= 4

    def test_extracts_imports(self):
        analysis = analyze_source(SAMPLE_SOURCE)
        modules = [imp.module for imp in analysis.imports]
        assert "os" in modules
        assert "sys" in modules

    def test_from_import(self):
        analysis = analyze_source(SAMPLE_SOURCE)
        from_imports = [imp for imp in analysis.imports if imp.is_from]
        assert any("argv" in imp.names for imp in from_imports)

    def test_syntax_error_handled_gracefully(self):
        analysis = analyze_source(SYNTAX_ERROR_SOURCE)
        assert analysis.syntax_error is not None
        assert isinstance(analysis.syntax_error, str)

    def test_empty_source(self):
        analysis = analyze_source("")
        assert analysis.functions == []
        assert analysis.imports == []

    def test_to_dict_structure(self):
        analysis = analyze_source(SAMPLE_SOURCE)
        d = analysis.to_dict()
        assert "functions" in d
        assert "imports" in d
        assert "syntax_error" in d
        assert d["syntax_error"] is None

    def test_find_context_at_line_in_function(self):
        ctx = find_context_at_line(BUGGY_SOURCE, 8)  # line 8: return f"Found: {reslt}"
        assert ctx.enclosing_function == "get_item"
        assert ctx.is_in_function is True

    def test_find_context_snippet(self):
        ctx = find_context_at_line(BUGGY_SOURCE, 4)
        assert any("4" in line for line in ctx.snippet)

    def test_find_context_out_of_function(self):
        # Line 10 in SAMPLE_SOURCE: `x = 10` — top level
        ctx = find_context_at_line(SAMPLE_SOURCE, 10)
        assert ctx.is_in_function is False

    def test_buggy_functions_detected(self):
        analysis = analyze_source(BUGGY_SOURCE)
        names = [f.name for f in analysis.functions]
        assert set(names) == {"calculate_average", "get_item", "first_element"}


# ═══════════════════════════════════════════════════════════════════════════════
# root_cause tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestRootCause:

    def test_zero_division_detected(self):
        rc = analyze_root_cause(BUGGY_SOURCE, SAMPLE_TRACEBACK)
        assert rc.error_type == "ZeroDivisionError"
        assert rc.confidence >= 0.9
        assert "zero" in rc.root_cause.lower()

    def test_name_error_detected(self):
        rc = analyze_root_cause(BUGGY_SOURCE, NAMEERROR_TRACEBACK)
        assert rc.error_type == "NameError"
        assert "reslt" in rc.error_message or "reslt" in rc.explanation
        assert rc.confidence >= 0.85

    def test_index_error_detected(self):
        rc = analyze_root_cause(BUGGY_SOURCE, INDEX_TRACEBACK)
        assert rc.error_type == "IndexError"
        assert rc.confidence >= 0.8

    def test_affected_line_extracted(self):
        rc = analyze_root_cause(BUGGY_SOURCE, SAMPLE_TRACEBACK)
        assert rc.affected_line == 23  # from the traceback frame

    def test_affected_function_extracted(self):
        rc = analyze_root_cause(BUGGY_SOURCE, SAMPLE_TRACEBACK)
        assert rc.affected_function == "calculate_average"

    def test_to_dict_has_all_fields(self):
        rc = analyze_root_cause(BUGGY_SOURCE, SAMPLE_TRACEBACK)
        d = rc.to_dict()
        for key in ["error_type", "error_message", "affected_function",
                    "affected_line", "root_cause", "explanation", "confidence"]:
            assert key in d

    def test_empty_source_still_works(self):
        rc = analyze_root_cause("", SAMPLE_TRACEBACK)
        assert rc.error_type == "ZeroDivisionError"

    def test_unknown_exception_fallback(self):
        tb = "Traceback (most recent call last):\n  File \"x.py\", line 1, in f\n    boom()\nMyCustomError: something weird"
        rc = analyze_root_cause("", tb)
        assert rc.error_type == "MyCustomError"
        assert rc.confidence < 0.5


# ═══════════════════════════════════════════════════════════════════════════════
# fix_generator tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestFixGenerator:

    def _rc_dict(self, **kwargs) -> dict:
        base = {
            "error_type": "NameError",
            "error_message": "name 'reslt' is not defined",
            "affected_function": "get_item",
            "affected_line": 8,
            "affected_file": "demo/buggy_sample.py",
            "root_cause": "Undefined variable",
            "explanation": "reslt is not defined",
            "confidence": 0.92,
        }
        base.update(kwargs)
        return base

    def test_name_error_fix_inserts_stub(self):
        rc = self._rc_dict()
        result = generate_fix(BUGGY_SOURCE, rc)
        assert result.fix_available is True
        assert "reslt" in result.fixed_code
        assert "= None" in result.fixed_code

    def test_name_error_fix_diff_non_empty(self):
        rc = self._rc_dict()
        result = generate_fix(BUGGY_SOURCE, rc)
        assert result.diff != ""
        assert "@@" in result.diff

    def test_zero_division_fix(self):
        rc = self._rc_dict(
            error_type="ZeroDivisionError",
            error_message="division by zero",
            affected_function="calculate_average",
            affected_line=4,
        )
        result = generate_fix(BUGGY_SOURCE, rc)
        assert result.fix_available is True
        assert "!= 0" in result.fixed_code

    def test_index_error_fix(self):
        rc = self._rc_dict(
            error_type="IndexError",
            error_message="list index out of range",
            affected_function="first_element",
            affected_line=11,
        )
        result = generate_fix(BUGGY_SOURCE, rc)
        assert result.fix_available is True

    def test_source_file_not_modified(self):
        """The fix generator must return the original_code unchanged."""
        rc = self._rc_dict()
        result = generate_fix(BUGGY_SOURCE, rc)
        assert result.original_code == BUGGY_SOURCE

    def test_fix_result_has_all_fields(self):
        rc = self._rc_dict()
        result = generate_fix(BUGGY_SOURCE, rc)
        d = result.to_dict()
        for key in ["explanation", "proposed_change", "original_code",
                    "fixed_code", "diff", "fix_available"]:
            assert key in d

    def test_accepts_root_cause_result_object(self):
        # Use a traceback whose line number (8) exists in BUGGY_SOURCE (12 lines)
        tb_for_buggy = (
            'Traceback (most recent call last):\n'
            '  File "buggy_sample.py", line 8, in get_item\n'
            '    return f"Found: {reslt}"\n'
            "NameError: name 'reslt' is not defined\n"
        )
        rc_obj = analyze_root_cause(BUGGY_SOURCE, tb_for_buggy)
        result = generate_fix(BUGGY_SOURCE, rc_obj)
        assert result.fix_available is True

    def test_unknown_error_type_returns_no_fix(self):
        rc = self._rc_dict(error_type="SomeObscureError", error_message="something odd")
        result = generate_fix(BUGGY_SOURCE, rc)
        assert result.fix_available is False


# ═══════════════════════════════════════════════════════════════════════════════
# sandbox_runner tests
# ═══════════════════════════════════════════════════════════════════════════════

PASSING_TEST = """\
def test_addition():
    assert 1 + 1 == 2

def test_string():
    assert "hello".upper() == "HELLO"
"""

FAILING_TEST = """\
def test_this_will_fail():
    assert 1 == 2, "expected failure"
"""

SYNTAX_ERROR_TEST = """\
def test_bad_syntax(
    assert True
"""

EMPTY_TEST = """\
# No tests here
x = 1 + 1
"""


class TestSandboxRunner:

    def test_passing_tests_return_passed_true(self):
        result = sandbox_run_tests(PASSING_TEST)
        assert result.passed is True
        assert result.returncode == 0

    def test_passing_tests_count(self):
        result = sandbox_run_tests(PASSING_TEST)
        assert result.tests_passed == 2
        assert result.tests_failed == 0

    def test_failing_test_returns_passed_false(self):
        result = sandbox_run_tests(FAILING_TEST)
        assert result.passed is False
        assert result.tests_failed >= 1

    def test_stdout_captured(self):
        result = sandbox_run_tests(PASSING_TEST)
        assert isinstance(result.stdout, str)

    def test_stderr_captured(self):
        result = sandbox_run_tests(FAILING_TEST)
        assert isinstance(result.stderr, str)

    def test_syntax_error_test_fails(self):
        result = sandbox_run_tests(SYNTAX_ERROR_TEST)
        assert result.passed is False

    def test_empty_script_passes_zero_tests(self):
        result = sandbox_run_tests(EMPTY_TEST)
        # No pytest tests — may pass or fail depending on pytest exit code
        assert isinstance(result.tests_total, int)

    def test_to_dict_structure(self):
        result = sandbox_run_tests(PASSING_TEST)
        d = result.to_dict()
        for key in ["returncode", "stdout", "stderr", "passed", "timed_out",
                    "tests_total", "tests_passed", "tests_failed", "tests_errors", "summary"]:
            assert key in d

    def test_summary_non_empty(self):
        result = sandbox_run_tests(PASSING_TEST)
        assert result.summary != ""

    def test_timeout_parameter_accepted(self):
        # Should not raise — just verify the parameter is accepted
        result = sandbox_run_tests(PASSING_TEST, timeout=60)
        assert result.passed is True
