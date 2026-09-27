"""
buggy_sample.py
---------------
A deliberately buggy Python module for DebugFlow demo purposes.

Bug 1 — ZeroDivisionError:
    calculate_average() divides by the count without checking for an empty list.

Bug 2 — NameError:
    get_item() references an undefined variable `reslt` (typo — should be `result`).

Bug 3 — IndexError:
    first_element() accesses index 0 without checking whether the list is empty.

These bugs are intentionally simple so that DebugFlow can reproduce and analyze
each one deterministically.
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
    # BUG 2: typo — `reslt` is not defined (should be `result`)
    return f"Found: {reslt}"


def first_element(items: list):
    """Return the first element of a list."""
    # BUG 3: no bounds check — raises IndexError when items is empty
    return items[0]


if __name__ == "__main__":
    # Demonstrate Bug 1
    print("--- Bug 1: ZeroDivisionError ---")
    try:
        avg = calculate_average([])
        print(f"Average: {avg}")
    except ZeroDivisionError as e:
        print(f"Caught: {type(e).__name__}: {e}")

    # Demonstrate Bug 2
    print("\n--- Bug 2: NameError ---")
    try:
        item = get_item({"name": "Alice"}, "name")
        print(item)
    except NameError as e:
        print(f"Caught: {type(e).__name__}: {e}")

    # Demonstrate Bug 3
    print("\n--- Bug 3: IndexError ---")
    try:
        first = first_element([])
        print(f"First: {first}")
    except IndexError as e:
        print(f"Caught: {type(e).__name__}: {e}")
