from typing import TypeVar, Union

from modelity.unset import UnsetType

__all__ = ["StrictOptional", "LooseOptional"]

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
