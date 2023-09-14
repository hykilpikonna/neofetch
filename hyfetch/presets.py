from __future__ import annotations

from typing import Iterable


def remove_duplicates(seq: Iterable) -> list:
    """
    Remove duplicate items from a sequence while preserving the order
    """
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]
