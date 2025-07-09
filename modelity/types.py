from typing import TypeVar, Union

from modelity.unset import UnsetType

T = TypeVar("T")


#: An optional that allows the field to be set to either instance of T or not
#: set at all.
#:
#: This was added to replace `optional` parameter of the
#: :class:`modelity.model.FieldInfo` class.
#:
#: .. versionadded:: 0.16.0
StrictOptional = Union[T, UnsetType]
