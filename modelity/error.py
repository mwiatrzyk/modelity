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
    VALUE_TOO_LOW = "modelity.ValueTooLow"  # TODO: remove
    VALUE_TOO_HIGH = "modelity.ValueTooHigh"  # TODO: remove
    VALUE_TOO_SHORT = "modelity.ValueTooShort"  # TODO: remove
    VALUE_TOO_LONG = "modelity.ValueTooLong"  # TODO: remove
    REQUIRED_MISSING = "modelity.RequiredMissing"
    VALUE_ERROR = "modelity.ValueError"
    TYPE_ERROR = "modelity.TypeError"
    UNICODE_DECODE_ERROR = "modelity.UnicodeDecodeError"
    UNICODE_ENCODE_ERROR = "modelity.UnicodeEncodeError"
    GE_FAILED = "modelity.GeFailed"
    GT_FAILED = "modelity.GtFailed"
    LE_FAILED = "modelity.LeFailed"
    LT_FAILED = "modelity.LtFailed"
    MIN_LEN_FAILED = "modelity.MinLenFailed"
    MAX_LEN_FAILED = "modelity.MaxLenFailed"
    REGEX_FAILED = "modelity.RegexFailed"
    UNION_PARSING_FAILED = "modelity.UnionParsingFailed"
    TUPLE_TOO_SHORT = "modelity.TUPLE_TOO_SHORT"
    TUPLE_TOO_LONG = "modelity.TUPLE_TOO_LONG"


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


