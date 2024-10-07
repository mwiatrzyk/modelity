import typing

from modelity.error import Error
from modelity.invalid import Invalid
from modelity.interface import ITypeParserProvider
from modelity.providers import TypeParserProvider

provider = TypeParserProvider()


@provider.type_parser_factory(typing.Union)
def make_union_parser(provider: ITypeParserProvider, tp: type):

    def parse_union(value, loc):
        for type in supported_types:
            if isinstance(value, type):
                return value
        for parser in supported_parsers:
            result = parser(value, loc)
            if not isinstance(result, Invalid):
                return result
        return Invalid(value, Error.create_unsupported_type(loc, supported_types))

    supported_types = typing.get_args(tp)
    supported_parsers = [provider.provide_type_parser(x) for x in supported_types]
    return parse_union
