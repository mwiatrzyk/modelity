# TODO: Added to check Annotated type; make it better

from numbers import Number
from typing import Any

from modelity.error import ErrorFactory
from modelity.invalid import Invalid
from modelity.loc import Loc
from modelity.parsing.interface import IParser


class Range(IParser):

    def __init__(self, min: Number, max: Number):
        self._min = min
        self._max = max

    def __call__(self, value: Number, loc: Loc) -> Any | Invalid:
        if value < self._min or value > self._max:
            return Invalid(value, ErrorFactory.value_out_of_range(loc, self._min, self._max))
        return value


class Min(IParser):

    def __init__(self, min: Number):
        self._min = min

    def __call__(self, value: Number, loc: Loc) -> Any | Invalid:
        if value < self._min:
            return Invalid(value, ErrorFactory.value_too_low(loc, self._min))
        return value


class Max(IParser):

    def __init__(self, max: Number):
        self._max = max

    def __call__(self, value: Number, loc: Loc) -> Any | Invalid:
        if value > self._max:
            return Invalid(value, ErrorFactory.value_too_high(loc, self._max))
        return value
