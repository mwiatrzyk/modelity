import dataclasses
from enum import Enum
from typing import Any, Iterable, Sequence, cast

from modelity.loc import Loc
from modelity.unset import Unset


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
    UNSUPPORTED_DATETIME_FORMAT = "modelity.UnknownDatetimeFormat"
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
    """Object containing details of the single error.

    It is used for both parsing and validation stages of the model
    processing.
    """

    #: Location of the value in the model tree.
    loc: Loc

    #: Error code.
    #:
    #: This is a short string that precisely identifies the problem. It does
    #: not depend on the model or the field that is being processed.
    code: str

    #: Formatted error message.
    #:
    #: Contains human-readable error description based on :attr:`code` and
    #: :attr:`data`.
    msg: str

    #: Value for which this error is reported.
    value: Any = Unset

    #: Additional error data.
    #:
    #: This is closely related to the :attr:`code` and along with it can be
    #: used to render custom error messages.
    data: dict = dataclasses.field(default_factory=dict)


class ErrorFactory:
    """Factory class for creating built-in errors."""

    @staticmethod
    def invalid_literal(loc: Loc, allowed_values: Sequence):
        return Error(loc, ErrorCode.INVALID_LITERAL, "", data={"allowed_values": tuple(allowed_values)})

    @staticmethod
    def unsupported_type(loc: Loc, supported_types: Sequence[type]):
        return Error(loc, ErrorCode.UNSUPPORTED_TYPE, "", data={"supported_types": tuple(supported_types)})

    @staticmethod
    def required_missing(loc: Loc):
        return Error(loc, ErrorCode.REQUIRED_MISSING, "this field is required")

    @staticmethod
    def value_error(loc: Loc, msg: str):
        return Error(loc, ErrorCode.VALUE_ERROR, msg)

    @staticmethod
    def integer_required(loc: Loc):
        return Error(loc, ErrorCode.INTEGER_REQUIRED, "not a valid integer number")

    @staticmethod
    def value_too_low(loc: Loc, min_inclusive=None, min_exclusive=None):
        if min_inclusive is not None:
            msg, data = f"value must be >= {min_inclusive}", {"min_inclusive": min_inclusive}
        elif min_exclusive is not None:
            msg, data = f"value must be > {min_exclusive}", {"min_exclusive": min_exclusive}
        else:
            raise TypeError("one of the following arguments is required: min_inclusive, min_exclusive")
        return Error(loc, ErrorCode.VALUE_TOO_LOW, msg, data=data)

    @staticmethod
    def value_too_high(loc: Loc, max_inclusive=None, max_exclusive=None):
        if max_inclusive is not None:
            msg, data = f"value must be <= {max_inclusive}", {"max_inclusive": max_inclusive}
        elif max_exclusive is not None:
            msg, data = f"value must be < {max_exclusive}", {"max_exclusive": max_exclusive}
        else:
            raise TypeError("one of the following arguments is required: max_inclusive, max_exclusive")
        return Error(loc, ErrorCode.VALUE_TOO_HIGH, msg, data=data)

    @staticmethod
    def invalid_tuple_format(loc: Loc, expected_format: Sequence[type]) -> Error:
        return Error(loc, ErrorCode.INVALID_TUPLE_FORMAT, "", data={"expected_format": tuple(expected_format)})

    @staticmethod
    def float_required(loc: Loc):
        return Error(loc, ErrorCode.FLOAT_REQUIRED, "not a valid float number")

    @staticmethod
    def string_required(loc: Loc):
        return Error(loc, ErrorCode.STRING_REQUIRED, "not a valid string value")

    @staticmethod
    def mapping_required(loc: Loc):
        return Error(loc, ErrorCode.MAPPING_REQUIRED, "not a valid mapping value")

    @staticmethod
    def hashable_required(loc: Loc):
        return Error(loc, ErrorCode.HASHABLE_REQUIRED, "not a valid hashable value")

    @staticmethod
    def invalid_model(loc: Loc, model: Any):
        return Error(loc, ErrorCode.INVALID_MODEL, "")

    @staticmethod
    def value_too_short(loc: Loc, min_length: int):
        return Error(
            loc,
            ErrorCode.VALUE_TOO_SHORT,
            f"value too short; minimum length is {min_length}",
            data={"min_length": min_length},
        )

    @staticmethod
    def value_too_long(loc: Loc, max_length: int):
        return Error(
            loc,
            ErrorCode.VALUE_TOO_LONG,
            f"value too long; maximum length is {max_length}",
            data={"max_length": max_length},
        )

    @staticmethod
    def type_error(loc: Loc, msg: str):
        return Error(loc, ErrorCode.TYPE_ERROR, msg)

    @staticmethod
    def none_required(loc: Loc):
        return Error(loc, ErrorCode.NONE_REQUIRED, "this field can only be set to None")

    @staticmethod
    def bytes_required(loc: Loc):
        return Error(loc, ErrorCode.BYTES_REQUIRED, "this field can only be assigned with bytes")

    @staticmethod
    def unicode_decode_error(loc: Loc, codec: str):
        return Error(loc, ErrorCode.UNICODE_DECODE_ERROR, "", data={"codec": codec})

    @staticmethod
    def boolean_required(loc: Loc):
        return Error(loc, ErrorCode.BOOLEAN_REQUIRED, "not a valid boolean value")

    @staticmethod
    def datetime_required(loc: Loc):
        return Error(loc, ErrorCode.DATETIME_REQUIRED, "not a valid datetime value")

    @staticmethod
    def unsupported_datetime_format(loc: Loc, supported_formats: Sequence[str]):
        supported_formats_str = ", ".join(supported_formats)
        return Error(
            loc,
            ErrorCode.UNSUPPORTED_DATETIME_FORMAT,
            f"unsupported datetime format; supported formats are: {supported_formats_str}",
            data={"supported_formats": tuple(supported_formats)},
        )

    @staticmethod
    def invalid_enum(loc: Loc, typ: type[Enum]):
        typ_str = ", ".join(repr(x) for x in cast(Iterable, typ))
        return Error(
            loc,
            ErrorCode.INVALID_ENUM,
            f"unsupported enumerated value; supported ones are: {typ_str}",
            data={"typ": typ},
        )

    @staticmethod
    def iterable_required(loc: Loc) -> Error:
        """Create error signalling that iterable value is required.

        :param loc:
            The location of the error.
        """
        return Error(loc, ErrorCode.ITERABLE_REQUIRED, "not a valid iterable value")
