from modelity.error import Error, ErrorCode
from modelity.invalid import Invalid
from modelity.parsing.registry import TypeParserRegistry

_TRUE_VALUES = (True, 1, "on", "On", "ON", "true", "True", "TRUE")
_FALSE_VALUES = (False, 0, "off", "Off", "OFF", "false", "False", "FALSE")

registry = TypeParserRegistry()


@registry.type_parser_factory(bool)
def make_bool_parser():

    def parse_bool(value, loc):
        if value in _TRUE_VALUES:
            return True
        if value in _FALSE_VALUES:
            return False
        return Invalid(value, Error.create(loc, ErrorCode.BOOLEAN_REQUIRED))

    return parse_bool
