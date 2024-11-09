from typing import Literal, get_args

from modelity.error import ErrorCode
from modelity.interface import IConfig
from modelity.invalid import Invalid
from modelity.providers import TypeParserProvider

provider = TypeParserProvider()


@provider.type_parser_factory(Literal)
def make_literal_parser(tp: type):

    def parse_literal(value, loc, config: IConfig):
        if value not in supported_values:
            return Invalid(value, config.create_error(loc, ErrorCode.INVALID_LITERAL, {"allowed_values": supported_values}))
        return value

    supported_values = get_args(tp)
    return parse_literal
