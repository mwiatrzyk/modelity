import dataclasses
from enum import Enum
from typing import Any, Optional, Sequence, Sized, TextIO

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

    #: Reported during validation for :obj:`typing.Optional` fields that remain
    #: unset during validation.
    #:
    #: To allow usage of ``Unset`` please use
    #: :obj:`modelity.types.StrictOptional` or :obj:`modelity.types.LooseOptional`
    #: type wrappers. Check their docs for more details.
    #:
    #: This error can be avoided by setting default values for optional fields.
    #:
    #: Use :meth:`ErrorFactory.unset_not_allowed` to create errors with this code.
    #:
    #: .. versionadded:: 0.29.0
    UNSET_NOT_ALLOWED = "modelity.UNSET_NOT_ALLOWED"

    #: Reported during parsing of :obj:`modelity.types.StrictOptional` wrapped
    #: fields if ``None`` is used as input value.
    #:
    #: Strict optional fields require the field to either be set to instance of
    #: type T, or not set at all (unlike :obj:`typing.Optional`, which allows ``None``).
    #: Modelity needs to provide such clean separation to make sure that model
    #: satisfies all type constraints after validation.
    #:
    #: .. important::
    #:      This error is reserved for :obj:`modelity.types.StrictOptional` wrapper
    #:      and should not be used elsewhere.
    #:
    #: Use :meth:`ErrorFactory.none_not_allowed` to create errors with this code.
    #:
    #: .. versionadded:: 0.29.0
    NONE_NOT_ALLOWED = "modelity.NONE_NOT_ALLOWED"

    #: Default error code for the :exc:`modelity.exc.UserError` exception.
    #:
    #: .. versionadded:: 0.30.0
    USER_ERROR = "modelity.USER_ERROR"


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
class ErrorWriter:
    """Class that formats errors as string and appends to the end of provided
    text buffer.

    :param out:
        The output text buffer.

    :param indent_string:
        Indentation string.

    :param indent_level:
        Indentation level.

    :param show_code:
        Display error code.

    :param show_value:
        Display input value.

    :param show_value_type:
        Display input value type.

    :param show_data:
        Display additional error data.

    .. versionadded:: 0.28.0
    """

    def __init__(
        self,
        out: TextIO,
        indent_string: str = "  ",
        indent_level: int = 0,
        show_code: bool = False,
        show_value: bool = False,
        show_value_type: bool = False,
        show_data: bool = False,
    ):
        self._out = out
        self._loc_indent = indent_string * indent_level
        self._msg_indent = indent_string * (indent_level + 1)
        self._show_code = show_code
        self._show_value = show_value
        self._show_value_type = show_value_type
        self._show_data = show_data

    def write(self, obj: Error):
        """Format given error object and write to the end of the text buffer
        provided in the constructor.

        :param obj:
            The error object.
        """
        attrs = {}
        attrs_str = ""
        if self._show_code:
            attrs["code"] = obj.code
        if self._show_value:
            attrs["value"] = _utils.describe(obj.value)
        if self._show_value_type:
            attrs["value_type"] = _utils.describe(type(obj.value))
        if self._show_data:
            for k, v in obj.data.items():
                attrs[k] = _utils.describe(v)
        if len(attrs) > 0:
            attrs_str = ", ".join(f"{k}={v}" for k, v in attrs.items())
            attrs_str = f" [{attrs_str}]"
        self._out.write(f"{self._loc_indent}{obj.loc}:\n")
        self._out.write(f"{self._msg_indent}{obj.msg}{attrs_str}\n")


