import dataclasses
from enum import Enum
from typing import Any, Optional, Sequence, Sized

from modelity import _utils
from modelity.loc import Loc
from modelity.unset import Unset

__all__ = export = _utils.ExportList()  # type: ignore


@export
class ErrorCode:
    """Class defining all built-in error codes."""

    #: Used when Modelity could not parse input value to an expected type.
    #:
    #: For example, string "abc" cannot be parsed as integer number.
    #:
    #: Use :meth:`ErrorFactory.parse_error` to create errors with this code.
    PARSE_ERROR = "modelity.PARSE_ERROR"

    #: Used when input value was not one of the expected values.
    #:
    #: For example, field accepts literals ``Literal[1, 2, "3"]``, but the input
    #: was ``"2"`` which is not one of the allowed literals.
    #:
    #: Use :meth:`ErrorFactory.invalid_value` to create errors with this code.
    INVALID_VALUE = "modelity.INVALID_VALUE"

    #: Similar to :attr:`INVALID_VALUE`, but used with enumerated values and
    #: :class:`enum.Enum` type.
    #:
    #: Use :meth:`ErrorFactory.invalid_enum_value` to create errors with this code.
    INVALID_ENUM_VALUE = "modelity.INVALID_ENUM_VALUE"

    #: Used when type of the input value does not match the expected type and
    #: it cannot be automatically converted.
    #:
    #: Use :meth:`ErrorFactory.invalid_type` to create errors with this code.
    INVALID_TYPE = "modelity.INVALID_TYPE"

    #: Used when datetime field gets text input that has invalid datetime
    #: format.
    #:
    #: Used :meth:`ErrorFactory.invalida_datetime_format` to create errors with this code.
    INVALID_DATETIME_FORMAT = "modelity.INVALID_DATETIME_FORMAT"

    #: Same as for :attr:`INVALID_DATETIME_FORMAT`, but for dates.
    #:
    #: Use :meth:`ErrorFactory.invalid_date_format` to create errors with this code.
    INVALID_DATE_FORMAT = "modelity.INVALID_DATE_FORMAT"

    #: Used when bytes could not be decoded into string using any of the
    #: provided encoding.
    #:
    #: Use :meth:`ErrorFactory.decode_error` to create errors with this code.
    DECODE_ERROR = "modelity.DECODE_ERROR"

    #: Used when it was not possible to automatically convert allowed input
    #: value type into expected type.
    #:
    #: For example, a :class:`set` cannot be created from :class:`list` if the
    #: list contains unhashable elements.
    #:
    #: Use by :meth:`ErrorFactory.conversion_error` to create errors with this code.
    CONVERSION_ERROR = "modelity.CONVERSION_ERROR"

    #: Used for fixed-length tuple types where input value is a tuple that does
    #: not have the exact number of elements.
    #:
    #: Use :meth:`ErrorFactory.invalid_tuple` to create errors with this code.
    INVALID_TUPLE_LENGTH = "modelity.INVALID_TUPLE_LENGTH"

    #: Used to signal value range errors.
    #:
    #: Use :meth:`out_of_range` to create error with this code.
    OUT_OF_RANGE = "modelity.OUT_OF_RANGE"

    #: Used to signal value length range errors.
    #:
    #: Use :meth:`invalid_length` to create errors with this code.
    INVALID_LENGTH = "modelity.INVALID_LENGTH"

    #: Used to inform that the input value string has incorrect format.
    #:
    #: For example, input expects data matching some regular expression
    #: pattern, but the input value does not match the pattern.
    #:
    #: Use :meth:`invalid_string_format` to create errors with this code.
    INVALID_STRING_FORMAT = "modelity.INVALID_STRING_FORMAT"

    #: Signals that the field is required but is not present in the model.
    #:
    #: Use :meth:`ErrorFactory.required_missing` to create errors with this code.
    REQUIRED_MISSING = "modelity.REQUIRED_MISSING"

    #: Used to wrap user exception caught during parsing or validation stage.
    #:
    #: This error code is used to wrap :exc:`TypeError` (and its subclasses)
    #: raised during parsing stage or :exc:`ValueError` (and its subclasses)
    #: raised during validation stage by user-defined hook.
    #:
    #: Use :meth:`ErrorFactory.exception` to create errors with this code.
    EXCEPTION = "modelity.EXCEPTION"


@export
@dataclasses.dataclass
class Error:
    """Object containing details of the single error.

    It is used for both parsing and validation stages of the model
    processing.
    """

    #: Error location in the model.
    loc: Loc

    #: Error code.
    #:
    #: This is a short description of the error. Check :class:`ErrorCode` for
    #: the list of Modelity built-in error code constants and their meaning.
    code: str

    #: Formatted error message.
    #:
    #: Contains human-readable error description based on :attr:`code` and
    #: :attr:`data`.
    msg: str

    #: The incorrect value, if present, or :obj:`modelity.unset.Unset` otherwise.
    value: Any = Unset

    #: Additional error data.
    #:
    #: This property, along with :attr:`code`, can be used to render custom
    #: error messages. It is recommended to always use same structure for same
    #: error code.
    #:
    #: For built-in errors, this property will get filled with any extra
    #: arguments passed to factory functions defined in :class:`ErrorFactory`
    #: class.
    data: dict = dataclasses.field(default_factory=dict)

    @property
    def value_type(self) -> type:
        """The type of the incorrect value."""
        return type(self.value)


