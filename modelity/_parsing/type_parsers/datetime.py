import datetime

from modelity.error import ErrorCode
from modelity.interface import IConfig
from modelity.invalid import Invalid
from modelity.providers import TypeParserProvider

provider = TypeParserProvider()


@provider.type_parser_factory(datetime.datetime)
def make_datetime_parser():

    def parse_datetime(value, loc, config: IConfig):
        if isinstance(value, datetime.datetime):
            return value
        if not isinstance(value, str):
            return Invalid(value, config.create_error(loc, ErrorCode.DATETIME_REQUIRED))
        for format_ in supported_formats:
            try:
                return datetime.datetime.strptime(value, format_)
            except ValueError:
                pass
        return Invalid(
            value, config.create_error(loc, ErrorCode.UNKNOWN_DATETIME_FORMAT, {"supported_formats": supported_formats_human_readable})
        )

    supported_formats = (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y%m%d%H%M%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y%m%d%H%M%S%z",
    )
    supported_formats_human_readable = tuple(x.replace("%", "") for x in supported_formats)
    return parse_datetime
