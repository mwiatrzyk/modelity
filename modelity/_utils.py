import functools
from typing import Callable, Iterable, Optional, TypeVar, Union

from modelity.error import Error, ErrorFactory
from modelity.loc import Loc

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


def make_noexcept_func(func: Callable[..., T], loc: Loc = Loc()) -> Callable[..., Union[T, Error]]:
    """Convert provided function into new function returning :class:`Error`
    whenever given ``func`` raises :exc:`ValueError` or :exc:`TypeError`
    exceptions.

    This is used to wrap custom validator and filter functions.

    :param func:
        The callable to be wrapped.

    :param loc:
        The location to use when error is returned.
    """

    @functools.wraps(func)
    def proxy(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return ErrorFactory.value_error(loc, str(e))
        except TypeError as e:
            return ErrorFactory.type_error(loc, str(e))

    return proxy
