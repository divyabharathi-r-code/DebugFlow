/**
 * demo.js
 * -------
 * Demo code and traceback strings loaded from demo/buggy_sample.py.
 * Used by the "Load Demo" buttons.
 */

export const DEMO_CODE = `"""
buggy_sample.py — A deliberately buggy Python module for DebugFlow demo.

Bug 1 — ZeroDivisionError: calculate_average() divides by count without
         checking for an empty list.
Bug 2 — NameError: get_item() references undefined variable \`reslt\` (typo).
Bug 3 — IndexError: first_element() accesses index 0 without bounds check.
"""


def calculate_average(numbers: list) -> float:
    """Return the arithmetic mean of a list of numbers."""
    total = sum(numbers)
    count = len(numbers)
    # BUG 1: if numbers is empty, count == 0 → ZeroDivisionError
    return total / count


def get_item(data: dict, key: str) -> str:
    """Look up a key in a dictionary and return a formatted string."""
    result = data.get(key, "unknown")
    # BUG 2: typo — \`reslt\` is not defined (should be \`result\`)
    return f"Found: {reslt}"


def first_element(items: list):
    """Return the first element of a list."""
    # BUG 3: no bounds check — raises IndexError when items is empty
    return items[0]
`

export const DEMO_ERROR = `Traceback (most recent call last):
  File "buggy_sample.py", line 22, in calculate_average
    return total / count
ZeroDivisionError: division by zero`

export const DEMO_ERROR_NAMEERROR = `Traceback (most recent call last):
  File "buggy_sample.py", line 29, in get_item
    return f"Found: {reslt}"
NameError: name 'reslt' is not defined`

export const DEMO_ERROR_INDEXERROR = `Traceback (most recent call last):
  File "buggy_sample.py", line 29, in first_element
    return items[0]
IndexError: list index out of range`

export const DEMO_TEST_CODE = `import pytest

def calculate_average(numbers):
    total = sum(numbers)
    count = len(numbers)
    return total / count

def get_item(data, key):
    result = data.get(key, "unknown")
    return f"Found: {reslt}"

def first_element(items):
    return items[0]

class TestCalculateAverage:
    def test_empty_list_raises_zero_division(self):
        with pytest.raises(ZeroDivisionError):
            calculate_average([])

    def test_normal_list_returns_correct_average(self):
        result = calculate_average([2, 4, 6])
        assert result == 4.0

class TestGetItem:
    def test_existing_key_raises_name_error(self):
        with pytest.raises(NameError):
            get_item({"name": "Alice"}, "name")

class TestFirstElement:
    def test_empty_list_raises_index_error(self):
        with pytest.raises(IndexError):
            first_element([])

    def test_non_empty_list_returns_first(self):
        assert first_element([42, 99]) == 42
`
