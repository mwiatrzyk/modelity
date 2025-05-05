import re
from typing import Any

from modelity.error import Error, ErrorFactory
from modelity.loc import Loc
from modelity.unset import Unset


class Ge:
    """Minimum inclusive value constraint.

    :param min_inclusive:
        The minimum inclusive value.
    """

    #: The minimum inclusive value set for this constraint.
    min_inclusive: Any

    def __init__(self, min_inclusive):
        self.min_inclusive = min_inclusive

    def __repr__(self):
        return f"{self.__class__.__name__}({self.min_inclusive!r})"

    def __hash__(self):
        return hash((self.__class__, self.min_inclusive))

    def __eq__(self, other):
        if type(other) is not self.__class__:
            return NotImplemented
        return self.min_inclusive == other.min_inclusive

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        if value >= self.min_inclusive:
            return True
        errors.append(ErrorFactory.ge_constraint_failed(loc, value, self.min_inclusive))
        return False


class Gt:
    """Minimum exclusive value constraint.

    :param min_exclusive:
        The minimum exclusive value.
    """

    #: The minimum exclusive value set for this constraint.
    min_exclusive: Any

    def __init__(self, min_exclusive):
        self.min_exclusive = min_exclusive

    def __repr__(self):
        return f"{self.__class__.__name__}({self.min_exclusive!r})"

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        if value > self.min_exclusive:
            return True
        errors.append(ErrorFactory.gt_constraint_failed(loc, value, self.min_exclusive))
        return False


class Le:
    """Maximum inclusive value constraint.

    :param max_inclusive:
        The maximum inclusive value.
    """

    #: The maximum inclusive value set for this constraint.
    max_inclusive: Any

    def __init__(self, max_inclusive):
        self.max_inclusive = max_inclusive

    def __repr__(self):
        return f"{self.__class__.__name__}({self.max_inclusive!r})"

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        if value <= self.max_inclusive:
            return True
        errors.append(ErrorFactory.le_constraint_failed(loc, value, self.max_inclusive))
        return False


class Lt:
    """Maximum exclusive value constraint.

    :param max_exclusive:
        The maximum exclusive value.
    """

    #: The maximum exclusive value set for this constraint.
    max_exclusive: Any

    def __init__(self, max_exclusive):
        self.max_exclusive = max_exclusive

    def __repr__(self):
        return f"{self.__class__.__name__}({self.max_exclusive!r})"

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        if value < self.max_exclusive:
            return True
        errors.append(ErrorFactory.lt_constraint_failed(loc, value, self.max_exclusive))
        return False


class MinLen:
    """Minimum length constraint.

    :param min_len:
        The minimum value length.
    """

    #: The minimum length.
    min_len: int

    def __init__(self, min_len: int):
        self.min_len = min_len

    def __repr__(self):
        return f"{self.__class__.__name__}({self.min_len!r})"

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        if len(value) >= self.min_len:
            return True
        errors.append(ErrorFactory.min_len_constraint_failed(loc, value, self.min_len))
        return False


class MaxLen:
    """Maximum length constraint.

    :param max_len:
        The maximum value length.
    """

    #: The minimum length.
    max_len: int

    def __init__(self, max_len: int):
        self.max_len = max_len

    def __repr__(self):
        return f"{self.__class__.__name__}({self.max_len!r})"

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        if len(value) <= self.max_len:
            return True
        errors.append(ErrorFactory.max_len_constraint_failed(loc, value, self.max_len))
        return False


class Regex:
    """Regular expression constraint.

    Allows values matching given regular expression and reject all other. Can
    only operate on strings.

    :param pattern:
        Regular expression pattern.
    """

    def __init__(self, pattern: str):
        self._compiled_pattern = re.compile(pattern)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._compiled_pattern.pattern!r})"

    @property
    def pattern(self) -> str:
        return self._compiled_pattern.pattern

    def __call__(self, errors: list[Error], loc: Loc, value: str):
        if self._compiled_pattern.match(value):
            return True
        errors.append(ErrorFactory.regex_constraint_failed(loc, value, self.pattern))
        return False
