from typing import Literal, get_args
from modelity.error import ErrorFactory
from modelity.invalid import Invalid
from modelity.providers import TypeParserProvider

provider = TypeParserProvider()


@provider.type_parser_factory(Literal)
def make_literal_parser(tp: type):

    def parse_literal(value, loc):
        if value not in supported_values:
            return Invalid(value, ErrorFactory.create_invalid_literal(loc, supported_values))
        return value

    supported_values = get_args(tp)
    return parse_literal
