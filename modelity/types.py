from typing import TypeVar, Union

from modelity.unset import UnsetType

__all__ = ["StrictOptional"]

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
