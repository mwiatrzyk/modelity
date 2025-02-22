"""Parser factories for the built-in simple types."""

from datetime import datetime
from enum import Enum
from numbers import Number
from typing import Any, Callable, Literal, Optional, Sequence, cast, get_args, get_origin

from modelity.error import Error, ErrorFactory
from modelity.exc import UnsupportedTypeError
from modelity.interface import IParser
from modelity.loc import Loc
from modelity.unset import Unset

_DEFAULT_TRUE_LITERALS = {True, 1, "True"}
_DEFAULT_FALSE_LITERALS = {False, 0, "False"}
_DEFAULT_DATETIME_ISO8601_FORMATS = [
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S",
    "%Y%m%d%H%M%S%z",
    "%Y%m%d%H%M%S",
    "%Y-%m-%d",
    "%Y%m%d",
]


def make_any_parser() -> IParser:
    """Make parser for the :class:`typing.Any` type."""

    def parse_any(errors, loc, value):
        return value

    return parse_any


def make_bool_parser(true_literals: Optional[set] = None, false_literals: Optional[set] = None) -> IParser:
    f"""Make type parser for the :class:`bool` Python type.

    Can be customized with literals for both ``True`` and ``False`` output
    values.

    :param true_literals:
        Literals evaluating to ``True``.

        If not given, then built-in literals are used: {', '.join(repr(x) for x in _DEFAULT_TRUE_LITERALS)}

    :param false_literals:
        Literals evaluating to ``False``.

        If not given, then built-in literals are used: {', '.join(repr(x) for x in _DEFAULT_FALSE_LITERALS)}
    """

    def parse_bool(errors: list[Error], loc: Loc, value: Any):
        if value in true_literals:
            return True
        if value in false_literals:
            return False
        errors.append(ErrorFactory.boolean_required(loc, value))
        return Unset

    true_literals = true_literals or _DEFAULT_TRUE_LITERALS
    false_literals = false_literals or _DEFAULT_FALSE_LITERALS
    return parse_bool


def make_datetime_parser(formats: Optional[Sequence[str]] = None) -> IParser:
    """Make parser for the :class:`datetime.datetime` type.

    By default, parses ISO8601 datetime strings, but this behavior can be
    changed by specifying list of custom formats to try.

    :param formats:
        List of user-defined datetime formats.

        If given, then default ISO8601 is no longer used, just the format given
        by the user are tried from left to right until the matching one is
        found for given input value.
    """

    def parse_datetime(errors: list[Error], loc: Loc, value: Any):
        if isinstance(value, datetime):
            return value
        if not isinstance(value, str):
            errors.append(ErrorFactory.datetime_required(loc, value))
            return Unset
        for fmt in formats_tuple:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                pass
        errors.append(ErrorFactory.unsupported_datetime_format(loc, formats_tuple, value))
        return Unset

    formats_tuple = tuple(cast(list[str], formats or _DEFAULT_DATETIME_ISO8601_FORMATS))
    return parse_datetime


def make_enum_parser(typ: type[Enum]) -> IParser:
    """Make parser for an enumerated type.

    :param typ:
        Enumerate typed to make parser for.
    """

    def parse_enum(errors: list[Error], loc: Loc, value: Any):
        try:
            return typ(value)
        except ValueError:
            errors.append(ErrorFactory.invalid_enum(loc, typ, value))
            return Unset

    assert isinstance(typ, type) and issubclass(
        typ, Enum
    ), f"{make_enum_parser.__name__!r} can only be used with Enum subclasses"
    return parse_enum


def make_literal_parser(typ) -> IParser:
    """Make parser for a literal type.

    Literals are similar to enums, but allow values of different types to
    compose a set of allowed values.

    :param typ:
        The literal type (:class:`typing.Literal`) to make parser for.
    """

    def parse_literal(errors: list[Error], loc: Loc, value: Any):
        if value in allowed_values:
            return value
        errors.append(ErrorFactory.invalid_literal(loc, allowed_values, value))
        return Unset

    origin = get_origin(typ)
    assert origin is Literal, f"{make_literal_parser.__name__!r} can only be used with Literal types"
    allowed_values = get_args(typ)
    return parse_literal


def make_none_parser() -> IParser:
    """Make parser for the ``type(None)`` type.

    The parser produced by this function will only accept ``None`` value. It
    was added for use in complex types, like unions, to avoid special handling
    of the ``None`` values. Direct use of this parser is rather pointless.
    """

    def parse_none(errors: list[Error], loc: Loc, value: Any):
        if value is None:
            return value
        errors.append(ErrorFactory.none_required(loc, value))
        return Unset

    return parse_none


def make_int_parser() -> IParser:
    """Make parser for the integer numbers."""

    def parse_int(errors: list[Error], loc: Loc, value: Any):
        try:
            return int(value)
        except (ValueError, TypeError):
            errors.append(ErrorFactory.integer_required(loc, value))
            return Unset

    return parse_int


def make_float_parser() -> IParser:
    """Make parser for the floating point numbers."""

    def parse_float(errors: list[Error], loc: Loc, value: Any):
        try:
            return float(value)
        except (ValueError, TypeError):
            errors.append(ErrorFactory.float_required(loc, value))
            return Unset

    return parse_float


def make_number_parser(typ: type[Number]) -> IParser:
    """Make parser for the any numeric type.

    Will raise :exc:`modelity.exc.UnsupportedTypeError` if *typ* is not a
    numeric type that is known to Modelity library.

    :param typ:
        The numeric type to make parser for.
    """
    # IMPORTANT: Remember to add any new numeric type also here, as this
    # function aggregates all numeric types.
    assert issubclass(typ, Number), f"{make_number_parser.__name__!r} can only be used with Number subclasses"
    if issubclass(typ, int):
        return make_int_parser()
    if issubclass(typ, float):
        return make_float_parser()
    raise UnsupportedTypeError(typ)


def make_str_parser(encodings: Optional[Sequence[str]] = None) -> IParser:
    """Make parser for the built-in :class:`str` type.

    :param encodings:
        Encodings to try when :class:`bytes` object is given as the input
        value.

        This is a sequence of encodings to try, from left-to-right. Decoding
        stops at first encoding that was able to decode input value, so bear in
        mind to put most promising encodings first.

        By default, only ``utf-8`` is used.
    """

    def parse_str(errors: list[Error], loc: Loc, value: Any):
        if isinstance(value, str):
            return value
        if isinstance(value, bytes):
            for enc in selected_encodings:
                try:
                    return value.decode(enc)
                except UnicodeDecodeError:
                    pass
            else:
                errors.append(ErrorFactory.unicode_decode_error(loc, selected_encodings, value))
                return Unset
        errors.append(ErrorFactory.string_required(loc, value))
        return Unset

    selected_encodings = tuple(encodings or ["utf-8"])
    return parse_str


def make_bytes_parser(encoding: Optional[str] = None) -> IParser:
    """Make parser for the built-in :class:`bytes` type.

    :param encoding:
        Encoding to use when encoding input :class:`str` object into resulting
        :class:`bytes` object.

        If not given, then ``utf-8`` is used.
    """

    def parse_bytes(errors: list[Error], loc: Loc, value: Any):
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            try:
                return value.encode(selected_encoding)
            except UnicodeEncodeError:
                errors.append(ErrorFactory.unicode_encode_error(loc, value, selected_encoding))
                return Unset
        errors.append(ErrorFactory.bytes_required(loc, value))
        return Unset

    selected_encoding = encoding or "utf-8"
    return parse_bytes
