import enum
from typing import Callable, Iterable, cast

from modelity.error import ErrorCode
from modelity.interface import IConfig
from modelity.invalid import Invalid
from modelity.providers import TypeParserProvider

provider = TypeParserProvider()


@provider.type_parser_factory(enum.Enum)
def make_enum_parser(tp: enum.Enum):

    def parse_enum(value, loc, config: IConfig):
        try:
            return cast(Callable, tp)(value)
        except ValueError:
            return Invalid(value, config.create_error(loc, ErrorCode.INVALID_ENUM, {"allowed_values": tuple(cast(Iterable, tp))}))

    return parse_enum
