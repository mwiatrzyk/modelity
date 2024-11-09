from modelity.error import ErrorCode
from modelity.interface import IConfig
from modelity.invalid import Invalid
from modelity.providers import TypeParserProvider

provider = TypeParserProvider()


@provider.type_parser_factory(type(None))
def make_none_parser():

    def parse_none(value, loc, config: IConfig):
        if value is None:
            return value
        return Invalid(value, config.create_error(loc, ErrorCode.NONE_REQUIRED))

    return parse_none
