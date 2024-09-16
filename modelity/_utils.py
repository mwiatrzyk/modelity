from ast import Tuple
import functools
from typing import Callable, Sequence, TypeVar, Union

from modelity.error import Error, ErrorFactory
from modelity.loc import Loc

T = TypeVar("T")


def is_subsequence(candidate: Sequence, seq: Sequence) -> bool:
    """Check if ``candidate`` is a subsequence of sequence ``seq``."""
    it = iter(seq)
    return all(element in it for element in candidate)


def format_signature(sig: Sequence[str]) -> str:
    """Format function's signature to string."""
    return f"({', '.join(sig)})"


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
