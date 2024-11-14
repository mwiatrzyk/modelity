import dataclasses
from typing import Optional, Tuple, cast

from modelity.interface import IErrorCreator
from modelity.loc import Loc


class ErrorCode:
    """Class containing constants with all built-in error codes."""
    NONE_REQUIRED = "modelity.NoneRequired"
    INTEGER_REQUIRED = "modelity.IntegerRequired"
    STRING_REQUIRED = "modelity.StringRequired"
    BYTES_REQUIRED = "modelity.BytesRequired"
    FLOAT_REQUIRED = "modelity.FloatRequired"
    BOOLEAN_REQUIRED = "modelity.BooleanRequired"
    ITERABLE_REQUIRED = "modelity.IterableRequired"
    HASHABLE_REQUIRED = "modelity.HashableRequired"
    MAPPING_REQUIRED = "modelity.MappingRequired"
    DATETIME_REQUIRED = "modelity.DatetimeRequired"
    UNKNOWN_DATETIME_FORMAT = "modelity.UnknownDatetimeFormat"
    UNSUPPORTED_TYPE = "modelity.UnsupportedType"
    INVALID_TUPLE_FORMAT = "modelity.InvalidTupleFormat"
    INVALID_ENUM = "modelity.InvalidEnum"
    INVALID_LITERAL = "modelity.InvalidLiteral"
    INVALID_MODEL = "modelity.InvalidModel"
    VALUE_TOO_LOW = "modelity.ValueTooLow"
    VALUE_TOO_HIGH = "modelity.ValueTooHigh"
    VALUE_TOO_SHORT = "modelity.ValueTooShort"
    VALUE_TOO_LONG = "modelity.ValueTooLong"
    REQUIRED_MISSING = "modelity.RequiredMissing"
    VALUE_ERROR = "modelity.ValueError"
    TYPE_ERROR = "modelity.TypeError"
    UNICODE_DECODE_ERROR = "modelity.UnicodeDecodeError"


@dataclasses.dataclass
class Error:
    """Object describing error."""

    #: Location of the error.
    loc: Loc

    #: Error code.
    code: str

    #: Optional error data, with format depending on the :attr:`code`.
    data: Optional[dict] = None

    #: Formatted error message.
    msg: Optional[str] = None


