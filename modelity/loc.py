import collections.abc

from typing import Any


class Loc(collections.abc.Iterable):
    """Object used to keep error location."""
    __slots__ = ("_path",)

    def __init__(self, *path: Any):
        self._path = path

    def __iter__(self) -> collections.abc.Iterator:
        return iter(self._path)

    def __repr__(self) -> str:
        return f"Loc({", ".join(repr(x) for x in self._path)})"

    def __str__(self) -> str:
        return ".".join(str(x) for x in self)

    def __eq__(self, value: object) -> bool:
        return isinstance(value, Loc) and self._path == value._path

    def __ne__(self, value: object) -> bool:
        return not self.__eq__(value)

    def __add__(self, other: "Loc") -> "Loc":
        return Loc(*(self._path + other._path))
