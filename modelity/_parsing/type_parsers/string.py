from modelity.error import ErrorCode
from modelity.interface import IConfig
from modelity.invalid import Invalid
from modelity.providers import TypeParserProvider

provider = TypeParserProvider()


@provider.type_parser_factory(str)
def make_string_parser():

    def parse_string(value, loc, config: IConfig):
        if isinstance(value, str):
            return value
        if isinstance(value, bytes):
            try:
                return value.decode()
            except UnicodeDecodeError:
                return Invalid(value, config.create_error(loc, ErrorCode.UNICODE_DECODE_ERROR, {"codec": "utf-8"}))
        return Invalid(value, config.create_error(loc, ErrorCode.STRING_REQUIRED))

    return parse_string


@provider.type_parser_factory(bytes)
def make_bytes_parser():

    def parse_bytes(value, loc, config: IConfig):
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return value.encode()
        return Invalid(value, config.create_error(loc, ErrorCode.BYTES_REQUIRED))

    return parse_bytes
