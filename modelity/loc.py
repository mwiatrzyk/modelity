from typing import Any, Sequence

from modelity._export_list import ExportList

__all__ = export = ExportList()  # type: ignore


@export
class Loc(Sequence):
    """A tuple-like type that stores location of the value (or error) in the
    model tree.

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

    :param `*args`:
        The positional arguments composing location's path.
    """

    __slots__ = ("_data",)

    def __init__(self, *path: Any):
        self._data = path

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({', '.join(repr(x) for x in self._data)})"

    def __str__(self) -> str:
        return ".".join(str(x) for x in self) or "(empty)"

    def __hash__(self) -> int:
        return hash(self._data)

    def __getitem__(self, index):
        if type(index) is slice:
            if index.step is not None:
                raise TypeError("slicing with step is not allowed for Loc objects")
            return Loc(*self._data[index])
        return self._data[index]

    def __len__(self) -> int:
        return len(self._data)

    def __lt__(self, value: object) -> bool:
        if type(value) is not Loc:
            return NotImplemented
        return self._data < value._data

    def __eq__(self, value: object) -> bool:
        if type(value) is not Loc:
            return NotImplemented
        return self._data == value._data

    def __add__(self, other):
        if type(other) is not Loc:
            return NotImplemented
        return Loc(*(self._data + other._data))

    def to_tuple(self) -> tuple:
        """Convert this location into tuple object.

        .. versionadded:: 0.36.0
        """
        return self._data

    @property
    def last(self) -> Any:
        """Return last component of the location."""
        return self._data[-1]

    def is_parent_of(self, other: "Loc") -> bool:
        """Check if this location is parent (prefix) of given *other*
        location.

        :param other:
            The other location object.
        """
        self_len = len(self)
        if self_len > len(other):
            return False
        return self._data == other._data[:self_len]

    def is_empty(self) -> bool:
        """Check if this is an empty location object."""
        return len(self) == 0

    def suffix_match(self, pattern: "Loc") -> bool:
        """Check if suffix of this location matches given pattern.

        Examples:

        .. doctest::

            >>> Loc("foo").suffix_match(Loc("foo"))
            True
            >>> Loc("foo").suffix_match(Loc("foo", "bar"))
            False
            >>> Loc("foo", "bar").suffix_match(Loc("foo", "bar"))
            True
            >>> Loc("foo", "bar").suffix_match(Loc("foo", "*"))
            True
            >>> Loc("foo", 3, "bar").suffix_match(Loc("foo", "*", "bar"))
            True
            >>> Loc("foo", 3, "bar").suffix_match(Loc("foo", "*", "baz"))
            False

        .. versionadded:: 0.27.0
        """
        if len(pattern) > len(self):
            return False
        for val, pattern in zip(reversed(self), reversed(pattern)):
            if val != pattern and pattern != "*":
                return False
        return True

    @classmethod
    def irrelevant(cls) -> "Loc":
        """Return a special location value indicating that the exact location
        is irrelevant.

        This is equivalent to ``Loc("_")`` and is typically used in containers
        like sets or unordered structures, where the concept of position or
        path does not apply.

        For example, when comparing or storing elements where their precise
        placement is not semantically meaningful, this sentinel location can be
        used to fulfill API requirements without implying an actual location.

        .. versionadded:: 0.17.0
        """
        return cls("_")


class Pattern(Sequence):
    """A tuple-like type for storing location patterns.

    This is used when performing location match tests.

    .. versionadded:: 0.36.0
    """
    __slots__ = ("_data",)

    def __init__(self, *pattern: Any):
        self._data = pattern

    def __hash__(self) -> int:
        return hash(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, index: Any) -> Any:
        if type(index) is slice:
            raise TypeError("slicing is not supported for Pattern type")
        return self._data[index]

    def __eq__(self, value: object) -> bool:
        if type(value) is not Pattern:
            return NotImplemented
        return self._data == value._data

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({', '.join(repr(x) for x in self._data)})"

    def match(self, loc: Loc) -> bool:
        """Check if given location can be matched by this pattern.

        This method compares from left to right and returns as soon as
        inconsistency is found. Following wildcards are supported:

        * ``?`` for matching exactly one location element
        * ``*`` for matching one or more location elements
        * ``**`` for matching zero or more location elements

        :param loc:
            The location to check.
        """
        pattern = self._data
        pattern_len = len(pattern)
        path = loc.to_tuple()
        i = j = 0
        star_i = star_j = -1
        double_star_i = double_star_j = -1
        while j < len(path):
            if i < pattern_len and (pattern[i] == path[j] or pattern[i] == "?"):
                i += 1
                j += 1
            elif i < pattern_len and pattern[i] == "*":
                star_i = i
                star_j = j
                i += 1
                j += 1
            elif i < pattern_len and pattern[i] == "**":
                double_star_i = i
                double_star_j = j
                i += 1
            elif star_i != -1:
                star_j += 1
                i = star_i + 1
                j = star_j
            elif double_star_i != -1:
                double_star_j += 1
                i = double_star_i + 1
                j = double_star_j
            else:
                return False
        return i == pattern_len or pattern == ("**",)

    @classmethod
    def wildcard_one(cls):
        """Return a special location containing a single-item wildcard.

        This is equivalent to ``Loc("?")`` and is used to compose location
        patterns for the :meth:`match` method.
        """
        return cls("?")

    @classmethod
    def wildcard_one_or_more(cls):
        """Return a special location containing a one-or-more-items wildcard.

        This is equivalent to ``Loc("*")`` and is used to compose location
        patterns for the :meth:`match` method.
        """
        return cls("*")
