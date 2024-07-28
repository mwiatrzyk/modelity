from modelity.exc import ParsingError
from modelity.parsing.registry import ParserRegistry

registry = ParserRegistry()


@registry.type_parser_factory(type(None))
def make_none_parser():

    def parse_none(value):
        if value is not None:
            raise ParsingError("None value required")
        return value

    return parse_none


@registry.type_parser_factory(int)
def make_int_parser():

    def parse_int(value):
        try:
            return int(value)
        except (ValueError, TypeError):
            raise ParsingError("Not a valid integer number")

    return parse_int


@registry.type_parser_factory(str)
def make_str_parser():

    def parse_str(value):
        if not isinstance(value, str):
            raise ParsingError("String value required")
        return value

    return parse_str
