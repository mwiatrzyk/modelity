import dataclasses
import functools
import re
from typing import Any

from modelity import _utils
from modelity.error import Error, ErrorFactory
from modelity.interface import IConstraint
from modelity.loc import Loc

__all__ = export = _utils.ExportList()  # type: ignore


@export
@dataclasses.dataclass(frozen=True)
class Ge(IConstraint):
    """Greater-or-equal constraint.

    Used to specify minimum inclusive value for a numeric field.
    """

    #: The minimum inclusive value set for this constraint.
    min_inclusive: int | float

    def __repr__(self):
        return f"{self.__class__.__name__}({self.min_inclusive!r})"

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        if value >= self.min_inclusive:
            return True
        errors.append(ErrorFactory.out_of_range(loc, value, min_inclusive=self.min_inclusive))
        return False


@export
@dataclasses.dataclass(frozen=True)
class Gt(IConstraint):
    """Greater-than constraint.

    Used to specify minimum exclusive value for a numeric field.
    """

    #: The minimum exclusive value set for this constraint.
    min_exclusive: int | float

    def __repr__(self):
        return f"{self.__class__.__name__}({self.min_exclusive!r})"

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        if value > self.min_exclusive:
            return True
        errors.append(ErrorFactory.out_of_range(loc, value, min_exclusive=self.min_exclusive))
        return False


@export
@dataclasses.dataclass(frozen=True)
class Le(IConstraint):
    """Less-or-equal constraint.

    Used to set maximum inclusive value for a numeric field.
    """

    #: The maximum inclusive value set for this constraint.
    max_inclusive: Any

    def __repr__(self):
        return f"{self.__class__.__name__}({self.max_inclusive!r})"

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        if value <= self.max_inclusive:
            return True
        errors.append(ErrorFactory.out_of_range(loc, value, max_inclusive=self.max_inclusive))
        return False


@export
@dataclasses.dataclass(frozen=True)
class Lt(IConstraint):
    """Less-than constraint.

    Used to set maximum exclusive value for a numeric field.
    """

    #: The maximum exclusive value set for this constraint.
    max_exclusive: Any

    def __repr__(self):
        return f"{self.__class__.__name__}({self.max_exclusive!r})"

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        if value < self.max_exclusive:
            return True
        errors.append(ErrorFactory.out_of_range(loc, value, max_exclusive=self.max_exclusive))
        return False


@export
@dataclasses.dataclass(frozen=True)
class Range(IConstraint):
    """Range constraint.

    Used to set allowed value range for a numeric field using one of
    :class:`Lt` or :class:`Gt` for minimum value, and one of :class:`Lt` or
    :class:`Le` for maximum value.

    .. versionadded:: 0.28.0
    """

    #: The minimum value.
    min: Gt | Ge

    #: The maximum value.
    max: Lt | Le

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.min!r}, {self.max!r})"

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        tmp_errors: list[Error] = []
        if self.min(tmp_errors, loc, value) and self.max(tmp_errors, loc, value):
            return True
        kwargs = {}
        if isinstance(self.min, Gt):
            kwargs["min_exclusive"] = self.min.min_exclusive
        else:
            kwargs["min_inclusive"] = self.min.min_inclusive
        if isinstance(self.max, Lt):
            kwargs["max_exclusive"] = self.max.max_exclusive
        else:
            kwargs["max_inclusive"] = self.max.max_inclusive
        errors.append(ErrorFactory.out_of_range(loc, value, **kwargs))
        return False


@export
@dataclasses.dataclass(frozen=True)
class MinLen(IConstraint):
    """Minimum length constraint.

    Can be used with sized types, like containers, :class:`byte` or
    :class:`str`.
    """

    #: Minimum length.
    min_length: int

    def __repr__(self):
        return f"{self.__class__.__name__}({self.min_length!r})"

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        if len(value) >= self.min_length:
            return True
        errors.append(ErrorFactory.invalid_length(loc, value, min_length=self.min_length))
        return False


@export
@dataclasses.dataclass(frozen=True)
class MaxLen(IConstraint):
    """Maximum length constraint.

    Can be used with sized types, like containers, :class:`byte` or
    :class:`str`.
    """

    #: Maximum length.
    max_length: int

    def __repr__(self):
        return f"{self.__class__.__name__}({self.max_length!r})"

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        if len(value) <= self.max_length:
            return True
        errors.append(ErrorFactory.invalid_length(loc, value, max_length=self.max_length))
        return False


@export
@dataclasses.dataclass(frozen=True)
class LenRange(IConstraint):
    """Length range constraint.

    Combines both minimum and maximum length constraints.

    .. versionadded:: 0.28.0
    """

    #: Minimum length.
    min_length: int

    #: Maximum length.
    max_length: int

    def __repr__(self):
        return f"{self.__class__.__name__}({self.min_length!r}, {self.max_length!r})"

    def __call__(self, errors: list[Error], loc: Loc, value: Any) -> bool:
        if self.min_length <= len(value) <= self.max_length:
            return True
        errors.append(ErrorFactory.invalid_length(loc, value, min_length=self.min_length, max_length=self.max_length))
        return False


@export
@dataclasses.dataclass(frozen=True)
class Regex(IConstraint):
    """Regular expression constraint.

    Allows values matching given regular expression and reject all other. Can
    only operate on strings.
    """

    #: Regular expression pattern.
    pattern: str

    def __repr__(self):
        return f"{self.__class__.__name__}({self.pattern!r})"

    @functools.cached_property
    def _compiled_pattern(self) -> re.Pattern:
        return re.compile(self.pattern)

    def __call__(self, errors: list[Error], loc: Loc, value: str):
        if self._compiled_pattern.match(value):
            return True
        errors.append(ErrorFactory.invalid_string_format(loc, value, self.pattern))
        return False
