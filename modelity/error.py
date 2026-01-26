import dataclasses
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional, Sequence

from modelity import _utils
from modelity.loc import Loc
from modelity.unset import Unset

__all__ = export = _utils.ExportList()  # type: ignore


@export
class ErrorCode:
    """Class containing constants with all built-in error codes.

    These codes are used by factory methods defined in :class:`ErrorFactory`
    class.
    """

    #: Error code reported by :meth:`ErrorFactory.parse_error` method.
    PARSE_ERROR = "modelity.PARSE_ERROR"

    #: Error code reported by :meth:`ErrorFactory.invalid_value` method.
    INVALID_VALUE = "modelity.INVALID_VALUE"

    #: Error code reported by :meth:`ErrorFactory.invalid_enum_value` method.
    INVALID_ENUM_VALUE = "modelity.INVALID_ENUM_VALUE"

    #: Error code reported by :meth:`ErrorFactory.invalid_type` method.
    INVALID_TYPE = "modelity.INVALID_TYPE"

    #: Error code reported by :meth:`ErrorFactory.invalida_datetime_format` method.
    INVALID_DATETIME_FORMAT = "modelity.INVALID_DATETIME_FORMAT"

    #: Error code reported by :meth:`ErrorFactory.invalid_date_format` method.
    INVALID_DATE_FORMAT = "modelity.INVALID_DATE_FORMAT"

    #: Error code reported by :meth:`ErrorFactory.decode_error` method.
    DECODE_ERROR = "modelity.DECODE_ERROR"

    #: Error code reported by :meth:`ErrorFactory.conversion_error` method.
    CONVERSION_ERROR = "modelity.CONVERSION_ERROR"

    #: Error code reported by :meth:`ErrorFactory.invalid_tuple` method.
    INVALID_TUPLE_LENGTH = "modelity.INVALID_TUPLE_LENGTH"

    # Old below:

    #: Error code reported by :meth:`ErrorFactory.parsing_error` method.
    PARSING_ERROR = "modelity.PARSING_ERROR"  # TODO: remove; use PARSE_ERROR

    #: Error code reported by :meth:`ErrorFactory.union_parsing_error` method.
    UNION_PARSING_ERROR = "modelity.UNION_PARSING_ERROR"

    #: Error code reported by :meth:`ErrorFactory.invalid_tuple_format` method.
    INVALID_TUPLE_FORMAT = "modelity.INVALID_TUPLE_FORMAT"

    #: Error code reported by :meth:`ErrorFactory.value_not_allowed` method.
    VALUE_NOT_ALLOWED = "modelity.VALUE_NOT_ALLOWED"

    #: Error code reported by :meth:`ErrorFactory.constraint_failed` method.
    CONSTRAINT_FAILED = "modelity.CONSTRAINT_FAILED"

    #: Error reported by :meth:`ErrorFactory.required_missing` method.
    REQUIRED_MISSING = "modelity.REQUIRED_MISSING"

    #: Error reported by :meth:`ErrorFactory.exception` method.
    EXCEPTION = "modelity.EXCEPTION"

    #: Error reported by :meth:`ErrorFactory.unsupported_value_type` method.
    UNSUPPORTED_VALUE_TYPE = "modelity.UNSUPPORTED_VALUE_TYPE"


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

    # TODO: parse_error -> only from string/bytes
    @staticmethod
    def parse_error(loc: Loc, value: Any, expected_type: type, msg: Optional[str] = None, **extra_data) -> Error:
        """Generic error reported when it was not possible to parse *value*
        as instance of *target_type*.

        :param loc:
            Value location in the model.

        :param value:
            Value given.

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
            Expected type after successful conversion.
        """
        msg = f"Cannot convert {type(value).__name__} to {expected_type.__name__}; {reason}"
        return Error(loc, ErrorCode.CONVERSION_ERROR, msg, value, data={"expected_type": expected_type})

    @staticmethod
    def invalid_value(loc: Loc, value: Any, expected_values: list, **extra_data) -> Error:
        """Error reported when value given is out of predefined set of allowed
        values.

        :param loc:
            Value location in the model.

        :param value:
            Value given.

        :param expected_values:
            List with expected values.

        :param `**extra_data`:
            Optional extra error data.
        """
        expected_values_str = ", ".join(repr(x) for x in expected_values)
        return Error(
            loc,
            ErrorCode.INVALID_VALUE,
            f"Not a valid value; expected one of: {expected_values_str}",
            value,
            data={"expected_values": expected_values, **extra_data},
        )

    @staticmethod
    def invalid_type(
        loc: Loc,
        value: Any,
        expected_types: list[type],
        allowed_types: Optional[list[type]] = None,
        forbidden_types: Optional[list[type]] = None,
        **extra_data,
    ) -> Error:
        """Error reported when input value has incorrect type.

        :param loc:
            Error location in the model.

        :param value:
            Incorrect input value.

        :param expected_types:
            List with expected types.

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

        :param `**extra_data`:
            Optional extra error data.
        """
        expected_types_str = ", ".join(x.__name__ for x in expected_types)
        msg = "Not a valid value"
        if len(expected_types) > 1:
            msg += f"; expected one of: {expected_types_str}"
        else:
            msg += f"; expected {_utils.articlify(expected_types_str)}"
        data = {"expected_types": expected_types}
        if allowed_types is not None:
            data["allowed_types"] = allowed_types
        if forbidden_types is not None:
            data["forbidden_types"] = forbidden_types
        data.update(extra_data)
        return Error(loc, ErrorCode.INVALID_TYPE, msg, value=value, data=data)

    @staticmethod
    def invalid_datetime_format(loc: Loc, value: str, expected_formats: list[str]) -> Error:
        """Error reported when given datetime string did not match any of the
        expected formats.

        :param loc:
            Value location in the model.

        :param value:
            Value given.

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
        """Error reported when given date string did not match any of the
        expected date formats.

        :param loc:
            Value location in the model.

        :param value:
            Value given.

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
        """Error reported when value could not be matched to any of the values
        provided by given enum type.

        :param loc:
            Value location in the model.

        :param value:
            Value given.

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
        """Error reported when given bytes value could not be decoded into
        string using any of the provided encodings.

        :param loc:
            Error location in the model.

        :param value:
            Input value.

        :param expected_encodings:
            List of expected encodings.
        """
        return Error(
            loc, ErrorCode.DECODE_ERROR, "Invalid text encoding", value, data={"expected_encodings": expected_encodings}
        )

    @staticmethod
    def invalid_tuple_length(loc: Loc, value: tuple, expected_tuple: tuple[type, ...]) -> Error:
        """Error reported if input value is a tuple that has incorrect number
        of items.

        :param loc:
            Error location in the model.

        :param value:
            Incorrect input enum.

        :param expected_tuple:
            Expected tuple shape.
        """
        msg = f"Not a valid tuple; expected {len(expected_tuple)} elements, got {len(value)}"
        return Error(
            loc,
            ErrorCode.INVALID_TUPLE_LENGTH,
            msg,
            value,
            data={
                "expected_tuple": expected_tuple
            }
        )

    # TODO: Remove
    @staticmethod
    def parsing_error(loc: Loc, value: Any, msg: str, target_type: type, **extra_data) -> Error:
        """Error reported when *value* could not be parsed as a *target_type*
        type.

        :param loc:
            The location of the error.

        :param value:
            The invalid value.

        :param msg:
            The error message.

        :param target_type:
            The target type.

        :param `**extra_data`:
            The extra parameters to be placed inside :attr:`Error.data`
            property of created error.
        """
        return Error(loc, ErrorCode.PARSING_ERROR, msg, value, {"target_type": target_type, **extra_data})

    @classmethod
    def union_parsing_error(cls, loc: Loc, value: Any, union_types: tuple[type, ...]) -> Error:
        """Error reported when *value* could not be parsed as one of types
        given in the union.

        For creating unions, :obj:`typing.Union` is used.

        :param loc:
            The location of the error.

        :param value:
            The invalid value.

        :param union_types:
            The types extracted from the union.
        """
        union_types_str = ", ".join(repr(x) for x in union_types)
        return Error(
            loc,
            ErrorCode.UNION_PARSING_ERROR,
            f"could not parse union value; types tried: {union_types_str}",
            value,
            {"union_types": union_types},
        )

    @classmethod
    def dict_parsing_error(cls, loc: Loc, value: Any) -> Error:
        """Error reported when *value* could not be parsed as :class:`dict`
        object.

        :param loc:
            The location of the error.

        :param value:
            The invalid value.
        """
        return cls.parsing_error(loc, value, "could not parse value as dict", dict)

    @classmethod
    def list_parsing_error(cls, loc: Loc, value: Any) -> Error:
        """Error reported when *value* could not be parsed as :class:`list`
        object.

        :param loc:
            The location of the error.

        :param value:
            The invalid value.
        """
        return cls.parsing_error(loc, value, "could not parse value as list", list)

    @classmethod
    def set_parsing_error(cls, loc: Loc, value: Any) -> Error:
        """Error reported when *value* could not be parsed as :class:`set`
        object.

        :param loc:
            The location of the error.

        :param value:
            The invalid value.
        """
        return cls.parsing_error(loc, value, "could not parse value as set", set)

    @classmethod
    def tuple_parsing_error(cls, loc: Loc, value: Any) -> Error:
        """Error reported when *value* could not be parsed as :class:`tuple`
        object.

        :param loc:
            The location of the error.

        :param value:
            The invalid value.
        """
        return cls.parsing_error(loc, value, "could not parse value as tuple", tuple)

    @staticmethod
    def invalid_tuple_format(loc: Loc, value: tuple, expected_format: tuple) -> Error:
        """Error reported for fixed-size typed tuple fields when *value* is a
        tuple that is either too short, or too long.

        For example, let's create example model with field *foo* that must be a
        tuple containing exactly 3 elements:

        * an integer number,
        * a float number
        * and a string.

        Here's the model:

        .. testcode::

            from modelity.model import Model

            class FixedTupleExample(Model):
                foo: tuple[int, float, str]

        And here's code snippet that will trigger this error:

        .. doctest::

            >>> model = FixedTupleExample()
            >>> model.foo = (1, 3.14, "spam")  # correct
            >>> model.foo = (1, 3.14)  # incorrect; too short
            Traceback (most recent call last):
              ...
            modelity.exc.ParsingError: parsing failed for type 'FixedTupleExample' with 1 error(-s):
              foo:
                invalid tuple format; expected format: <class 'int'>, <class 'float'>, <class 'str'> [code=modelity.INVALID_TUPLE_FORMAT, value_type=<class 'tuple'>]

        :param loc:
            The location of the error.

        :param value:
            The invalid value.

        :param expected_format:
            The tuple of types composing expected format for the input value.
        """
        supported_format_str = ", ".join(repr(x) for x in expected_format)
        return Error(
            loc,
            ErrorCode.INVALID_TUPLE_FORMAT,
            f"invalid tuple format; expected format: {supported_format_str}",
            value,
            {"expected_format": expected_format},
        )

    @classmethod
    def model_parsing_error(cls, loc: Loc, value: Any, target_model_type: type):
        """Error reported when *value* could not be parsed as
        :class:`modelity.model.Model` subclass given via *target_model_type*.

        :param loc:
            The location of the error.

        :param value:
            The invalid value.

        :param target_model_type:
            The target model type.
        """
        return cls.parsing_error(
            loc, value, f"could not parse value as {target_model_type.__qualname__} model", target_model_type
        )

    @classmethod
    def bool_parsing_error(
        cls, loc: Loc, value: Any, true_literals: Optional[set] = None, false_literals: Optional[set] = None
    ):
        """Error reported when *value* could not be parsed as :class:`bool` type.

        :param loc:
            The location of the error.

        :param value:
            The invalid value.

        :param true_literals:
            Set containing user-defined literals evaluating to ``True``.

        :param false_literals:
            Set containing user-defined literals evaluating to ``False``.
        """
        return cls.parsing_error(
            loc,
            value,
            "could not parse value as bool",
            bool,
            true_literals=true_literals or set(),
            false_literals=false_literals or set(),
        )

    @classmethod
    def datetime_parsing_error(cls, loc: Loc, value: Any):
        """Error reported when *value* could not be parsed as
        :class:`datetime.datetime` type.

        :param loc:
            The location of the error.

        :param value:
            The invalid value.
        """
        return cls.parsing_error(loc, value, "could not parse value as datetime", datetime)

    @classmethod
    def date_parsing_error(cls, loc: Loc, value: Any):
        """Error reported when *value* could not be parsed as
        :class:`datetime.date` type.

        :param loc:
            The location of the error.

        :param value:
            The invalid value.
        """
        return cls.parsing_error(loc, value, "could not parse value as date", date)

    @staticmethod
    def value_not_allowed(loc: Loc, value: Any, allowed_values: tuple):
        """Error signalling that given *value* was not found in the set of
        allowed values given via *allowed_values* argument.

        This is reported for types that allow values of any type, but only from
        a predefined set of values. Such types are, for example,
        :class:`enum.Enum` subclasses, or fields annotated with
        :obj:`typing.Literal` annotation.

        :param loc:
            The error location.

        :param value:
            The invalid value.

        :param allowed_values:
            The tuple of allowed values.
        """
        allowed_values_str = ", ".join(repr(x) for x in allowed_values)
        return Error(
            loc,
            ErrorCode.VALUE_NOT_ALLOWED,
            f"value not allowed; allowed values: {allowed_values_str}",
            value=value,
            data={"allowed_values": allowed_values},
        )

    @classmethod
    def integer_parsing_error(cls, loc: Loc, value: Any) -> Error:
        """Create error signalling that the input *value* could not be parsed
        as valid integer number.

        :param loc:
            The error location.

        :param value:
            The incorrect value.
        """
        return cls.parsing_error(loc, value, "could not parse value as integer number", int)

    @classmethod
    def float_parsing_error(cls, loc: Loc, value: Any):
        """Create error signalling that the input *value* could not be parsed
        as valid floating point number.

        :param loc:
            The error location.

        :param value:
            The incorrect value.
        """
        return cls.parsing_error(loc, value, "could not parse value as floating point number", float)

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
            The incorrect value.
        """
        return cls.unsupported_value_type(loc, value, "string value required", (str,))

    @classmethod
    def bytes_value_required(cls, loc: Loc, value: Any) -> Error:
        """Create error signalling that the field requires :class:`bytes`
        object, but value of another type was given.

        :param loc:
            The location of the error.

        :param value:
            The incorrect value.
        """
        return cls.unsupported_value_type(loc, value, "bytes value required", (bytes,))

    @staticmethod
    def constraint_failed(loc: Loc, value: Any, msg: str, **data) -> Error:
        """Error signalling that *value* did not pass constraint checking.

        :param loc:
            The location of the error.

        :param value:
            The incorrect value.

        :param msg:
            The error message.

        :param `**data`:
            The error data.

            This should be used to pass parameters from a constraint object,
            like minimum or maximum length etc.
        """
        return Error(loc, ErrorCode.CONSTRAINT_FAILED, msg, value, data)

    @classmethod
    def ge_constraint_failed(cls, loc: Loc, value: Any, min_inclusive: Any) -> Error:
        """Create error signalling that the *value* did not pass
        *greater-or-equal* constraint check.

        :param loc:
            The location of the error.

        :param value:
            The incorrect value.

        :param min_inclusive:
            The minimum inclusive value allowed.
        """
        return cls.constraint_failed(loc, value, f"the value must be >= {min_inclusive}", min_inclusive=min_inclusive)

    @classmethod
    def gt_constraint_failed(cls, loc: Loc, value: Any, min_exclusive: Any) -> Error:
        """Create error signalling that the *value* did not pass *greater-than*
        constraint check.

        :param loc:
            The location of the error.

        :param value:
            The incorrect value.

        :param min_exclusive:
            The minimum exclusive value.
        """
        return cls.constraint_failed(loc, value, f"the value must be > {min_exclusive}", min_exclusive=min_exclusive)

    @classmethod
    def le_constraint_failed(cls, loc: Loc, value: Any, max_inclusive: Any) -> Error:
        """Create error signalling that the *value* did not pass *less-or-equal*
        constraint check.

        :param loc:
            The location of the error.

        :param value:
            The incorrect value.

        :param max_inclusive:
            The maximum inclusive value.
        """
        return cls.constraint_failed(loc, value, f"the value must be <= {max_inclusive}", max_inclusive=max_inclusive)

    @classmethod
    def lt_constraint_failed(cls, loc: Loc, value: Any, max_exclusive: Any) -> Error:
        """Create error signalling that the *value* did not pass *less-than*
        constraint check.

        :param loc:
            The location of the error.

        :param value:
            The incorrect value.

        :param max_exclusive:
            The maximum exclusive value.
        """
        return cls.constraint_failed(loc, value, f"the value must be < {max_exclusive}", max_inclusive=max_exclusive)

    @classmethod
    def min_len_constraint_failed(cls, loc: Loc, value: Any, min_len: int) -> Error:
        """Create error signalling that the *value* is too short.

        :param loc:
            The location of the error.

        :param value:
            The incorrect value.

        :param min_len:
            The minimum value length.
        """
        return cls.constraint_failed(
            loc, value, f"the value is too short; minimum length is {min_len}", min_len=min_len
        )

    @classmethod
    def max_len_constraint_failed(cls, loc: Loc, value: Any, max_len: int) -> Error:
        """Create error signalling that the *value* is too long.

        :param loc:
            The location of the error.

        :param value:
            The incorrect value.

        :param max_len:
            The maximum value length.
        """
        return cls.constraint_failed(loc, value, f"the value is too long; maximum length is {max_len}", max_len=max_len)

    @classmethod
    def regex_constraint_failed(cls, loc: Loc, value: str, regex: str) -> Error:
        """Create error signalling that the *value* did not match expected
        regular expression pattern.

        :param loc:
            The location of the error.

        :param value:
            The incorrect value.

        :param regex:
            The regular expression pattern.
        """
        return cls.constraint_failed(
            loc, value, f"the value does not match regular expression pattern: {regex}", regex=regex
        )

    @staticmethod
    def required_missing(loc: Loc):
        """Create error signalling that the required field has value missing.

        :param loc:
            The location of the error.
        """
        return Error(loc, ErrorCode.REQUIRED_MISSING, "this field is required")

    @staticmethod
    def exception(loc: Loc, value: Any, msg: str, exc_type: type[Exception]) -> Error:
        """Create error from a caught exception.

        :param loc:
            The location of the error.

        :param msg:
            The error message.

        :param value:
            The incorrect value.

        :param exc_type:
            The type of the exception caught.
        """
        return Error(loc, ErrorCode.EXCEPTION, msg, value, {"exc_type": exc_type})
