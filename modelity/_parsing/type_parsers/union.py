import typing

from modelity.error import ErrorFactory
from modelity.invalid import Invalid
from modelity.interface import IModelConfig, ITypeParserProvider
from modelity.providers import TypeParserProvider

provider = TypeParserProvider()


@provider.type_parser_factory(typing.Union)
def make_union_parser(tp: typing.Any, model_config: IModelConfig):

    def parse_union(value, loc):
        for type in supported_types:
            if isinstance(value, type):
                return value
        for parser in supported_parsers:
            result = parser(value, loc)
            if not isinstance(result, Invalid):
                return result
        return Invalid(value, ErrorFactory.create_unsupported_type(loc, supported_types))

    supported_types = typing.get_args(tp)
    provide_type_parser = model_config.type_parser_provider.provide_type_parser
    supported_parsers = [provide_type_parser(x, model_config) for x in supported_types]
    return parse_union
