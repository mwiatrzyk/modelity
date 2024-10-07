# TODO: Added to check Annotated type; make it better

from typing import Union, TypeVar

from modelity.error import ErrorFactory
from modelity.invalid import Invalid
from modelity.loc import Loc
from modelity.interface import IParser, ISupportsLess

T = TypeVar("T", bound=ISupportsLess)


class Range(IParser[T]):
    min: T
    max: T

    def __init__(self, min: T, max: T):
        self.min = min
        self.max = max

    def __call__(self, value: T, loc: Loc) -> Union[T, Invalid]:
        if value < self.min or value > self.max:
            return Invalid(value, ErrorFactory.value_out_of_range(loc, self.min, self.max))
        return value


class Min(IParser[T]):
    min: T

    def __init__(self, min: T):
        self.min = min

    def __call__(self, value: T, loc: Loc) -> Union[T, Invalid]:
        if value < self.min:
            return Invalid(value, ErrorFactory.value_too_low(loc, self.min))
        return value


class Max(IParser[T]):
    max: T

    def __init__(self, max: T):
        self.max = max

    def __call__(self, value: T, loc: Loc) -> Union[T, Invalid]:
        if value > self.max:
            return Invalid(value, ErrorFactory.value_too_high(loc, self.max))
        return value
