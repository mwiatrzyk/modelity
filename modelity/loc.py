from typing import Any, Sequence, cast

__all__ = ["Loc"]


class Loc(Sequence):
    """A tuple-like type for storing location of the value in the model tree.

    Examples:

    >>> from modelity.loc import Loc
    >>> root = Loc("root")
    >>> nested = root + Loc("nested")
    >>> nested
    Loc('root', 'nested')
    >>> nested += Loc(0)
    >>> nested
    Loc('root', 'nested', 0)
    >>> str(nested)
    'root.nested.0'
    >>> nested[0]
    'root'
    >>> nested[-1]
    0
    """

    __slots__ = ("_path",)

    def __init__(self, *path: Any):
        self._path = path

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({', '.join(repr(x) for x in self._path)})"

    def __str__(self) -> str:
        return ".".join(str(x) for x in self) or "(empty)"

    def __getitem__(self, index):
        if type(index) is slice:
            if index.step is not None:
                raise TypeError("slicing with step is not allowed for Loc objects")
            return Loc(*self._path[index])
        return self._path[index]

    def __len__(self) -> int:
        return len(self._path)

    def __lt__(self, value: object) -> bool:
        if self.__class__ is not value.__class__:
            return NotImplemented
        return self._path < cast(Loc, value)._path

    def __eq__(self, value: object) -> bool:
        if self.__class__ is not value.__class__:
            return NotImplemented
        return self._path == cast(Loc, value)._path

    def __add__(self, other: "Loc") -> "Loc":
        return Loc(*(self._path + other._path))

    @property
    def last(self) -> Any:
        """Return last component of the location."""
        return self._path[-1]

    def is_parent_of(self, other: "Loc") -> bool:
        """Check if this location is parent (prefix) of given *other*
        location.

        :param other:
            The other location object.
        """
        self_len = len(self)
        if self_len > len(other):
            return False
        return self._path == other._path[:self_len]

    def is_empty(self) -> bool:
        """Check if this is an empty location object."""
        return len(self) == 0

    @classmethod
    def irrelevant(cls) -> "Loc":
        """Return a special location value indicating that the exact location
        is irrelevant.

        This is equivalent to ``Loc('_')`` and is typically used in containers
        like sets or unordered structures, where the concept of position or
        path does not apply.

        For example, when comparing or storing elements where their precise
        placement is not semantically meaningful, this sentinel location can be
        used to fulfill API requirements without implying an actual location.

        .. versionadded:: 0.17.0
        """
        return cls("_")
