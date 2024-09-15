from numbers import Number
from typing import Union
from modelity.error import Error, ErrorCode
from modelity.invalid import Invalid
from modelity.parsing.interface import IParserProvider
from modelity.parsing.registry import TypeParserRegistry

registry = TypeParserRegistry()


@registry.type_parser_factory(int)
def make_int_parser():

    def parse_int(value, loc):
        try:
            return int(value)
        except (ValueError, TypeError):
            return Invalid(value, Error.create(loc, ErrorCode.INTEGER_REQUIRED))

    return parse_int


@registry.type_parser_factory(float)
def make_float_parser():

    def parse_float(value, loc):
        try:
            return float(value)
        except (ValueError, TypeError):
            return Invalid(value, Error.create(loc, ErrorCode.FLOAT_REQUIRED))

    return parse_float


@registry.type_parser_factory(Number)
def make_number_parser(registry: IParserProvider):
    return registry.provide_parser(Union[int, float])
