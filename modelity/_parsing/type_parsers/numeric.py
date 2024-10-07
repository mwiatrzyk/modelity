from numbers import Number
from typing import Union
from modelity.error import Error, ErrorCode
from modelity.invalid import Invalid
from modelity.interface import ITypeParserProvider
from modelity.providers import TypeParserProvider

provider = TypeParserProvider()


@provider.type_parser_factory(int)
def make_int_parser():

    def parse_int(value, loc):
        try:
            return int(value)
        except (ValueError, TypeError):
            return Invalid(value, Error.create(loc, ErrorCode.INTEGER_REQUIRED))

    return parse_int


@provider.type_parser_factory(float)
def make_float_parser():

    def parse_float(value, loc):
        try:
            return float(value)
        except (ValueError, TypeError):
            return Invalid(value, Error.create(loc, ErrorCode.FLOAT_REQUIRED))

    return parse_float


@provider.type_parser_factory(Number)
def make_number_parser(provider: ITypeParserProvider):
    # IMPORTANT: Remember to add more numeric types here
    return provider.provide_type_parser(Union[int, float])  # type: ignore
