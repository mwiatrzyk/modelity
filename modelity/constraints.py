import dataclasses
import functools
from numbers import Number
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

    :param min_inclusive:
        The minimum inclusive value.
    """

    #: The minimum inclusive value set for this constraint.
    min_inclusive: int | float | Number

    def __repr__(self):
        return f"{self.__class__.__name__}({self.min_inclusive!r})"

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        if value >= self.min_inclusive:
            return True
        errors.append(ErrorFactory.ge_constraint_failed(loc, value, self.min_inclusive))
        return False


@export
@dataclasses.dataclass(frozen=True)
class Gt(IConstraint):
    """Greater-than constraint.

    Used to specify minimum exclusive value for a numeric field.

    :param min_exclusive:
        The minimum exclusive value.
    """

    #: The minimum exclusive value set for this constraint.
    min_exclusive: int | float | Number

    def __repr__(self):
        return f"{self.__class__.__name__}({self.min_exclusive!r})"

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        if value > self.min_exclusive:
            return True
        errors.append(ErrorFactory.gt_constraint_failed(loc, value, self.min_exclusive))
        return False


@export
@dataclasses.dataclass(frozen=True)
class Le(IConstraint):
    """Less-or-equal constraint.

    Used to set maximum inclusive value for a numeric field.

    :param max_inclusive:
        The maximum inclusive value.
    """

    #: The maximum inclusive value set for this constraint.
    max_inclusive: Any

    def __repr__(self):
        return f"{self.__class__.__name__}({self.max_inclusive!r})"

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        if value <= self.max_inclusive:
            return True
        errors.append(ErrorFactory.le_constraint_failed(loc, value, self.max_inclusive))
        return False


@export
@dataclasses.dataclass(frozen=True)
class Lt(IConstraint):
    """Less-than constraint.

    Used to set maximum exclusive value for a numeric field.

    :param max_exclusive:
        The maximum exclusive value.
    """

    #: The maximum exclusive value set for this constraint.
    max_exclusive: Any

    def __repr__(self):
        return f"{self.__class__.__name__}({self.max_exclusive!r})"

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        if value < self.max_exclusive:
            return True
        errors.append(ErrorFactory.lt_constraint_failed(loc, value, self.max_exclusive))
        return False


@export
@dataclasses.dataclass(frozen=True)
class MinLen(IConstraint):
    """Minimum length constraint.

    Used to set minimum allowed number of characters/bytes for a text/bytes
    field or minimum number of elements for collection fields.

    :param min_len:
        The minimum length.
    """

    #: The minimum length.
    min_len: int

    def __repr__(self):
        return f"{self.__class__.__name__}({self.min_len!r})"

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        if len(value) >= self.min_len:
            return True
        errors.append(ErrorFactory.min_len_constraint_failed(loc, value, self.min_len))
        return False


@export
@dataclasses.dataclass(frozen=True)
class MaxLen(IConstraint):
    """Maximum length constraint.

    Used to set maximum allowed number of characters/bytes in a text/bytes
    field or a maximum number of elements for collection fields.

    :param max_len:
        The maximum length.
    """

    #: The minimum length.
    max_len: int

    def __repr__(self):
        return f"{self.__class__.__name__}({self.max_len!r})"

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        if len(value) <= self.max_len:
            return True
        errors.append(ErrorFactory.max_len_constraint_failed(loc, value, self.max_len))
        return False


@export
@dataclasses.dataclass(frozen=True)
class Regex(IConstraint):
    """Regular expression constraint.

    Allows values matching given regular expression and reject all other. Can
    only operate on strings.

    :param pattern:
        Regular expression pattern.
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
        errors.append(ErrorFactory.regex_constraint_failed(loc, value, self.pattern))
        return False
