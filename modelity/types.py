# TODO: Consider renaming this module to `typing.py`

from typing import Protocol, TypeVar, Union

from modelity import _utils
from modelity.unset import UnsetType

__all__ = export = _utils.ExportList(["StrictOptional", "LooseOptional"])  # type: ignore

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


@export
class Comparable(Protocol):
    """Protocol describing generic comparable type.

    .. versionadded:: 0.33.0
    """

    def __lt__(self, other: object) -> bool: ...
    def __le__(self, other: object) -> bool: ...
    def __gt__(self, other: object) -> bool: ...
    def __ge__(self, other: object) -> bool: ...
