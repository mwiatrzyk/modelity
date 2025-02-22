import re
from typing import Any, Generic, Optional, Sized, Union, TypeVar

from modelity.error import Error, ErrorCode, ErrorFactory
from modelity.invalid import Invalid
from modelity.loc import Loc
from modelity.interface import IConfig, IInvalid, ISupportsLessEqual
from modelity.unset import Unset

T = TypeVar("T", bound=ISupportsLessEqual)


class Ge:
    """Minimum inclusive value constraint.

    :param min_inclusive:
        The minimum inclusive value.
    """

    #: The minimum inclusive value set for this constraint.
    min_inclusive: Any

    def __init__(self, min_inclusive):
        self.min_inclusive = min_inclusive

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        if value >= self.min_inclusive:
            return value
        errors.append(ErrorFactory.ge_failed(loc, value, self.min_inclusive))
        return Unset


class Gt:
    """Minimum exclusive value constraint.

    :param min_exclusive:
        The minimum exclusive value.
    """

    #: The minimum exclusive value set for this constraint.
    min_exclusive: Any

    def __init__(self, min_exclusive):
        self.min_exclusive = min_exclusive

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        if value > self.min_exclusive:
            return value
        errors.append(ErrorFactory.gt_failed(loc, value, self.min_exclusive))
        return Unset


class Le:
    """Maximum inclusive value constraint.

    :param max_inclusive:
        The maximum inclusive value.
    """

    #: The maximum inclusive value set for this constraint.
    max_inclusive: Any

    def __init__(self, max_inclusive):
        self.max_inclusive = max_inclusive

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        if value <= self.max_inclusive:
            return value
        errors.append(ErrorFactory.le_failed(loc, value, self.max_inclusive))
        return Unset


class Lt:
    """Maximum exclusive value constraint.

    :param max_exclusive:
        The maximum exclusive value.
    """

    #: The maximum exclusive value set for this constraint.
    max_exclusive: Any

    def __init__(self, max_exclusive):
        self.max_exclusive = max_exclusive

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        if value < self.max_exclusive:
            return value
        errors.append(ErrorFactory.lt_failed(loc, value, self.max_exclusive))
        return Unset


class MinLen:
    """Minimum length constraint.

    :param min_len:
        The minimum value length.
    """

    #: The minimum length.
    min_len: int

    def __init__(self, min_len: int):
        self.min_len = min_len

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        if len(value) >= self.min_len:
            return value
        errors.append(ErrorFactory.min_len_failed(loc, value, self.min_len))
        return Unset


class MaxLen:
    """Maximum length constraint.

    :param max_len:
        The maximum value length.
    """

    #: The minimum length.
    max_len: int

    def __init__(self, max_len: int):
        self.max_len = max_len

    def __call__(self, errors: list[Error], loc: Loc, value: Any):
        if len(value) <= self.max_len:
            return value
        errors.append(ErrorFactory.max_len_failed(loc, value, self.max_len))
        return Unset


class Regex:
    """Regular expression constraint.

    Allows values matching given regular expression and reject all other. Can
    only operate on strings.

    :param pattern:
        Regular expression pattern.
    """

    def __init__(self, pattern: str):
        self._compiled_pattern = re.compile(pattern)

    @property
    def pattern(self) -> str:
        return self._compiled_pattern.pattern

    def __call__(self, errors: list[Error], loc: Loc, value: str):
        if self._compiled_pattern.match(value):
            return value
        errors.append(ErrorFactory.regex_failed(loc, value, self.pattern))
        return Unset


### XXX: Remaining to be removed...


class MinValue(Generic[T]):
    """Constraint for annotating model field with minimum value, either
    inclusive or exclusive.

    Example use:

    .. testcode::

        from typing import Annotated

        from modelity.model import Model
        from modelity.constraints import MinValue

        class Dummy(Model):
            foo: Annotated[int, MinValue(min_inclusive=0)]

    .. doctest::

        >>> dummy = Dummy()
        >>> dummy.foo = 0
        >>> dummy.foo
        0
        >>> dummy.foo = -1
        Traceback (most recent call last):
            ...
        modelity.exc.ParsingError: parsing failed with 1 error(-s):
          foo:
            value must be >= 0 [code=modelity.ValueTooLow, data={'min_inclusive': 0}]

    :param min_inclusive:
        Minimum value (inclusive).

    :param min_exclusive:
        Minimum value (exclusive).
    """

    #: Minimum inclusive value.
    min_inclusive: Optional[T]

    #: Minimum exclusive value.
    min_exclusive: Optional[T]

    def __init__(self, min_inclusive: Optional[T] = None, min_exclusive: Optional[T] = None):
        if min_inclusive is None and min_exclusive is None:
            raise TypeError("__init__() requires either 'min_inclusive' or 'min_exclusive' argument to be provided")
        if min_inclusive is not None and min_exclusive is not None:
            raise TypeError("__init__() cannot be called with both 'min_inclusive' and 'min_exclusive' arguments")
        self.min_inclusive = min_inclusive
        self.min_exclusive = min_exclusive

    def __call__(self, value: T, loc: Loc, config: IConfig) -> Union[T, IInvalid]:
        if self.min_inclusive is not None and value < self.min_inclusive:
            return Invalid(
                value,
                Error(
                    loc,
                    ErrorCode.VALUE_TOO_LOW,
                    f"value must be >= {self.min_inclusive}",
                    data={"min_inclusive": self.min_inclusive},
                ),
            )
        if self.min_exclusive is not None and value <= self.min_exclusive:
            return Invalid(
                value,
                Error(
                    loc,
                    ErrorCode.VALUE_TOO_LOW,
                    f"value must be > {self.min_exclusive}",
                    data={"min_exclusive": self.min_exclusive},
                ),
            )
        return value


