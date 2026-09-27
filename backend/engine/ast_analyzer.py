"""
ast_analyzer.py
---------------
Parse Python source code using the built-in `ast` module and extract
structural information useful for debugging.

Public API
----------
analyze_source(source: str) -> SourceAnalysis
    Full analysis of a source string.

find_context_at_line(source: str, lineno: int) -> LineContext
    Given a line number, return the enclosing function/class and nearby lines.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Optional


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class FunctionInfo:
    """Metadata about a top-level or nested function/method."""
    name: str
    start_line: int
    end_line: int
    args: list[str]          # argument names
    decorators: list[str]    # decorator names (as strings)


@dataclass
class ImportInfo:
    """One import statement found in the source."""
    module: str              # e.g. "os.path" or "sys"
    names: list[str]         # names imported, empty = import-all / module-level
    lineno: int
    is_from: bool            # True if `from X import Y`


@dataclass
class SourceAnalysis:
    """Full static analysis of a Python source string."""
    functions: list[FunctionInfo] = field(default_factory=list)
    imports: list[ImportInfo] = field(default_factory=list)
    syntax_error: Optional[str] = None   # non-None if the source couldn't be parsed
    top_level_statements: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "functions": [
                {
                    "name": f.name,
                    "start_line": f.start_line,
                    "end_line": f.end_line,
                    "args": f.args,
                    "decorators": f.decorators,
                }
                for f in self.functions
            ],
            "imports": [
                {
                    "module": imp.module,
                    "names": imp.names,
                    "lineno": imp.lineno,
                    "is_from": imp.is_from,
                }
                for imp in self.imports
            ],
            "syntax_error": self.syntax_error,
            "top_level_statements": self.top_level_statements,
        }


@dataclass
class LineContext:
    """Information about a specific line within a source file."""
    lineno: int
    enclosing_function: Optional[str]    # name of the function containing this line
    enclosing_function_start: Optional[int]
    snippet: list[str]                   # ±3 lines of context (line text, 1-indexed)
    is_in_function: bool


# ── Internal helpers ───────────────────────────────────────────────────────────

class _Visitor(ast.NodeVisitor):
    """AST visitor that collects functions and imports."""

    def __init__(self) -> None:
        self.functions: list[FunctionInfo] = []
        self.imports: list[ImportInfo] = []
        self.top_level_statements: list[str] = []
        self._depth = 0  # track nesting to label top-level vs nested

    # ── Functions / async functions ────────────────────────────────────────────

    def _visit_func(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        args = [arg.arg for arg in node.args.args]
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(f"{ast.unparse(dec)}")
            else:
                decorators.append(ast.unparse(dec))

        end_line = getattr(node, "end_lineno", node.lineno)
        self.functions.append(
            FunctionInfo(
                name=node.name,
                start_line=node.lineno,
                end_line=end_line,
                args=args,
                decorators=decorators,
            )
        )
        self._depth += 1
        self.generic_visit(node)
        self._depth -= 1

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_func(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_func(node)

    # ── Imports ────────────────────────────────────────────────────────────────

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(
                ImportInfo(
                    module=alias.name,
                    names=[alias.asname or alias.name],
                    lineno=node.lineno,
                    is_from=False,
                )
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        names = [alias.name for alias in node.names]
        self.imports.append(
            ImportInfo(
                module=module,
                names=names,
                lineno=node.lineno,
                is_from=True,
            )
        )
        self.generic_visit(node)

    # ── Top-level statements ───────────────────────────────────────────────────

    def visit_Module(self, node: ast.Module) -> None:
        for child in ast.iter_child_nodes(node):
            stmt_type = type(child).__name__
            if stmt_type not in ("FunctionDef", "AsyncFunctionDef", "ClassDef"):
                self.top_level_statements.append(stmt_type)
        self.generic_visit(node)


# ── Public API ─────────────────────────────────────────────────────────────────

def analyze_source(source: str) -> SourceAnalysis:
    """
    Parse a Python source string and extract structural information.

    Handles syntax errors gracefully — returns a SourceAnalysis with
    `syntax_error` set to the error description instead of raising.

    Parameters
    ----------
    source : str
        Raw Python source code.

    Returns
    -------
    SourceAnalysis
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return SourceAnalysis(syntax_error=str(exc))

    visitor = _Visitor()
    visitor.visit(tree)

    return SourceAnalysis(
        functions=visitor.functions,
        imports=visitor.imports,
        top_level_statements=visitor.top_level_statements,
    )


def find_context_at_line(source: str, lineno: int) -> LineContext:
    """
    Given a 1-based line number, find the enclosing function and nearby source.

    Parameters
    ----------
    source : str
        Raw Python source code.
    lineno : int
        The 1-based line number of interest (e.g. from a traceback).

    Returns
    -------
    LineContext
    """
    analysis = analyze_source(source)

    # Find the tightest-enclosing function (if any)
    enclosing: Optional[FunctionInfo] = None
    for func in analysis.functions:
        if func.start_line <= lineno <= func.end_line:
            # Prefer the most specific (innermost) enclosing function
            if enclosing is None or (
                func.start_line >= enclosing.start_line
                and func.end_line <= enclosing.end_line
            ):
                enclosing = func

    # Build ±3-line snippet (1-indexed display)
    source_lines = source.splitlines()
    start = max(0, lineno - 4)   # 3 lines before
    end = min(len(source_lines), lineno + 3)  # 3 lines after
    snippet_lines = source_lines[start:end]
    snippet = [
        f"{'→ ' if (start + idx + 1) == lineno else '  '}{start + idx + 1:4d} | {text}"
        for idx, text in enumerate(snippet_lines)
    ]

    return LineContext(
        lineno=lineno,
        enclosing_function=enclosing.name if enclosing else None,
        enclosing_function_start=enclosing.start_line if enclosing else None,
        snippet=snippet,
        is_in_function=enclosing is not None,
    )
