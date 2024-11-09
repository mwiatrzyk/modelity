from modelity.error import ErrorCode
from modelity.interface import IConfig
from modelity.invalid import Invalid
from modelity.providers import TypeParserProvider

_TRUE_VALUES = (True, 1, "on", "true")
_FALSE_VALUES = (False, 0, "off", "false")

provider = TypeParserProvider()


@provider.type_parser_factory(bool)
def make_bool_parser():

    def parse_bool(value, loc, config: IConfig):
        if value in _TRUE_VALUES:
            return True
        if value in _FALSE_VALUES:
            return False
        return Invalid(value, config.create_error(loc, ErrorCode.BOOLEAN_REQUIRED))

    return parse_bool
