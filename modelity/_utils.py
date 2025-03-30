import itertools
from typing import Any, Callable, Optional, Sequence, TypeVar

T = TypeVar("T")

_unique_id_counter = itertools.count(1)


def next_unique_id() -> int:
    """Create next unique and ascending ID number."""
    return next(_unique_id_counter)


def is_subsequence(candidate: Sequence, seq: Sequence) -> bool:
    """Check if ``candidate`` is a subsequence of sequence ``seq``."""
    it = iter(seq)
    return all(element in it for element in candidate)


def is_mutable(obj: Any) -> bool:
    """Check if *obj* is mutable."""
    try:
        hash(obj)
        return False
    except TypeError:
        return True


def is_neither_str_nor_bytes_sequence(obj: object) -> bool:
    """Check if the object is a sequence that is neither string, nor bytes
    instance.

    :param obj:
        The object to check.
    """
    return isinstance(obj, Sequence) and not isinstance(obj, (str, bytes))


def format_signature(sig: Sequence[str]) -> str:
    """Format function's signature to string."""
    return f"({', '.join(sig)})"


def get_method(obj: object, method_name: str) -> Optional[Callable]:
    """Get method named *method_name* from object *obj*.

    Returns callable or ``None`` if method was not found.

    :param obj:
        Object to be investigated.

    :param method_name:
        Name of a method to look for.
    """
    maybe_method = getattr(obj, method_name, None)
    if not callable(maybe_method):
        return None
    return maybe_method
