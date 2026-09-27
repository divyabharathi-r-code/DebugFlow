"""
test_sample.py
--------------
Pytest tests for buggy_sample.py — used as the DebugFlow demo.

Each test verifies that the buggy function raises the expected exception.
After DebugFlow generates a fix, this test file can be rerun to confirm
the fix resolves the issue.
"""

import sys
import os
import pytest

# Allow importing buggy_sample when running from different working directories
sys.path.insert(0, os.path.dirname(__file__))

from buggy_sample import calculate_average, get_item, first_element


class TestCalculateAverage:
    """Tests for calculate_average()."""

    def test_empty_list_raises_zero_division(self):
        """Bug 1: empty list → ZeroDivisionError."""
        with pytest.raises(ZeroDivisionError):
            calculate_average([])

    def test_normal_list_returns_correct_average(self):
        """Sanity check: non-empty list should work once the bug is fixed."""
        # This test PASSES even with the bug (non-empty input)
        result = calculate_average([2, 4, 6])
        assert result == 4.0

    def test_single_element(self):
        """Single-element list average equals the element."""
        assert calculate_average([10]) == 10.0


class TestGetItem:
    """Tests for get_item()."""

    def test_existing_key_raises_name_error(self):
        """Bug 2: typo `reslt` → NameError even when key exists."""
        with pytest.raises(NameError):
            get_item({"name": "Alice"}, "name")

    def test_missing_key_raises_name_error(self):
        """Bug 2 also affects missing-key lookups."""
        with pytest.raises(NameError):
            get_item({}, "name")


class TestFirstElement:
    """Tests for first_element()."""

    def test_empty_list_raises_index_error(self):
        """Bug 3: empty list → IndexError."""
        with pytest.raises(IndexError):
            first_element([])

    def test_non_empty_list_returns_first(self):
        """Sanity check: non-empty list should work."""
        assert first_element([42, 99]) == 42