class ErrorFactory:  # TODO: flatten the errors to be more generic, f.e. value_out_of_range for both enums and literals
    """Factory class for creating built-in errors."""

    @staticmethod
    def invalid_literal(loc: Loc, allowed_values: Sequence, value: Any = Unset):  # TODO: make value required
        return Error(
            loc,
            ErrorCode.INVALID_LITERAL,
            "invalid literal",
            value=value,
            data={"allowed_values": tuple(allowed_values)},
        )

    @staticmethod
    def unsupported_type(loc: Loc, supported_types: Sequence[type], value: Any = Unset):  # TODO: make value required
        """Error reported when input value has unsupported type that cannot be
        converted to a desired type.

        For example, integers cannot be converted to lists.

        :param loc:
            Error location.

        :param value:
            Incorrect value.

        :param supported_types:
            Sequence of supported types.
        """
        supported_types = tuple(supported_types)
        supported_types_str = ", ".join(repr(x) for x in supported_types)
        return Error(
            loc,
            ErrorCode.UNSUPPORTED_TYPE,
            f"unsupported value type; supported types are: {supported_types_str}",
            value=value,
            data={"supported_types": supported_types},
        )

    @staticmethod
    def required_missing(loc: Loc):
        return Error(loc, ErrorCode.REQUIRED_MISSING, "this field is required")

    @staticmethod
    def value_error(loc: Loc, msg: str):
        return Error(loc, ErrorCode.VALUE_ERROR, msg)

    @staticmethod
    def integer_required(loc: Loc, value: Any = Unset):  # TODO: make value required
        return Error(loc, ErrorCode.INTEGER_REQUIRED, "not a valid integer number", value=value)

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
    def invalid_tuple_format(
        loc: Loc, expected_format: Sequence[type], value: Any = Unset
    ) -> Error:  # TODO: make value required
        expected_format = tuple(expected_format)
        expected_format_str = ", ".join(repr(x) for x in expected_format)
        return Error(
            loc,
            ErrorCode.INVALID_TUPLE_FORMAT,
            f"invalid tuple format; accepted format is: {expected_format_str}",
            value=value,
            data={"expected_format": expected_format},
        )

    @staticmethod
    def float_required(loc: Loc, value: Any = Unset):  # TODO: make value required
        return Error(loc, ErrorCode.FLOAT_REQUIRED, "not a valid float number", value=value)

    @staticmethod
    def string_required(loc: Loc, value: Any = Unset):  # TODO: make value required
        return Error(loc, ErrorCode.STRING_REQUIRED, "not a valid string value", value=value)

    @staticmethod
    def mapping_required(loc: Loc, value: Any = Unset):  # TODO: make value required
        return Error(loc, ErrorCode.MAPPING_REQUIRED, "not a valid mapping value", value=value)

    @staticmethod
    def hashable_required(loc: Loc, value: Any = Unset):  # TODO: make value required
        return Error(loc, ErrorCode.HASHABLE_REQUIRED, "input value must be hashable", value=value)

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
    def none_required(loc: Loc, value: Any = Unset):  # TODO: make value required
        return Error(loc, ErrorCode.NONE_REQUIRED, "this field can only be set to None", value=value)

    @staticmethod
    def bytes_required(loc: Loc, value: Any = Unset):  # TODO: make value required
        return Error(loc, ErrorCode.BYTES_REQUIRED, "this field can only be set to bytes", value=value)

    @staticmethod
    def unicode_decode_error(loc: Loc, codecs_tried: Sequence[str], value: Any = Unset):  # TODO: make value required
        return Error(
            loc,
            ErrorCode.UNICODE_DECODE_ERROR,
            "unable to decode bytes; codecs tried:",
            data={"codecs_tried": tuple(codecs_tried)},
        )

    @staticmethod
    def unicode_encode_error(loc: Loc, value: Any, encoding: str):
        return Error(
            loc,
            ErrorCode.UNICODE_ENCODE_ERROR,
            f"unable to encode string using {encoding} encoding",
            value,
            data={"encoding": encoding},
        )

    @staticmethod
    def boolean_required(loc: Loc, value: Any = Unset):  # TODO: make value required
        return Error(loc, ErrorCode.BOOLEAN_REQUIRED, "not a valid boolean value", value=value)

    @staticmethod
    def datetime_required(loc: Loc, value: Any = Unset):  # TODO: make value required
        return Error(loc, ErrorCode.DATETIME_REQUIRED, "not a valid datetime value", value=value)

    @staticmethod
    def unsupported_datetime_format(
        loc: Loc, supported_formats: Sequence[str], value: Any = Unset
    ):  # TODO: make value required
        supported_formats_str = ", ".join(supported_formats)
        return Error(
            loc,
            ErrorCode.UNSUPPORTED_DATETIME_FORMAT,
            f"unsupported datetime format; supported formats are: {supported_formats_str}",
            value=value,
            data={"supported_formats": tuple(supported_formats)},
        )

    @staticmethod
    def invalid_enum(loc: Loc, typ: type[Enum], value: Any = Unset):  # TODO: make value required
        typ_str = ", ".join(repr(x) for x in cast(Iterable, typ))
        return Error(
            loc,
            ErrorCode.INVALID_ENUM,
            f"invalid enumerated value; valid ones are: {typ_str}",
            value=value,
            data={"typ": typ},
        )

    @staticmethod
    def iterable_required(loc: Loc, value: Any = Unset) -> Error:  # TODO: make value required
        """Create error signalling that iterable value is required.

        :param loc:
            The location of the error.
        """
        return Error(loc, ErrorCode.ITERABLE_REQUIRED, "not a valid iterable value", value=value)

    @staticmethod
    def ge_failed(loc: Loc, value: Any, min_inclusive: Any) -> Error:
        return Error(
            loc, ErrorCode.GE_FAILED, f"the value must be >= {min_inclusive}", value, {"min_inclusive": min_inclusive}
        )

    @staticmethod
    def gt_failed(loc: Loc, value: Any, min_exclusive: Any) -> Error:
        return Error(
            loc, ErrorCode.GT_FAILED, f"the value must be > {min_exclusive}", value, {"min_exclusive": min_exclusive}
        )

    @staticmethod
    def le_failed(loc: Loc, value: Any, max_inclusive: Any) -> Error:
        return Error(
            loc, ErrorCode.LE_FAILED, f"the value must be <= {max_inclusive}", value, {"max_inclusive": max_inclusive}
        )

    @staticmethod
    def lt_failed(loc: Loc, value: Any, max_exclusive: Any) -> Error:
        return Error(
            loc, ErrorCode.LT_FAILED, f"the value must be < {max_exclusive}", value, {"max_exclusive": max_exclusive}
        )

    @staticmethod
    def min_len_failed(loc: Loc, value: Any, min_len: int) -> Error:
        return Error(
            loc,
            ErrorCode.MIN_LEN_FAILED,
            f"the value is too short; minimum length is {min_len}",
            value,
            {"min_len": min_len},
        )

    @staticmethod
    def max_len_failed(loc: Loc, value: Any, max_len: int) -> Error:
        return Error(
            loc,
            ErrorCode.MAX_LEN_FAILED,
            f"the value is too long; maximum length is {max_len}",
            value,
            {"max_len": max_len},
        )

    @staticmethod
    def regex_failed(loc: Loc, value: Any, pattern: str) -> Error:
        return Error(
            loc,
            ErrorCode.REGEX_FAILED,
            f"the value does not match regex pattern: {pattern}",
            value,
            {"pattern": pattern},
        )

    @staticmethod
    def union_parsing_failed(loc: Loc, value: Any, types_tried: Sequence[type]) -> Error:
        types_tried = tuple(types_tried)
        types_tried_str = ", ".join(repr(x) for x in types_tried)
        return Error(
            loc,
            ErrorCode.UNION_PARSING_FAILED,
            f"not a valid union value; types tried: {types_tried_str}",
            value=value,
            data={"types_tried": types_tried},
        )

    @staticmethod
    def tuple_too_short(loc: Loc, value: Any, required_len: int) -> Error:
        """Error reported when typed tuple with constrained size has too few
        elements.

        :param loc:
            Error location.

        :param value:
            Incorrect value.

        :param required_len:
            Expected tuple length.
        """
        return Error(
            loc,
            ErrorCode.TUPLE_TOO_SHORT,
            f"tuple too short; required length is {required_len}",
            value=value,
            data={"required_len": required_len},
        )

    @staticmethod
    def tuple_too_long(loc: Loc, value: Any, required_len: int) -> Error:
        """Error reported when typed tuple with constrained size has too many
        elements.

        :param loc:
            Error location.

        :param value:
            Incorrect value.

        :param required_len:
            Expected tuple length.
        """
        return Error(
            loc,
            ErrorCode.TUPLE_TOO_LONG,
            f"tuple too short; required length is {required_len}",
            value=value,
            data={"required_len": required_len},
        )