@export
class ErrorFactory:
    """Class grouping factory methods for creating built-in errors."""

    @staticmethod
    def parse_error(loc: Loc, value: Any, expected_type: type, msg: Optional[str] = None, **extra_data) -> Error:
        """Create parse error.

        :param loc:
            Error location in the model.

        :param value:
            Input value that could not be parsed.

        :param expected_type:
            Expected value type.

        :param msg:
            Optional message to override default one.

        :param `**extra_data`:
            Additional keyword arguments to be passed into error data.
        """
        return Error(
            loc,
            ErrorCode.PARSE_ERROR,
            msg or f"Not a valid {expected_type.__name__} value",
            value,
            data={"expected_type": expected_type, **extra_data},
        )

    @staticmethod
    def conversion_error(loc: Loc, value: Any, reason: str, expected_type: type) -> Error:
        """Create conversion error.

        This signals that value could not be converted into instance of
        *expected_type* due to the reason explained in error message.

        .. important::

            This error is reserved only for failing conversion where input
            value is non-string. If input value is string or bytes then it is
            better to use :meth:`parse_error` factory instead.

        :param loc:
            Error location in the model.

        :param value:
            Input value that could not be converted.

        :param reason:
            The reason text.

        :param expected_type:
            Expected value type.
        """
        msg = f"Cannot convert {type(value).__name__} to {expected_type.__name__}; {reason}"
        return Error(loc, ErrorCode.CONVERSION_ERROR, msg, value, data={"expected_type": expected_type})

    @staticmethod
    def invalid_value(loc: Loc, value: Any, expected_values: list) -> Error:
        """Create invalid value error.

        :param loc:
            Error location in the model.

        :param value:
            Input value from outside of expected values set.

        :param expected_values:
            List with expected values.
        """
        expected_values_str = ", ".join(repr(x) for x in expected_values)
        return Error(
            loc,
            ErrorCode.INVALID_VALUE,
            f"Not a valid value; expected one of: {expected_values_str}",
            value,
            data={"expected_values": expected_values},
        )

    @staticmethod
    def invalid_type(
        loc: Loc,
        value: Any,
        expected_types: list[type],
        allowed_types: Optional[list[type]] = None,
        forbidden_types: Optional[list[type]] = None,
    ) -> Error:
        """Create invalid type error.

        :param loc:
            Error location in the model.

        :param value:
            Incorrect input value.

        :param expected_types:
            List with expected type or types.

        :param allowed_types:
            Optional list with allowed types.

            This is information that if one of these types is used as type of
            the input value then it will be accepted and converted to one of
            expected types.

            For example, a set can be constructed from set, list or tuple of
            items.

        :param forbidden_types:
            Optional list of forbidden types.

            This is used to specify types that are arbitrary forbidden and will
            fail value processing immediately when encountered.
        """
        expected_types_str = ", ".join(x.__name__ for x in expected_types)
        msg = "Not a valid value"
        if len(expected_types) > 1:
            msg += f"; expected one of: {expected_types_str}"
        else:
            msg += f"; expected: {expected_types_str}"
        data = {"expected_types": expected_types}
        if allowed_types is not None:
            data["allowed_types"] = allowed_types
        if forbidden_types is not None:
            data["forbidden_types"] = forbidden_types
        return Error(loc, ErrorCode.INVALID_TYPE, msg, value=value, data=data)

    @staticmethod
    def invalid_datetime_format(loc: Loc, value: str, expected_formats: list[str]) -> Error:
        """Create invalid datetime format error.

        :param loc:
            Error location in the model.

        :param value:
            Incorrect input string.

        :param expected_formats:
            List with expected datetime formats.
        """
        expected_formats_str = ", ".join(expected_formats)
        return Error(
            loc,
            ErrorCode.INVALID_DATETIME_FORMAT,
            f"Not a valid datetime format; expected one of: {expected_formats_str}",
            value=value,
            data={"expected_formats": expected_formats},
        )

    @staticmethod
    def invalid_date_format(loc: Loc, value: str, expected_formats: Sequence[str]):
        """Create invalid date format error.

        :param loc:
            Error location in the model.

        :param value:
            Incorrect input string.

        :param expected_formats:
            List with expected date formats.
        """
        expected_formats_str = ", ".join(expected_formats)
        return Error(
            loc,
            ErrorCode.INVALID_DATE_FORMAT,
            f"Not a valid date format; expected one of: {expected_formats_str}",
            value=value,
            data={"expected_formats": expected_formats},
        )

    @staticmethod
    def invalid_enum_value(loc: Loc, value: Any, expected_enum_type: type[Enum]) -> Error:
        """Create invalid enum value error.

        :param loc:
            Error location in the model.

        :param value:
            Input value from outside of expected enumerated values set.

        :param expected_enum_type:
            Expected enum type.
        """
        expected_values_str = ", ".join(repr(x.value) for x in tuple(expected_enum_type))
        return Error(
            loc,
            ErrorCode.INVALID_ENUM_VALUE,
            f"Not a valid value; expected one of: {expected_values_str}",
            value=value,
            data={"expected_enum_type": expected_enum_type},
        )

    @staticmethod
    def decode_error(loc: Loc, value: bytes, expected_encodings: list[str]) -> Error:
        """Create decode error.

        :param loc:
            Error location in the model.

        :param value:
            Input bytes that could not be decoded into string.

        :param expected_encodings:
            List of expected encodings.
        """
        return Error(
            loc, ErrorCode.DECODE_ERROR, "Invalid text encoding", value, data={"expected_encodings": expected_encodings}
        )

    @staticmethod
    def invalid_tuple_length(loc: Loc, value: tuple, expected_tuple: tuple[type, ...]) -> Error:
        """Create invalid tuple length error.

        :param loc:
            Error location in the model.

        :param value:
            Incorrect input tuple.

        :param expected_tuple:
            Expected tuple shape.
        """
        msg = f"Not a valid tuple; expected {len(expected_tuple)} elements, got {len(value)}"
        return Error(loc, ErrorCode.INVALID_TUPLE_LENGTH, msg, value, data={"expected_tuple": expected_tuple})

    @staticmethod
    def out_of_range(
        loc: Loc,
        value: int | float,
        min_inclusive: Optional[int | float] = None,
        min_exclusive: Optional[int | float] = None,
        max_inclusive: Optional[int | float] = None,
        max_exclusive: Optional[int | float] = None,
    ) -> Error:
        """Create out of range error.

        This is a generic error factory for all kind of value range errors.

        :param loc:
            Error location in the model.

        :param value:
            Incorrect input number.

        :param min_inclusive:
            Minimum value (inclusive).

        :param min_exclusive:
            Minimum value (exclusive).

        :param max_inclusive:
            Maximum value (inclusive).

        :param max_exclusive:
            Maximum value (exclusive).
        """
        data = {}
        if min_inclusive is not None:
            data["min_inclusive"] = min_inclusive
        if min_exclusive is not None:
            data["min_exclusive"] = min_exclusive
        if max_inclusive is not None:
            data["max_inclusive"] = max_inclusive
        if max_exclusive is not None:
            data["max_exclusive"] = max_exclusive
        if "min_inclusive" in data and "min_exclusive" in data:
            raise ValueError("cannot have both 'min_inclusive' and 'min_exclusive' arguments set")
        if "max_inclusive" in data and "max_exclusive" in data:
            raise ValueError("cannot have both 'max_inclusive' and 'max_exclusive' arguments set")
        # TODO: on or after, on or before for dates
        if "min_inclusive" in data:
            msg = f"Value must be greater than or equal to {min_inclusive}"
        elif "min_exclusive" in data:
            msg = f"Value must be greater than {min_exclusive}"
        elif "max_inclusive" in data:
            msg = f"Value must be less than or equal to {max_inclusive}"
        else:
            msg = f"Value must be less than {max_exclusive}"
        return Error(loc, ErrorCode.OUT_OF_RANGE, msg, value, data=data)

    @staticmethod
    def invalid_length(
        loc: Loc, value: Sized, min_length: Optional[int] = None, max_length: Optional[int] = None
    ) -> Error:
        """Create invalid length error.

        This error is reported for containers or other sized types when length
        constraints are not satisfied.

        :param loc:
            Error location in the model.

        :param value:
            Incorrect input value.

        :param min_length:
            Minimum length.

        :param max_length:
            Maximum length.
        """
        data = {}
        if min_length is not None:
            data["min_length"] = min_length
        if max_length is not None:
            data["max_length"] = max_length
        #: TODO: Length must be between {min_length} and {max_length}
        if "min_length" in data:
            msg = f"Length must be at least {min_length}"
        else:
            msg = f"Length must be at most {max_length}"
        return Error(loc, ErrorCode.INVALID_LENGTH, msg, value, data=data)

    @staticmethod
    def invalid_string_format(loc: Loc, value: str, expected_pattern: str) -> Error:
        """Create invalid string format error.

        :param loc:
            Error location in the model.

        :param value:
            Incorrect input string.

        :param expected_pattern:
            Expected string pattern (f.e. regex pattern).
        """
        return Error(
            loc,
            ErrorCode.INVALID_STRING_FORMAT,
            "String does not match the expected format",
            value,
            data={
                "expected_pattern": expected_pattern,
            },
        )

    @staticmethod
    def required_missing(loc: Loc):
        """Create required missing error.

        :param loc:
            The location of a missing field.
        """
        return Error(loc, ErrorCode.REQUIRED_MISSING, "This field is required")

    @staticmethod
    def exception(loc: Loc, value: Any, exc: Exception) -> Error:
        """Create error from a user exception.

        :param loc:
            Error location in the model.

        :param value:
            The incorrect value.

        :param exc:
            The exception object.
        """
        return Error(loc, ErrorCode.EXCEPTION, str(exc), value, {"exc_type": exc.__class__})
