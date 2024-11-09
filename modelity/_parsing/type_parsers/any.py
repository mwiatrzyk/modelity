from typing import Any
from modelity.providers import TypeParserProvider

provider = TypeParserProvider()


@provider.type_parser_factory(Any)
def make_any_parser():

    def parse_any(value, loc, config):
        return value

    return parse_any
