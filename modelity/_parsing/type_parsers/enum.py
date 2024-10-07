import enum

from modelity.error import ErrorFactory
from modelity.invalid import Invalid
from modelity.providers import TypeParserProvider

provider = TypeParserProvider()


@provider.type_parser_factory(enum.Enum)
def make_enum_parser(tp: enum.Enum):

    def parse_enum(value, loc):
        try:
            return tp(value)
        except ValueError:
            return Invalid(value, ErrorFactory.create_invalid_enum(loc, tp))

    return parse_enum