@export
class ErrorFactory:
    """Class grouping factory methods for creating built-in errors."""

    @staticmethod
    def parse_error(loc: Loc, value: Any, expected_type: type, /, *, msg: Optional[str] = None, **extra_data) -> Error:
        """Create parse error.

        :param loc:
            Error location in the model.

        :param value:
            Input value that could not be parsed.

        :param expected_type:
            Expected value type.

        :param msg:
            The optional message to override built-in one.

        :param `**extra_data`:
            The optional extra error data.

            This will be placed inside :attr:`modelity.error.Error.data` dict
            of a created error object.
        """
        return Error(
            loc,
            ErrorCode.PARSE_ERROR,
            msg or f"Not a valid {_utils.describe(expected_type)} value",
            value,
            data={"expected_type": expected_type, **extra_data},
        )

    @staticmethod
    def conversion_error(
        loc: Loc,
        value: Any,
        expected_type: type,
        /,
        reason: Optional[str] = None,
        *,
        msg: Optional[str] = None,
        **extra_data,
    ) -> Error:
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

        :param expected_type:
            Expected value type.

        :param reason:
            The optional reason text.

        :param msg:
            The optional message to override built-in one.

            .. versionadded:: 0.33.0

        :param `**extra_data`:
            The optional extra error data.

            This will be placed inside :attr:`modelity.error.Error.data` dict
            of a created error object.

            .. versionadded:: 0.33.0
        """
        if msg is None:
            msg = f"Cannot convert {_utils.describe(type(value))} to {_utils.describe(expected_type)}"
            if reason is not None:
                msg += f"; {reason}"
        return Error(loc, ErrorCode.CONVERSION_ERROR, msg, value, data={"expected_type": expected_type, **extra_data})

    @staticmethod
    def invalid_value(
        loc: Loc, value: Any, expected_values: list, /, *, msg: Optional[str] = None, **extra_data
    ) -> Error:
        """Create invalid value error.

        :param loc:
            Error location in the model.

        :param value:
            Input value from outside of expected values set.

        :param expected_values:
            List with expected values.

        :param msg:
            The optional message to override built-in one.

            .. versionadded:: 0.32.0

        :param `**extra_data`:
            The optional extra error data.

            This will be placed inside :attr:`modelity.error.Error.data` dict
            of a created error object.

            .. versionadded:: 0.33.0
        """
        expected_values_str = ", ".join(_utils.describe(x) for x in expected_values)
        if msg is None:
            msg = "Not a valid value; expected"
            if len(expected_values) > 1:
                msg += f" one of: {expected_values_str}"
            else:
                msg += f": {expected_values_str}"
        return Error(
            loc,
            ErrorCode.INVALID_VALUE,
            msg,
            value,
            data={"expected_values": expected_values, **extra_data},
        )

    @staticmethod
    def invalid_type(
        loc: Loc,
        value: Any,
        expected_types: list[type],
        /,
        allowed_types: Optional[list[type]] = None,
        forbidden_types: Optional[list[type]] = None,
        *,
        msg: Optional[str] = None,
        **extra_data,
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

        :param msg:
            The optional message to override built-in one.

            .. versionadded:: 0.33.0

        :param `**extra_data`:
            The optional extra error data.

            This will be placed inside :attr:`modelity.error.Error.data` dict
            of a created error object.

            .. versionadded:: 0.33.0
        """
        if msg is None:
            expected_types_str = ", ".join(_utils.describe(x) for x in expected_types)
            msg = "Not a valid value"
            if len(expected_types) > 1:
                msg += f"; expected one of: {expected_types_str}"
            else:
                msg += f"; expected: {expected_types_str}"
        data = {"expected_types": expected_types, **extra_data}
        if allowed_types is not None:
            data["allowed_types"] = allowed_types
        if forbidden_types is not None:
            data["forbidden_types"] = forbidden_types
        return Error(loc, ErrorCode.INVALID_TYPE, msg, value=value, data=data)

    @staticmethod
    def invalid_datetime_format(loc: Loc, value: str, expected_formats: list[str], /) -> Error:
        """Create invalid datetime format error.

        :param loc:
            Error location in the model.

        :param value:
            Incorrect input string.

        :param expected_formats:
            List with expected datetime formats.
        """
        expected_formats_str = ", ".join(expected_formats)
        msg = "Not a valid datetime format; expected"
        if len(expected_formats) > 1:
            msg += f" one of: {expected_formats_str}"
        else:
            msg += f": {expected_formats_str}"
        return Error(
            loc,
            ErrorCode.INVALID_DATETIME_FORMAT,
            msg,
            value=value,
            data={"expected_formats": expected_formats},
        )

    @staticmethod
    def invalid_date_format(loc: Loc, value: str, expected_formats: list[str], /):
        """Create invalid date format error.

        :param loc:
            Error location in the model.

        :param value:
            Incorrect input string.

        :param expected_formats:
            List with expected date formats.
        """
        expected_formats_str = ", ".join(expected_formats)
        msg = "Not a valid date format; expected"
        if len(expected_formats) > 1:
            msg += f" one of: {expected_formats_str}"
        else:
            msg += f": {expected_formats_str}"
        return Error(
            loc,
            ErrorCode.INVALID_DATE_FORMAT,
            msg,
            value=value,
            data={"expected_formats": expected_formats},
        )

    @staticmethod
    def invalid_enum_value(loc: Loc, value: Any, expected_enum_type: type[Enum], /) -> Error:
        """Create invalid enum value error.

        :param loc:
            Error location in the model.

        :param value:
            Input value from outside of expected enumerated values set.

        :param expected_enum_type:
            Expected enum type.
        """
        expected_values_str = ", ".join(_utils.describe(x.value) for x in tuple(expected_enum_type))
        return Error(
            loc,
            ErrorCode.INVALID_ENUM_VALUE,
            f"Not a valid value; expected one of: {expected_values_str}",
            value=value,
            data={"expected_enum_type": expected_enum_type},
        )

    @staticmethod
    def decode_error(loc: Loc, value: bytes, expected_encodings: list[str], /) -> Error:
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
    def invalid_tuple_length(loc: Loc, value: tuple, expected_tuple: tuple[type, ...], /) -> Error:
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
        /,
        min_inclusive: Optional[int | float] = None,
        min_exclusive: Optional[int | float] = None,
        max_inclusive: Optional[int | float] = None,
        max_exclusive: Optional[int | float] = None,
        *,
        msg: Optional[str] = None,
    ) -> Error:
        """Create out of range error.

        This is a generic error factory for all kind of value range errors.

        .. important::
            The built-in message composer requires at least one range parameter
            to be provided.

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

        :param msg:
            The optional message to override built-in one.

            When custom message is provided then range parameters, although
            still recommended, become optional.

            .. versionadded:: 0.33.0
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
        if min_inclusive is not None and min_exclusive is not None:
            raise ValueError("cannot have both 'min_inclusive' and 'min_exclusive' arguments set")
        if max_inclusive is not None and max_exclusive is not None:
            raise ValueError("cannot have both 'max_inclusive' and 'max_exclusive' arguments set")
        if msg is None:
            if min_inclusive is not None and max_inclusive is not None:
                msg = f"Expected value in range [{min_inclusive}, {max_inclusive}]"
            elif min_inclusive is not None and max_exclusive is not None:
                msg = f"Expected value in range [{min_inclusive}, {max_exclusive})"
            elif min_exclusive is not None and max_inclusive is not None:
                msg = f"Expected value in range ({min_exclusive}, {max_inclusive}]"
            elif min_exclusive is not None and max_exclusive is not None:
                msg = f"Expected value in range ({min_exclusive}, {max_exclusive})"
            elif min_inclusive is not None:
                msg = f"Value must be >= {min_inclusive}"
            elif min_exclusive is not None:
                msg = f"Value must be > {min_exclusive}"
            elif max_inclusive is not None:
                msg = f"Value must be <= {max_inclusive}"
            elif max_exclusive is not None:
                msg = f"Value must be < {max_exclusive}"
            else:
                raise TypeError(
                    "need one or more range arguments: min_inclusive, min_exclusive, max_inclusive, max_exclusive"
                )
        return Error(loc, ErrorCode.OUT_OF_RANGE, msg, value, data=data)

    @staticmethod
    def invalid_length(
        loc: Loc,
        value: Sized,
        /,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        *,
        msg: Optional[str] = None,
    ) -> Error:
        """Create invalid length error.

        This error is reported for containers or other sized types when length
        constraints are not satisfied.

        .. important::
            The built-in message composer requires at least one length range
            parameter to be provided.

        :param loc:
            Error location in the model.

        :param value:
            Incorrect input value.

        :param min_length:
            Minimum length.

        :param max_length:
            Maximum length.

        :param msg:
            The optional message to override built-in one.

            When custom message is provided then length range parameters,
            although still recommended, become optional.

            .. versionadded:: 0.33.0
        """
        if msg is None:
            if min_length is not None and max_length is not None:
                msg = f"Expected length in range [{min_length}, {max_length}]"
            elif min_length is not None:
                msg = f"Expected length >= {min_length}"
            elif max_length is not None:
                msg = f"Expected length <= {max_length}"
            else:
                raise TypeError("need 'min_length', 'max_length' or both")
        data = {}
        if min_length is not None:
            data["min_length"] = min_length
        if max_length is not None:
            data["max_length"] = max_length
        return Error(loc, ErrorCode.INVALID_LENGTH, msg, value, data=data)

    @staticmethod
    def invalid_string_format(loc: Loc, value: str, expected_pattern: str, /, *, msg: Optional[str] = None) -> Error:
        """Create invalid string format error.

        .. versionchanged:: 0.33.0
            Now *loc*, *value* and *expected_pattern* are **positional-only**
            arguments, while *msg* is **keyword-only** argument. This was
            changed for compliance with other methods.

        :param loc:
            Error location in the model.

        :param value:
            Incorrect input string.

        :param expected_pattern:
            Expected string pattern (f.e. regex pattern).

        :param msg:
            Optional user-defined message to use instead of built-in one.
        """
        return Error(
            loc,
            ErrorCode.INVALID_STRING_FORMAT,
            "String does not match the expected format" if msg is None else msg,
            value,
            data={
                "expected_pattern": expected_pattern,
            },
        )

    @staticmethod
    def required_missing(loc: Loc, /):
        """Create required missing error.

        :param loc:
            The location of a missing field.
        """
        return Error(loc, ErrorCode.REQUIRED_MISSING, "This field is required")

    @staticmethod
    def exception(loc: Loc, value: Any, exc: Exception, /) -> Error:
        """Create error from a user exception.

        :param loc:
            Error location in the model.

        :param value:
            The incorrect value.

        :param exc:
            The exception object.
        """
        return Error(loc, ErrorCode.EXCEPTION, str(exc), value, {"exc_type": exc.__class__})

    @staticmethod
    def unset_not_allowed(loc: Loc, expected_type: Any, /) -> Error:
        """Create ``UNSET_NOT_ALLOWED`` error.

        See :attr:`ErrorCode.UNSET_NOT_ALLOWED` for more details.

        .. versionadded:: 0.29.0

        :param loc:
            Error location in the model.

        :param expected_types:
            The expected type.
        """
        return Error(
            loc,
            ErrorCode.UNSET_NOT_ALLOWED,
            f"This field does not allow Unset; expected: {_utils.describe(expected_type)}",
            data={"expected_type": expected_type},
        )

    @staticmethod
    def none_not_allowed(loc: Loc, expected_type: Any, /) -> Error:
        """Create ``NONE_NOT_ALLOWED`` error.

        See :attr:`ErrorCode.NONE_NOT_ALLOWED` for more details.

        .. versionadded:: 0.29.0

        :param loc:
            Error location in the model.

        :param expected_types:
            The expected type.
        """
        return Error(
            loc,
            ErrorCode.NONE_NOT_ALLOWED,
            f"This field does not allow None; expected: {_utils.describe(expected_type)}",
            None,
            data={"expected_type": expected_type},
        )
