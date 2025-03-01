"""Parser factories for the built-in simple types."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional, TypeVar, get_args

from modelity.error import Error, ErrorFactory
from modelity.exc import UnsupportedTypeError
from modelity.interface import IModelVisitor, ITypeDescriptor
from modelity.loc import Loc
from modelity.unset import Unset

T = TypeVar("T")

_DEFAULT_INPUT_DATETIME_FORMATS = [
    "YYYY-MM-DDThh:mm:ssZZZZ",
    "YYYY-MM-DDThh:mm:ss",
    "YYYY-MM-DD hh:mm:ssZZZZ",
    "YYYY-MM-DD hh:mm:ss",
    "YYYYMMDDThhmmssZZZZ",
    "YYYYMMDDThhmmss",
    "YYYYMMDDhhmmssZZZZ",
    "YYYYMMDDhhmmss",
]

_DEFAULT_OUTPUT_DATETIME_FORMAT = "YYYY-MM-DDThh:mm:ssZZZZ"


def make_bool_type_descriptor(
    true_literals: Optional[set] = None, false_literals: Optional[set] = None
) -> ITypeDescriptor:
    """Make :class:`bool` type descriptor.

    This descriptor accepts only :class:`bool` values and rejects all other,
    without trying to convert to bool. However, it allows to set true- and/or
    false-evaluating constants that, once given, will be treated as either
    boolean's ``True`` or ``False``, accordingly.

    :param true_literals:
        Literals that evaluate to ``True``.

    :param false_literals:
        Literals that evaluate to ``False``.
    """

    class BoolTypeDescriptor:
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if isinstance(value, bool):
                return value
            if value in (true_literals or []):
                return True
            if value in (false_literals or []):
                return False
            errors.append(
                ErrorFactory.invalid_bool(loc, value, true_literals=true_literals, false_literals=false_literals)
            )
            return Unset

        def accept(self, loc, value, visitor: IModelVisitor):
            visitor.visit_scalar(loc, value)

        def validate(self, errors, loc, value):
            return None

    true_literals = set(true_literals) if true_literals else None
    false_literals = set(false_literals) if false_literals else None
    return BoolTypeDescriptor()


def make_datetime_type_descriptor(
    input_datetime_formats: list[str] = None, output_datetime_format: str = None
) -> ITypeDescriptor:
    """Make parser for the :class:`datetime.datetime` type.

    :param input_datetime_formats:
        List of supported datetime formats to override default ones.

        By default, following subset of the ISO8601 standard is supported:

            * YYYY-MM-DDThh:mm:ss
            * YYYY-MM-DDThh:mm:ssZZZZ
            * YYYY-MM-DD hh:mm:ss
            * YYYY-MM-DD hh:mm:ssZZZZ
            * YYYYMMDDThhmmss
            * YYYYMMDDThhmmssZZZZ
            * YYYYMMDDhhmmss
            * YYYYMMDDhhmmssZZZZ

    :param output_datetime_format:
        Datetime format to be used when dumping datetime object to string.

        By default, following format is used:

            YYYY-MM-DDThh:mm:ssZZZZ
    """

    class DateTimeTypeDescriptor:
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if isinstance(value, datetime):
                return value
            if not isinstance(value, str):
                errors.append(ErrorFactory.invalid_datetime(loc, value))
                return Unset
            for fmt in compiled_input_formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    pass
            errors.append(ErrorFactory.unsupported_datetime_format(loc, value, input_formats))
            return Unset

        def accept(self, loc: Loc, value: datetime, visitor: IModelVisitor):
            visitor.visit_scalar(loc, value.strftime(compiled_output_format))

    def compile_format(fmt: str) -> str:
        return (
            fmt.replace("YYYY", "%Y")
            .replace("MM", "%m")
            .replace("DD", "%d")
            .replace("hh", "%H")
            .replace("mm", "%M")
            .replace("ss", "%S")
            .replace("ZZZZ", "%z")
        )

    input_formats = input_datetime_formats or _DEFAULT_INPUT_DATETIME_FORMATS
    compiled_input_formats = [compile_format(x) for x in input_formats]
    output_format = output_datetime_format or _DEFAULT_OUTPUT_DATETIME_FORMAT
    compiled_output_format = compile_format(output_format)
    return DateTimeTypeDescriptor()


def make_enum_type_descriptor(typ: type[Enum]) -> ITypeDescriptor:
    """Make enumerated type descriptor.

    :param typ:
        Enumerate typed to create descriptor for.
    """

    class EnumTypeDescriptor:
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            try:
                return typ(value)
            except ValueError:
                errors.append(ErrorFactory.value_out_of_range(loc, value, allowed_values))
                return Unset

        def accept(self, loc: Loc, value: Enum, visitor: IModelVisitor):
            visitor.visit_scalar(loc, value.value)

    allowed_values = tuple(typ)
    return EnumTypeDescriptor()


def make_literal_type_descriptor(typ) -> ITypeDescriptor:
    """Make descriptor for the :class:`typing.Literal` types.

    :param typ:
        The literal type to make descriptor for.
    """

    class LiteralTypeDescriptor:
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if value in allowed_values:
                return value
            errors.append(ErrorFactory.value_out_of_range(loc, value, allowed_values))
            return Unset

        def accept(self, loc: Loc, value: Any, visitor: IModelVisitor):
            visitor.visit_scalar(loc, value)

        def validate(self, errors: list[Error], loc: Loc, value: Any):
            return None

    allowed_values = get_args(typ)
    return LiteralTypeDescriptor()


def make_none_type_descriptor() -> ITypeDescriptor:
    """Make parser for the ``type(None)`` type.

    The parser produced by this function will only accept ``None`` value. It
    was added for use in complex types, like unions, to avoid special handling
    of the ``None`` values. Direct use of this parser is rather pointless.
    """

    class NoneTypeDescriptor:
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if value is None:
                return value
            errors.append(ErrorFactory.value_out_of_range(loc, value, (None,)))
            return Unset

        def accept(self, loc: Loc, value: None, visitor: IModelVisitor):
            visitor.visit_none(loc, value)

        def validate(self, errors: list[Error], loc: Loc, value: Any):
            return None

    return NoneTypeDescriptor()


def make_numeric_type_descriptor(typ: type[T]) -> ITypeDescriptor[T]:
    """Make type descriptor for a numeric type.

    Currently supported numeric types are:

        * :class:`int`
        * :class:`float`

    If unsupported type is given, then :exc:`modelity.exc.UnsupportedTypeError`
    exception will be raised.

    :param typ:
        The numeric type to create descriptor for.
    """

    class IntTypeDescriptor:
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            try:
                return int(value)
            except (ValueError, TypeError):
                errors.append(ErrorFactory.invalid_integer(loc, value))
                return Unset

        def accept(self, loc: Loc, value: int, visitor: IModelVisitor):
            visitor.visit_scalar(loc, value)

        def validate(self, errors: list[Error], loc: Loc, value: Any):
            return None

    class FloatTypeDescriptor:
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            try:
                return float(value)
            except (ValueError, TypeError):
                errors.append(ErrorFactory.invalid_float(loc, value))
                return Unset

        def accept(self, loc: Loc, value: float, visitor: IModelVisitor):
            visitor.visit_scalar(loc, value)

        def validate(self, errors: list[Error], loc: Loc, value: Any):
            return None

    if issubclass(typ, int):
        return IntTypeDescriptor()
    if issubclass(typ, float):
        return FloatTypeDescriptor()
    raise UnsupportedTypeError(typ)


def make_str_type_descriptor() -> ITypeDescriptor:
    """Make type descriptor for the :class:`str` built-in type."""

    class StrTypeDescriptor:
        def parse(self, errors: list[Error], loc: Loc, value: str):
            if isinstance(value, str):
                return value
            errors.append(ErrorFactory.string_value_required(loc, value))
            return Unset

        def accept(self, loc: Loc, value: str, visitor: IModelVisitor):
            visitor.visit_scalar(loc, value)

        def validate(self, errors: list[Error], loc: Loc, value: str):
            return None

    return StrTypeDescriptor()


def make_bytes_type_descriptor() -> ITypeDescriptor:
    """Make descriptor for the built-in :class:`bytes` type."""

    class BytesTypeDescriptor:
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if isinstance(value, bytes):
                return value
            errors.append(ErrorFactory.bytes_value_required(loc, value))
            return Unset

        def accept(self, loc: Loc, value: bytes, visitor: IModelVisitor):
            visitor.visit_scalar(loc, value)

    return BytesTypeDescriptor()
