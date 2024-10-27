from typing import Any, Generic, Optional, Sequence, Sized, Union, TypeVar

from modelity.error import ErrorFactory
from modelity.invalid import Invalid
from modelity.loc import Loc
from modelity.interface import ISupportsLessEqual

T = TypeVar("T", bound=ISupportsLessEqual)


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
            modelity.ValueTooLow {'min_inclusive': 0, 'min_exclusive': None}

    :param min_inclusive:
        Minimum value (inclusive).

    :param min_exclusive:
        Minimum value (exclusive).
    """

    #: Minimum inclusive value.
    min_inclusive: Optional[T]

    #: Minimum exclusive value.
    min_exclusive: Optional[T]

    def __init__(self, min_inclusive: Optional[T]=None, min_exclusive: Optional[T]=None):
        if min_inclusive is None and min_exclusive is None:
            raise TypeError("__init__() requires either 'min_inclusive' or 'min_exclusive' argument to be provided")
        if min_inclusive is not None and min_exclusive is not None:
            raise TypeError("__init__() cannot be called with both 'min_inclusive' and 'min_exclusive' arguments")
        self.min_inclusive = min_inclusive
        self.min_exclusive = min_exclusive

    def __call__(self, value: T, loc: Loc) -> Union[T, Invalid]:
        if self.min_inclusive is not None and value < self.min_inclusive:
            return Invalid(value, ErrorFactory.value_too_low(loc, min_inclusive=self.min_inclusive))
        if self.min_exclusive is not None and value <= self.min_exclusive:
            return Invalid(value, ErrorFactory.value_too_low(loc, min_exclusive=self.min_exclusive))
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
            modelity.ValueTooHigh {'max_inclusive': 10, 'max_exclusive': None}

    :param max_inclusive:
        Maximum value (inclusive).

    :param max_exclusive:
        Maximum value (exclusive).

    """

    #: Maximum inclusive value.
    max_inclusive: Optional[T]

    #: Maximum exclusive value.
    max_exclusive: Optional[T]

    def __init__(self, max_inclusive: Optional[T]=None, max_exclusive: Optional[T]=None):
        if max_inclusive is None and max_exclusive is None:
            raise TypeError("__init__() requires either 'max_inclusive' or 'max_exclusive' argument to be provided")
        if max_inclusive is not None and max_exclusive is not None:
            raise TypeError("__init__() cannot be called with both 'max_inclusive' and 'max_exclusive' arguments")
        self.max_inclusive = max_inclusive
        self.max_exclusive = max_exclusive

    def __call__(self, value: T, loc: Loc) -> Union[T, Invalid]:
        if self.max_inclusive is not None and value > self.max_inclusive:
            return Invalid(value, ErrorFactory.value_too_high(loc, max_inclusive=self.max_inclusive))
        if self.max_exclusive is not None and value >= self.max_exclusive:
            return Invalid(value, ErrorFactory.value_too_high(loc, max_exclusive=self.max_exclusive))
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
            modelity.ValueTooShort {'min_length': 1}

    :param min_length:
        Minimum length of the value.
    """

    #: Minimum length of the value.
    min_length: int

    def __init__(self, min_length: int):
        self.min_length = min_length

    def __call__(self, value: Sized, loc: Loc) -> Union[Sized, Invalid]:
        if len(value) < self.min_length:
            return Invalid(value, ErrorFactory.value_too_short(loc, min_length=self.min_length))
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
            modelity.ValueTooLong {'max_length': 3}

    :param max_length:
        Maximum length of the value.
    """

    #: Maximum length of the value.
    max_length: int

    def __init__(self, max_length: int):
        self.max_length = max_length

    def __call__(self, value: Sized, loc: Loc) -> Union[Sized, Invalid]:
        if len(value) > self.max_length:
            return Invalid(value, ErrorFactory.value_too_long(loc, max_length=self.max_length))
        return value
