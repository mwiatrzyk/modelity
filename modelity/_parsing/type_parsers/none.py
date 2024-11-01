from modelity.error import ErrorCode, ErrorFactory
from modelity.invalid import Invalid
from modelity.providers import TypeParserProvider

provider = TypeParserProvider()


@provider.type_parser_factory(type(None))
def make_none_parser():

    def parse_none(value, loc):
        if value is None:
            return value
        return Invalid(value, ErrorFactory.create(loc, ErrorCode.NONE_REQUIRED))

    return parse_none
