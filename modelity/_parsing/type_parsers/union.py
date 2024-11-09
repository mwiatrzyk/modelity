import typing

from modelity.error import ErrorCode
from modelity.invalid import Invalid
from modelity.interface import IConfig, IConfig
from modelity.providers import TypeParserProvider

provider = TypeParserProvider()


@provider.type_parser_factory(typing.Union)
def make_union_parser(tp: typing.Any, model_config: IConfig):

    def parse_union(value, loc, config: IConfig):
        for type in supported_types:
            if isinstance(value, type):
                return value
        for parser in supported_parsers:
            result = parser(value, loc, config)
            if not isinstance(result, Invalid):
                return result
        return Invalid(value, config.create_error(loc, ErrorCode.UNSUPPORTED_TYPE, {"supported_types": supported_types}))

    supported_types = typing.get_args(tp)
    provide_type_parser = model_config.type_parser_provider.provide_type_parser
    supported_parsers = [provide_type_parser(x, model_config) for x in supported_types]
    return parse_union
