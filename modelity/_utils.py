from typing import Any, Callable, Iterable, Optional, Type, TypeVar

T = TypeVar("T")


def is_subsequence(candidate: Iterable, seq: Iterable) -> bool:
    """Check if ``candidate`` is a subsequence of sequence ``seq``."""
    it = iter(seq)
    return all(element in it for element in candidate)


def format_signature(sig: Iterable[str]) -> str:
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
