import dataclasses
from enum import Enum
from numbers import Number
from typing import Any, Iterable, Optional, Sequence, cast

from modelity.loc import Loc
from modelity.unset import Unset


class ErrorCode:
    """Class containing constants with all built-in error codes."""

    INVALID_DICT = "modelity.INVALID_DICT"
    INVALID_LIST = "modelity.INVALID_LIST"
    INVALID_SET = "modelity.INVALID_SET"
    INVALID_TUPLE = "modelity.INVALID_TUPLE"
    UNSUPPORTED_TUPLE_FORMAT = "modelity.UNSUPPORTED_TUPLE_FORMAT"
    INVALID_MODEL = "modelity.INVALID_MODEL"
    INVALID_BOOL = "modelity.INVALID_BOOL"
    INVALID_DATETIME = "modelity.INVALID_DATETIME"
    INVALID_DATE = "modelity.INVALID_DATE"
    UNSUPPORTED_DATETIME_FORMAT = "modelity.UNSUPPORTED_DATETIME_FORMAT"
    UNSUPPORTED_DATE_FORMAT = "modelity.UNSUPPORTED_DATE_FORMAT"
    INVALID_NUMBER = "modelity.INVALID_NUMBER"
    VALUE_OUT_OF_RANGE = "modelity.VALUE_OUT_OF_RANGE"
    UNSUPPORTED_VALUE_TYPE = "modelity.UNSUPPORTED_VALUE_TYPE"
    GE_CONSTRAINT_FAILED = "modelity.GE_CONSTRAINT_FAILED"
    GT_CONSTRAINT_FAILED = "modelity.GT_CONSTRAINT_FAILED"
    LE_CONSTRAINT_FAILED = "modelity.LE_CONSTRAINT_FAILED"
    LT_CONSTRAINT_FAILED = "modelity.LT_CONSTRAINT_FAILED"
    MIN_LEN_CONSTRAINT_FAILED = "modelity.MIN_LEN_CONSTRAINT_FAILED"
    MAX_LEN_CONSTRAINT_FAILED = "modelity.MAX_LEN_CONSTRAINT_FAILED"
    REGEX_CONSTRAINT_FAILED = "modelity.REGEX_CONSTRAINT_FAILED"
    REQUIRED_MISSING = "modelity.REQUIRED_MISSING"
    EXCEPTION = "modelity.EXCEPTION"
    PARSING_ERROR = "modelity.PARSING_ERROR"


@dataclasses.dataclass
class Error:
    """Object containing details of the single error.

    It is used for both parsing and validation stages of the model
    processing.
    """

    #: The location of the incorrect value.
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

    #: The incorrect value (if applicable).
    value: Any = Unset

    #: Additional error data.
    #:
    #: This is closely related to the :attr:`code` and along with it can be
    #: used to render custom error messages.
    data: dict = dataclasses.field(default_factory=dict)

    @property
    def value_type(self) -> type:
        """The type of the incorrect value."""
        return type(self.value)


