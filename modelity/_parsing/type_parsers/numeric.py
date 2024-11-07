from numbers import Number
from typing import Any, Type, Union, cast
from modelity.error import ErrorCode, ErrorFactory
from modelity.invalid import Invalid
from modelity.interface import IModelConfig
from modelity.providers import TypeParserProvider

provider = TypeParserProvider()


@provider.type_parser_factory(int)
def make_int_parser():

    def parse_int(value, loc):
        try:
            return int(value)
        except (ValueError, TypeError):
            return Invalid(value, ErrorFactory.create(loc, ErrorCode.INTEGER_REQUIRED))

    return parse_int


@provider.type_parser_factory(float)
def make_float_parser():

    def parse_float(value, loc):
        try:
            return float(value)
        except (ValueError, TypeError):
            return Invalid(value, ErrorFactory.create(loc, ErrorCode.FLOAT_REQUIRED))

    return parse_float


@provider.type_parser_factory(Number)
def make_number_parser(model_config: IModelConfig):
    # IMPORTANT: Remember to add more numeric types here
    tp = cast(Type[Any], Union[int, float])
    return model_config.type_parser_provider.provide_type_parser(tp, model_config)