def get_builtin_error_creator() -> IErrorCreator:
    """Get error creator function for built-in types."""

    def create_unknown_datetime_error(loc: Loc, data: Optional[dict]) -> Error:
        assert data is not None
        supported_formats = cast(Tuple[str], data["supported_formats"])
        return Error(loc, ErrorCode.UNKNOWN_DATETIME_FORMAT, data, f"unknown datetime format; supported formats are: {', '.join(supported_formats)}")

    def create_invalid_enum(loc: Loc, data: Optional[dict]) -> Error:
        assert data is not None
        allowed_values = cast(tuple, data["allowed_values"])
        msg = f"not a valid enum; allowed values are: {', '.join(repr(x) for x in allowed_values)}"
        return Error(loc, ErrorCode.INVALID_ENUM, data, msg)

    def create_invalid_literal(loc: Loc, data: Optional[dict]) -> Error:
        assert data is not None
        allowed_values = cast(tuple, data["allowed_values"])
        msg = f"not a valid literal; allowed values are: {', '.join(repr(x) for x in allowed_values)}"
        return Error(loc, ErrorCode.INVALID_LITERAL, data, msg)

    def create_invalid_model(loc: Loc, data: Optional[dict]) -> Error:
        assert data is not None
        model_type = cast(type, data["model_type"])
        msg = f"not a valid {model_type.__name__!r} model value; need either a mapping, or an instance of {model_type.__name__!r} model"
        return Error(loc, ErrorCode.INVALID_MODEL, data, msg)

    def create_unicode_decode_error(loc: Loc, data: Optional[dict]) -> Error:
        assert data is not None
        codec = cast(str, data["codec"])
        return Error(loc, ErrorCode.UNICODE_DECODE_ERROR, data, f"could not decode value using {codec!r} codec")

    def create_unsupported_type_error(loc: Loc, data: Optional[dict]) -> Error:
        assert data is not None
        supported_types = cast(Tuple[type], data["supported_types"])
        msg = f"value of unsupported type given; supported types are: {', '.join(repr(x) for x in supported_types)}"
        return Error(loc, ErrorCode.UNSUPPORTED_TYPE, data, msg)

    def create_invalid_tuple_format_error(loc: Loc, data: Optional[dict]) -> Error:
        assert data is not None
        expected_format = cast(tuple, data["expected_format"])
        msg = f"invalid format of a tuple value; expected format is: {expected_format!r}"
        return Error(loc, ErrorCode.INVALID_TUPLE_FORMAT, data, msg)

    def create_value_too_low_error(loc: Loc, data: Optional[dict]) -> Error:
        assert data is not None
        min_inclusive = data.get("min_inclusive")
        min_exclusive = data.get("min_exclusive")
        msg = "value must be"
        if min_inclusive is not None:
            msg = f"{msg} >= {min_inclusive}"
        elif min_exclusive is not None:
            msg = f"{msg} > {min_exclusive}"
        return Error(loc, ErrorCode.VALUE_TOO_LOW, data, msg)

    def create_value_too_high_error(loc: Loc, data: Optional[dict]) -> Error:
        assert data is not None
        max_inclusive = data.get("max_inclusive")
        max_exclusive = data.get("max_exclusive")
        msg = "value must be"
        if max_inclusive is not None:
            msg = f"{msg} <= {max_inclusive}"
        elif max_exclusive is not None:
            msg = f"{msg} < {max_exclusive}"
        return Error(loc, ErrorCode.VALUE_TOO_HIGH, data, msg)

    def create_value_too_short_error(loc: Loc, data: Optional[dict]) -> Error:
        assert data is not None
        min_length = data["min_length"]
        return Error(loc, ErrorCode.VALUE_TOO_SHORT, data, f"value too short; minimum length is {min_length}")

    def create_value_too_long_error(loc: Loc, data: Optional[dict]) -> Error:
        assert data is not None
        max_length = data["max_length"]
        return Error(loc, ErrorCode.VALUE_TOO_LONG, data, f"value too long; maximum length is {max_length}")

    def create_error(loc: Loc, code: str, data: Optional[dict]=None) -> Error:
        if code == ErrorCode.REQUIRED_MISSING:
            return Error(loc, code, data, "this field is required")
        if code == ErrorCode.NONE_REQUIRED:
            return Error(loc, code, data, "not a None value")
        if code == ErrorCode.INTEGER_REQUIRED:
            return Error(loc, code, data, "not a valid integer number")
        if code == ErrorCode.FLOAT_REQUIRED:
            return Error(loc, code, data, "not a valid float number")
        if code == ErrorCode.STRING_REQUIRED:
            return Error(loc, code, data, "not a valid string value")
        if code == ErrorCode.BYTES_REQUIRED:
            return Error(loc, code, data, "not a valid bytes value")
        if code == ErrorCode.BOOLEAN_REQUIRED:
            return Error(loc, code, data, "not a valid boolean value")
        if code == ErrorCode.DATETIME_REQUIRED:
            return Error(loc, code, data, "not a valid datetime value")
        if code == ErrorCode.MAPPING_REQUIRED:
            return Error(loc, code, data, "not a valid mapping value")
        if code == ErrorCode.ITERABLE_REQUIRED:
            return Error(loc, code, data, "not a valid iterable value")
        if code == ErrorCode.HASHABLE_REQUIRED:
            return Error(loc, code, data, "not a valid hashable value")
        if code == ErrorCode.UNKNOWN_DATETIME_FORMAT:
            return create_unknown_datetime_error(loc, data)
        if code == ErrorCode.INVALID_ENUM:
            return create_invalid_enum(loc, data)
        if code == ErrorCode.INVALID_LITERAL:
            return create_invalid_literal(loc, data)
        if code == ErrorCode.INVALID_MODEL:
            return create_invalid_model(loc, data)
        if code == ErrorCode.UNICODE_DECODE_ERROR:
            return create_unicode_decode_error(loc, data)
        if code == ErrorCode.UNSUPPORTED_TYPE:
            return create_unsupported_type_error(loc, data)
        if code == ErrorCode.INVALID_TUPLE_FORMAT:
            return create_invalid_tuple_format_error(loc, data)
        if code == ErrorCode.VALUE_TOO_LOW:
            return create_value_too_low_error(loc, data)
        if code == ErrorCode.VALUE_TOO_HIGH:
            return create_value_too_high_error(loc, data)
        if code == ErrorCode.VALUE_TOO_SHORT:
            return create_value_too_short_error(loc, data)
        if code == ErrorCode.VALUE_TOO_LONG:
            return create_value_too_long_error(loc, data)
        return Error(loc, code, data)

    return create_error
