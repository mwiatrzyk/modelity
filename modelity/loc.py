from typing import Any, Sequence, Union, cast


class Loc(Sequence):
    """Class for storing location of the field in the model tree.

    This is basically a :class:`tuple`-like type but with some addons and
    customizations.

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