class MaxValue(Generic[T]):
    """Constraint for annotating model field with maximum allowed value, either
    inclusive or exclusive.

    Example use:

    .. testcode::

        from typing import Annotated

        from modelity.model import Model
        from modelity.constraints import MaxValue

        class Dummy(Model):
            foo: Annotated[int, MaxValue(max_inclusive=10)]

    .. doctest::

        >>> dummy = Dummy()
        >>> dummy.foo = 10
        >>> dummy.foo
        10
        >>> dummy.foo = 11
        Traceback (most recent call last):
            ...
        modelity.exc.ParsingError: parsing failed with 1 error(-s):
          foo:
            value must be <= 10 [code=modelity.ValueTooHigh, data={'max_inclusive': 10}]

    :param max_inclusive:
        Maximum value (inclusive).

    :param max_exclusive:
        Maximum value (exclusive).

    """

    #: Maximum inclusive value.
    max_inclusive: Optional[T]

    #: Maximum exclusive value.
    max_exclusive: Optional[T]

    def __init__(self, max_inclusive: Optional[T] = None, max_exclusive: Optional[T] = None):
        if max_inclusive is None and max_exclusive is None:
            raise TypeError("__init__() requires either 'max_inclusive' or 'max_exclusive' argument to be provided")
        if max_inclusive is not None and max_exclusive is not None:
            raise TypeError("__init__() cannot be called with both 'max_inclusive' and 'max_exclusive' arguments")
        self.max_inclusive = max_inclusive
        self.max_exclusive = max_exclusive

    def __call__(self, value: T, loc: Loc, config: IConfig) -> Union[T, IInvalid]:
        if self.max_inclusive is not None and value > self.max_inclusive:
            return Invalid(
                value,
                Error(
                    loc,
                    ErrorCode.VALUE_TOO_HIGH,
                    f"value must be <= {self.max_inclusive}",
                    data={"max_inclusive": self.max_inclusive},
                ),
            )
        if self.max_exclusive is not None and value >= self.max_exclusive:
            return Invalid(
                value,
                Error(
                    loc,
                    ErrorCode.VALUE_TOO_HIGH,
                    f"value must be < {self.max_exclusive}",
                    data={"max_exclusive": self.max_exclusive},
                ),
            )
        return value


class MinLength:
    """Constraint for annotating model field with minimum length.

    Suitable for model fields with types implementing :class:`typing.Sized`
    protocol, f.e. lists, strings, dicts etc.

    Example use:

    .. testcode::

        from typing import Annotated

        from modelity.model import Model
        from modelity.constraints import MinLength

        class Dummy(Model):
            foo: Annotated[str, MinLength(1)]

    .. doctest::

        >>> dummy = Dummy()
        >>> dummy.foo = "spam"
        >>> dummy.foo
        'spam'
        >>> dummy.foo = ""
        Traceback (most recent call last):
            ...
        modelity.exc.ParsingError: parsing failed with 1 error(-s):
          foo:
            value too short; minimum length is 1 [code=modelity.ValueTooShort, data={'min_length': 1}]

    :param min_length:
        Minimum length of the value.
    """

    #: Minimum length of the value.
    min_length: int

    def __init__(self, min_length: int):
        self.min_length = min_length

    def __call__(self, value: Sized, loc: Loc, config: IConfig) -> Union[Sized, IInvalid]:
        if len(value) < self.min_length:
            return Invalid(value, ErrorFactory.value_too_short(loc, self.min_length))
        return value


class MaxLength:
    """Constraint for annotating model field with maximum length.

    Suitable for model fields with types implementing :class:`typing.Sized`
    protocol, f.e. lists, strings, dicts etc.

    Example use:

    .. testcode::

        from typing import Annotated

        from modelity.model import Model
        from modelity.constraints import MaxLength

        class Dummy(Model):
            foo: Annotated[str, MaxLength(3)]

    .. doctest::

        >>> dummy = Dummy()
        >>> dummy.foo = "foo"
        >>> dummy.foo
        'foo'
        >>> dummy.foo = "spam"
        Traceback (most recent call last):
            ...
        modelity.exc.ParsingError: parsing failed with 1 error(-s):
          foo:
            value too long; maximum length is 3 [code=modelity.ValueTooLong, data={'max_length': 3}]

    :param max_length:
        Maximum length of the value.
    """

    #: Maximum length of the value.
    max_length: int

    def __init__(self, max_length: int):
        self.max_length = max_length

    def __call__(self, value: Sized, loc: Loc, config: IConfig) -> Union[Sized, IInvalid]:
        if len(value) > self.max_length:
            return Invalid(value, ErrorFactory.value_too_long(loc, self.max_length))
        return value
