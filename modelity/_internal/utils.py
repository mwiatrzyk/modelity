"""General purpose common utility functions."""

import itertools
from typing import Any, Sequence, TypeVar

T = TypeVar("T")

_unique_id_counter = itertools.count(1)


def next_unique_id() -> int:
    """Create next unique and ascending ID number."""
    return next(_unique_id_counter)


def is_subsequence(candidate: Sequence, seq: Sequence) -> bool:
    """Check if *candidate* sequence is a subsequence of sequence *seq*.

    The condition is ``True`` if and only if all items from *candidate* exist
    in *seq* and the order of elements existing in *seq* is the same as in
    *candidate*.
    """
    it = iter(seq)
    return all(element in it for element in candidate)


def is_mutable(obj: Any) -> bool:
    """Check if *obj* is mutable.

    This function uses :func:`hash` function; if hash can be computed, then the
    object is immutable, otherwise it is mutable.
    """
    try:
        hash(obj)
        return False
    except TypeError:
        return True


def is_neither_str_nor_bytes_sequence(obj: object) -> bool:
    """Check if *obj* is a sequence that is neither :class:`str` nor
    :class:`bytes` instance."""
    return isinstance(obj, Sequence) and not isinstance(obj, (str, bytes))


def format_signature(sig: Sequence[str]) -> str:
    """Format function's signature as string."""
    return f"({', '.join(sig)})"
