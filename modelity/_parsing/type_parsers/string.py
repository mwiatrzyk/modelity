from modelity.error import Error, ErrorCode
from modelity.invalid import Invalid
from modelity.providers import TypeParserProvider

provider = TypeParserProvider()


@provider.type_parser_factory(str)
def make_string_parser():

    def parse_string(value, loc):
        if isinstance(value, str):
            return value
        return Invalid(value, Error.create(loc, ErrorCode.STRING_REQUIRED))

    return parse_string
