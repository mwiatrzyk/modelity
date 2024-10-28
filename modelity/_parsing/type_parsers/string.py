from modelity.error import Error, ErrorCode, ErrorFactory
from modelity.invalid import Invalid
from modelity.providers import TypeParserProvider

provider = TypeParserProvider()


@provider.type_parser_factory(str)
def make_string_parser():

    def parse_string(value, loc):
        if isinstance(value, str):
            return value
        if isinstance(value, bytes):
            try:
                return value.decode()
            except UnicodeDecodeError:
                return Invalid(value, ErrorFactory.unicode_decode_error(loc, "utf-8"))
        return Invalid(value, ErrorFactory.string_required(loc))

    return parse_string


@provider.type_parser_factory(bytes)
def make_bytes_parser():

    def parse_bytes(value, loc):
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return value.encode()
        return Invalid(value, ErrorFactory.bytes_required(loc))

    return parse_bytes