class ErrorFactory:  # TODO: flatten the errors to be more generic, f.e. value_out_of_range for both enums and literals
    """Factory class for creating built-in errors."""

    @staticmethod
    def parsing_error(loc: Loc, value: Any, msg: str, typ: Any) -> Error:
        """Generic error to be reported when *value* could not be parsed to a
        given *target_type*.

        :param loc:
            The location of the error.

        :param value:
            Tha value that failed parsing.

        :param msg:
            The error message.

        :param typ:
            The type *value* was tried to be parsed to.
        """
        return Error(loc, ErrorCode.PARSING_ERROR, msg, value, {"typ": typ})

    @staticmethod
    def invalid_dict(loc: Loc, value: Any) -> Error:
        """Error reported when value is not a dict object and cannot be parsed
        to a dict object.

        :param loc:
            The location of the error.

        :param value:
            The invalid value.
        """
        return Error(loc, ErrorCode.INVALID_DICT, "not a valid dict object", value)

    @staticmethod
    def invalid_list(loc: Loc, value: Any) -> Error:
        """Error reported when value is not a list object and cannot be parsed
        to a list object.

        :param loc:
            The location of the error.

        :param value:
            The invalid value.
        """
        return Error(loc, ErrorCode.INVALID_LIST, "not a valid list object", value)

    @staticmethod
    def invalid_set(loc: Loc, value: Any) -> Error:
        """Error reported when value is not a set object and cannot be parsed
        to a set object.

        :param loc:
            The location of the error.

        :param value:
            The invalid value.
        """
        return Error(loc, ErrorCode.INVALID_SET, "not a valid set object", value)

    @staticmethod
    def invalid_tuple(loc: Loc, value: Any) -> Error:
        """Error reported when value is not a tuple object and cannot be parsed
        to a tuple object.

        :param loc:
            The location of the error.

        :param value:
            The invalid value.
        """
        return Error(loc, ErrorCode.INVALID_TUPLE, "not a valid tuple object", value)

    @staticmethod
    def unsupported_tuple_format(loc: Loc, value: tuple, supported_format: tuple) -> Error:
        """Error reported when tuple object does not match types defined for a
        fixed-size typed tuple.

        For example, when tuple is defined like this::

            tuple[int, float, str]

        Then it must contain exactly 3 elements in this order: integer number,
        float number and string.

        :param loc:
            The location of the error.

        :param value:
            The invalid value.

        :param supported_format:
            The types declared for a typed fixed-size tuple that define allowed
            tuple format.
        """
        supported_format_str = ", ".join(repr(x) for x in supported_format)
        return Error(
            loc,
            ErrorCode.UNSUPPORTED_TUPLE_FORMAT,
            f"unsupported tuple format; supported format: {supported_format_str}",
            value,
            {"supported_format": supported_format},
        )

    @staticmethod
    def invalid_model(loc: Loc, value: Any, model_type: type):
        """Error reported when value is not a :class:`modelity.model.Model`
        subclass instance and cannot be parsed into it.

        :param loc:
            The location of the error.

        :param value:
            The invalid value.

        :param model_type:
            The expected model type.
        """
        return Error(
            loc,
            ErrorCode.INVALID_MODEL,
            f"not a valid {model_type.__qualname__} model instance",
            value,
            {"model_type": model_type},
        )

    @staticmethod
    def invalid_bool(loc: Loc, value: Any, true_literals: Optional[set] = None, false_literals: Optional[set] = None):
        """Create error signalling that the input value is not a valid boolean.

        :param loc:
            The location of the error.

        :param value:
            The failed value.

        :param true_literals:
            Set of literals evaluating to ``True``.

        :param false_literals:
            Set of literals evaluating to ``False``.
        """
        return Error(
            loc,
            ErrorCode.INVALID_BOOL,
            "not a valid boolean value",
            value,
            {"true_literals": true_literals, "false_literals": false_literals},
        )

    @staticmethod
    def invalid_datetime(loc: Loc, value: Any):
        """Create error signalling that the input value is not a datetime
        object and cannot be parsed to a datetime object.

        :param loc:
            The location of the error.

        :param value:
            The failed value.
        """
        return Error(loc, ErrorCode.INVALID_DATETIME, "not a valid datetime value", value)

    @staticmethod
    def invalid_date(loc: Loc, value: Any):
        """Create error signalling that the input value is not a date
        object and cannot be parsed to a date object.

        :param loc:
            The location of the error.

        :param value:
            The failed value.
        """
        return Error(loc, ErrorCode.INVALID_DATE, "not a valid date value", value)

    @staticmethod
    def unsupported_datetime_format(loc: Loc, value: str, supported_formats: Sequence[str]):
        """Create error signalling that the input string does not match any
        known datetime format.

        :param loc:
            The location of the error.

        :param value:
            The failed value.

        :param supported_formats:
            Tuple with supported datetime formats.
        """
        supported_formats_str = ", ".join(supported_formats)
        return Error(
            loc,
            ErrorCode.UNSUPPORTED_DATETIME_FORMAT,
            f"unsupported datetime format; supported formats: {supported_formats_str}",
            value=value,
            data={"supported_formats": tuple(supported_formats)},
        )

    @staticmethod
    def unsupported_date_format(loc: Loc, value: str, supported_formats: Sequence[str]):
        """Create error signalling that the input string does not match any
        known date format.

        :param loc:
            The location of the error.

        :param value:
            The failed value.

        :param supported_formats:
            Tuple with supported date formats.
        """
        supported_formats_str = ", ".join(supported_formats)
        return Error(
            loc,
            ErrorCode.UNSUPPORTED_DATE_FORMAT,
            f"unsupported date format; supported formats: {supported_formats_str}",
            value=value,
            data={"supported_formats": tuple(supported_formats)},
        )

    @staticmethod
    def value_out_of_range(loc: Loc, value: Any, allowed_values: tuple):
        """Create error signalling that the value does not exist in the set of
        allowed values.

        :param loc:
            The error location.

        :param value:
            The incorrect value.

        :param allowed_values:
            Tuple of allowed values.
        """
        allowed_values_str = ", ".join(repr(x) for x in allowed_values)
        return Error(
            loc,
            ErrorCode.VALUE_OUT_OF_RANGE,
            f"value out of range; allowed values: {allowed_values_str}",
            value=value,
            data={"allowed_values": allowed_values},
        )

    @staticmethod
    def invalid_number(loc: Loc, value: Any, msg: str, expected_type: type) -> Error:
        """Create error signalling that the value could not be parsed to a
        valid number of given type.

        This is a generic error common for all numeric types.

        :param loc:
            The location of the error.

        :param value:
            The incorrect value.

        :param msg:
            The error message.

        :param expected_type:
            The expected numeric type.
        """
        return Error(loc, ErrorCode.INVALID_NUMBER, msg, value, {"expected_type": expected_type})

    @classmethod
    def invalid_integer(cls, loc: Loc, value: Any) -> Error:
        """Create error signalling that the input value could not be parsed
        into valid integer number.

        :param loc:
            The error location.

        :param value:
            The incorrect value.
        """
        return cls.invalid_number(loc, value, "not a valid integer number", int)

    @classmethod
    def invalid_float(cls, loc: Loc, value: Any):
        """Create error signalling that the input value could not be parsed
        into valid floating point number.

        :param loc:
            The error location.

        :param value:
            The incorrect value.
        """
        return cls.invalid_number(loc, value, "not a valid floating point number", float)

    @staticmethod
    def unsupported_value_type(loc: Loc, value: Any, msg: str, supported_types: tuple[type, ...]):
        """Error reported when input value has unsupported type that cannot be
        processed further.

        It signals that the value cannot be parsed (for various reasons) and
        must explicitly be instance of one of supported types to allow it.

        :param loc:
            The location of the error.

        :param value:
            The incorrect value.

        :param msg:
            The error message.

        :param supported_types:
            Tuple with supported types.
        """
        return Error(
            loc,
            ErrorCode.UNSUPPORTED_VALUE_TYPE,
            msg,
            value=value,
            data={"supported_types": supported_types},
        )

    @classmethod
    def string_value_required(cls, loc: Loc, value: Any) -> Error:
        """Create error signalling that the value is not a string, but string
        is required.

        :param loc:
            The location of the error.

        :param value:
            The incorrect (i.e. non-string) value.
        """
        return cls.unsupported_value_type(loc, value, "string value required", (str,))

    @classmethod
    def bytes_value_required(cls, loc: Loc, value: Any) -> Error:
        """Create error signalling that the field requires :class:`bytes`
        object, but value of another type was given.

        :param loc:
            Field's location.

        :param value:
            Field's incorrect value.
        """
        return cls.unsupported_value_type(loc, value, "bytes value required", (bytes,))

    @staticmethod
    def ge_constraint_failed(loc: Loc, value: Number, min_inclusive: Number) -> Error:
        """Create error signalling that GE (greater or equal) value constraint
        failed.

        :param loc:
            The location of the error.

        :param value:
            The incorrect value.

        :param min_inclusive:
            The minimum inclusive value.
        """
        return Error(
            loc,
            ErrorCode.GE_CONSTRAINT_FAILED,
            f"the value must be >= {min_inclusive}",
            value,
            {"min_inclusive": min_inclusive},
        )

    @staticmethod
    def gt_constraint_failed(loc: Loc, value: Any, min_exclusive: Any) -> Error:
        """Create error signalling that GT (greater than) value constraint
        failed.

        :param loc:
            The location of the error.

        :param value:
            The incorrect value.

        :param min_exclusive:
            The minimum exclusive value.
        """
        return Error(
            loc,
            ErrorCode.GT_CONSTRAINT_FAILED,
            f"the value must be > {min_exclusive}",
            value,
            {"min_exclusive": min_exclusive},
        )

    @staticmethod
    def le_constraint_failed(loc: Loc, value: Any, max_inclusive: Any) -> Error:
        """Create error signalling that LE (less or equal) value constraint
        failed.

        :param loc:
            The location of the error.

        :param value:
            The incorrect value.

        :param max_inclusive:
            The maximum inclusive value.
        """
        return Error(
            loc,
            ErrorCode.LE_CONSTRAINT_FAILED,
            f"the value must be <= {max_inclusive}",
            value,
            {"max_inclusive": max_inclusive},
        )

    @staticmethod
    def lt_constraint_failed(loc: Loc, value: Any, max_exclusive: Any) -> Error:
        """Create error signalling that LT (less than) value constraint
        failed.

        :param loc:
            The location of the error.

        :param value:
            The incorrect value.

        :param max_exclusive:
            The maximum exclusive value.
        """
        return Error(
            loc,
            ErrorCode.LT_CONSTRAINT_FAILED,
            f"the value must be < {max_exclusive}",
            value,
            {"max_exclusive": max_exclusive},
        )

    @staticmethod
    def min_len_constraint_failed(loc: Loc, value: Any, min_len: int) -> Error:
        """Create error signalling that the value is too short.

        :param loc:
            The location of the error.

        :param value:
            The incorrect value.

        :param min_len:
            The maximum value length.
        """
        return Error(
            loc,
            ErrorCode.MIN_LEN_CONSTRAINT_FAILED,
            f"the value is too short; minimum length is {min_len}",
            value,
            {"min_len": min_len},
        )

    @staticmethod
    def max_len_constraint_failed(loc: Loc, value: Any, max_len: int) -> Error:
        """Create error signalling that the value is too long.

        :param loc:
            The location of the error.

        :param value:
            The incorrect value.

        :param max_len:
            The maximum value length.
        """
        return Error(
            loc,
            ErrorCode.MAX_LEN_CONSTRAINT_FAILED,
            f"the value is too long; maximum length is {max_len}",
            value,
            {"max_len": max_len},
        )

    @staticmethod
    def regex_constraint_failed(loc: Loc, value: str, pattern: str) -> Error:
        """Create error signalling that the regular expression constrain
        failed.

        :param loc:
            The location of the error.

        :param value:
            The incorrect value.

        :param pattern:
            The regular expression pattern.
        """
        return Error(
            loc,
            ErrorCode.REGEX_CONSTRAINT_FAILED,
            f"the value does not match regex pattern: {pattern}",
            value,
            {"pattern": pattern},
        )

    @staticmethod
    def required_missing(loc: Loc):
        """Create error signalling that the required field is missing a value.

        :param loc:
            The location of the error.
        """
        return Error(loc, ErrorCode.REQUIRED_MISSING, "this field is required")

    @staticmethod
    def exception(loc: Loc, msg: str, exc_type: type[Exception]) -> Error:
        """Create error from a caught exception object.

        :param loc:
            The location of the error.

        :param msg:
            The error message.

        :param exc_type:
            The type of the exception caught.
        """
        return Error(loc, ErrorCode.EXCEPTION, msg, data={"exc_type": exc_type})
