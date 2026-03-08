# TODO: Consider renaming this module to `typing.py`

from typing import Annotated, Any, Protocol, TypeVar, Union, get_args, get_origin

from modelity import _utils
from modelity.unset import UnsetType

__all__ = export = _utils.ExportList(["StrictOptional", "LooseOptional", "Deferred"])  # type: ignore

T = TypeVar("T")


#: An optional that allows the field to be set to either instance of T or not
#: set at all.
#:
#: It can be used to replace :obj:`typing.Optional` for self-exclusive fields
#: where exactly one can be set. This corresponds to a situation in a JSON object
#: that only one key out of two possible is allowed.
#:
#: .. versionadded:: 0.16.0
StrictOptional = Union[T, UnsetType]


#: An extended :obj:`typing.Optional` that additionally allows
#: :class:`modelity.unset.UnsetType` objects as valid values.
#:
#: This can be used to satisfy static code checking tools, when initializing
#: fields with :obj:`modelity.unset.Unset` object explicitly.
#:
#: .. versionadded:: 0.28.0
LooseOptional = Union[T, None, UnsetType]


#: Marker used to to declare field as deferred.
#:
#: Deferred fields can be initialized with ``Unset``, but must eventually be
#: set to instance of type ``T`` to pass validation.
#:
#: .. versionadded:: 0.35.0
Deferred = Annotated[StrictOptional[T], "__deferred__"]


@export
class Comparable(Protocol):
    """Protocol describing generic comparable type.

    .. versionadded:: 0.33.0
    """

    def __lt__(self, other: Any, /) -> bool: ...
    def __le__(self, other: Any, /) -> bool: ...
    def __gt__(self, other: Any, /) -> bool: ...
    def __ge__(self, other: Any, /) -> bool: ...


def is_optional(typ: Any) -> bool:
    """Check if given type is ``Optional[T]``.

    .. versionadded:: 0.36.0

    :param tp:
        The type to check.
    """
    origin = get_origin(typ)
    if origin is not Union:
        return False
    args = get_args(typ)
    return len(args) == 2 and args[-1] is type(None)


def is_strict_optional(typ: Any) -> bool:
    """Check if given type is ``StrictOptional[T]``.

    .. versionadded:: 0.36.0

    :param tp:
        The type to check.
    """
    origin = get_origin(typ)
    if origin is not Union:
        return False
    args = get_args(typ)
    return len(args) == 2 and args[-1] is UnsetType and args[0] is not type(None)


def is_loose_optional(typ: Any) -> bool:
    """Check if given type is ``LooseOptional[T]``.

    .. versionadded:: 0.36.0

    :param tp:
        The type to check.
    """
    origin = get_origin(typ)
    if origin is not Union:
        return False
    args = get_args(typ)
    return len(args) == 3 and args[-2] is type(None) and args[-1] is UnsetType


def is_any_optional(typ: Any) -> bool:
    """Check if given type is any of the optional types supported by Modelity.

    :param tp:
        The type to check.
    """  # TODO: add ref to docs pointing to required/optional/deferred explanation
    if typ is type(None) or typ is UnsetType:
        return True
    origin = get_origin(typ)
    if origin is not Union:
        return False
    args = get_args(typ)
    return type(None) in args or UnsetType in args


def is_deferred(typ: Any) -> bool:
    """Check if given type is a deferred type.

    Deferred types in Modelity are used to declare model fields as required but
    only during validation stage. This means that the field can be unset when
    model is created, but must later be set to pass validation.

    .. versionadded:: 0.35.0

    :param tp:
        The type to check.
    """
    origin = get_origin(typ)
    if origin is not Annotated:
        return False
    args = get_args(typ)
    return args[-1] == "__deferred__"


def is_unsettable(typ: Any) -> bool:
    """Check if given type annotation allows :obj:`modelity.unset.Unset` as
    valid value.

    .. versionadded:: 0.35.0

    :param typ:
        The type to investigate.
    """
    origin = get_origin(typ)
    if origin is UnsetType:
        return True
    if origin is not Union:
        return False
    return UnsetType in get_args(typ)
