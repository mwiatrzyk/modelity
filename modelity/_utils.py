"""General purpose common utility functions."""

import datetime
import inspect
import itertools
from typing import (
    Any,
    Callable,
    Literal,
    Mapping,
    MutableSequence,
    Sequence,
    TypeVar,
    Union,
    get_args,
    get_origin,
)
from typing_extensions import TypeIs

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


def is_neither_str_nor_bytes_sequence(obj: object) -> TypeIs[Sequence]:
    """Check if *obj* is a sequence that is neither :class:`str` nor
    :class:`bytes` instance."""
    return isinstance(obj, Sequence) and not isinstance(obj, (str, bytes))


def format_signature(sig: Sequence[str]) -> str:
    """Format function's signature as string."""
    return f"({', '.join(sig)})"


def describe(obj: Any) -> str:
    """Describe object as string for the purpose of error formatting.

    :param obj:
        The object to get string representation for.
    """
    if obj is Literal:
        return "Literal"
    if obj is Union:
        return "Union"
    if obj is Ellipsis:
        return "..."
    if isinstance(obj, (str, bytes)):
        return repr(obj)
    if isinstance(obj, Mapping):
        items = (f"{k!r}: {describe(v)}" for k, v in obj.items())
        return "{" + ", ".join(items) + "}"
    if isinstance(obj, MutableSequence):
        return f"[{', '.join(describe(x) for x in obj)}]"
    if isinstance(obj, Sequence):
        return f"({', '.join(describe(x) for x in obj)})"
    origin = get_origin(obj)
    if origin is not None:
        args = get_args(obj)
        if args:
            return f"{describe(origin)}[{', '.join(describe(x) for x in args)}]"
        else:
            return describe(origin)
    if isinstance(obj, type):
        return obj.__qualname__
    return repr(obj)


def compile_datetime_format(format: str) -> str:
    """Compile datetime format from Modelity-specific into Python-specific.

    :param format:
        The format string.

        Supported placeholders:

        * **YYYY** for years
        * **MM** for months
        * **DD** for days
        * **hh** for hours
        * **mm** for minutes
        * **ss** for seconds
        * **ffffff** for microseconds
        * **ZZZZ** for timezone
    """
    return (
        compile_date_format(format)
        .replace("hh", "%H")
        .replace("mm", "%M")
        .replace("ss", "%S")
        .replace("ffffff", "%f")
        .replace("ZZZZ", "%z")
    )


def compile_date_format(format: str) -> str:
    """Compile date format from Modelity-specific into Python-specific.

    :param format:
        The format string.

        Supported placeholders:

        * **YYYY** for years
        * **MM** for months
        * **DD** for days
    """
    return format.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")


def extract_given_param_names_subsequence(func: Callable, supported_param_names: Sequence[str]) -> set[str]:
    """For given function, extract param names it was declared in and return as
    set if it is a subsequence of *supported_param_names*, or otherwise raise
    :exc:`TypeError` exception.

    :param func:
        The function to get given param names for.

    :param supported_param_names:
        Sequence of supported param names.

        The *func* must be declared with params being a subsequence of this
        sequence.
    """
    sig = inspect.signature(func)
    given_param_names = tuple(sig.parameters)
    if not is_subsequence(given_param_names, supported_param_names):
        raise TypeError(
            f"function {func.__name__!r} has incorrect signature: "
            f"{format_signature(given_param_names)} is not a subsequence of {format_signature(supported_param_names)}"
        )
    return set(given_param_names)


def to_int_or_str(obj: str) -> int | str:
    """Convert *obj* to integer if it is a numeric string, or leave it as is
    otherwise.

    :param obj:
        The object to convert.
    """
    if obj.isdigit():
        return int(obj)
    return obj


class ExportList(list):
    """Helper for making ``__all__`` lists automatically by decorating public
    names."""

    def __call__(self, type_or_func: T) -> T:
        name = getattr(type_or_func, "__name__", None)
        if name is None:
            raise TypeError(f"cannot export {type_or_func!r}; the '__name__' property is undefined")
        self.append(name)
        return type_or_func
