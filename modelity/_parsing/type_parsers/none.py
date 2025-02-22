from modelity.error import Error, ErrorCode, ErrorFactory
from modelity.interface import IConfig
from modelity.invalid import Invalid
from modelity.providers import TypeParserProvider

provider = TypeParserProvider()


@provider.type_parser_factory(type(None))
def make_none_parser():

    def parse_none(value, loc, config: IConfig):
        if value is None:
            return value
        return Invalid(value, ErrorFactory.none_required(loc))

    return parse_none
