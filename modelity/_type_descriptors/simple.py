"""Parser factories for the built-in simple types."""

from datetime import date, datetime
from enum import Enum
from typing import Any, Optional, TypeVar, get_args

from modelity.error import Error, ErrorFactory
from modelity.exc import UnsupportedTypeError
from modelity.interface import IDumpFilter, ITypeDescriptor
from modelity.loc import Loc
from modelity.mixins import EmptyValidateMixin, ExactDumpMixin
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

_DEFAULT_INPUT_DATE_FORMATS = ["YYYY-MM-DD"]

_DEFAULT_OUTPUT_DATETIME_FORMAT = "YYYY-MM-DDThh:mm:ssZZZZ"

_DEFAULT_OUTPUT_DATE_FORMAT = "YYYY-MM-DD"


def make_bool_type_descriptor(
    true_literals: Optional[set] = None, false_literals: Optional[set] = None
) -> ITypeDescriptor:

    class BoolTypeDescriptor(ExactDumpMixin, EmptyValidateMixin):
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

    true_literals = set(true_literals) if true_literals else None
    false_literals = set(false_literals) if false_literals else None
    return BoolTypeDescriptor()


def make_datetime_type_descriptor(
    input_datetime_formats: Optional[list[str]] = None, output_datetime_format: Optional[str] = None
) -> ITypeDescriptor:

    class DateTimeTypeDescriptor(EmptyValidateMixin):
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

        def dump(self, loc: Loc, value: datetime, filter: IDumpFilter):
            return filter(loc, value.strftime(compiled_output_format))

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


def make_date_type_descriptor(
    input_date_formats: Optional[list[str]] = None, output_date_format: Optional[str] = None
) -> ITypeDescriptor:
    # TODO: This is almost copy-paste; refactor date and datetime to some common thing

    class DateTypeDescriptor(EmptyValidateMixin):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if isinstance(value, date):
                return value
            if not isinstance(value, str):
                errors.append(ErrorFactory.invalid_date(loc, value))
                return Unset
            for fmt in compiled_input_formats:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    pass
            errors.append(ErrorFactory.unsupported_date_format(loc, value, input_formats))
            return Unset

        def dump(self, loc: Loc, value: date, filter: IDumpFilter):
            return filter(loc, value.strftime(compiled_output_format))

    def compile_format(fmt: str) -> str:
        return fmt.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")

    input_formats = input_date_formats or _DEFAULT_INPUT_DATE_FORMATS
    compiled_input_formats = [compile_format(x) for x in input_formats]
    output_format = output_date_format or _DEFAULT_OUTPUT_DATE_FORMAT
    compiled_output_format = compile_format(output_format)
    return DateTypeDescriptor()


def make_enum_type_descriptor(typ: type[Enum]) -> ITypeDescriptor:

    class EnumTypeDescriptor(EmptyValidateMixin):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            try:
                return typ(value)
            except ValueError:
                errors.append(ErrorFactory.value_out_of_range(loc, value, allowed_values))
                return Unset

        def dump(self, loc: Loc, value: Enum, filter: IDumpFilter):
            return value.value

    allowed_values = tuple(typ)
    return EnumTypeDescriptor()


def make_literal_type_descriptor(typ) -> ITypeDescriptor:

    class LiteralTypeDescriptor(ExactDumpMixin, EmptyValidateMixin):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if value in allowed_values:
                return value
            errors.append(ErrorFactory.value_out_of_range(loc, value, allowed_values))
            return Unset

    allowed_values = get_args(typ)
    return LiteralTypeDescriptor()


def make_none_type_descriptor() -> ITypeDescriptor:

    class NoneTypeDescriptor(ExactDumpMixin, EmptyValidateMixin):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if value is None:
                return value
            errors.append(ErrorFactory.value_out_of_range(loc, value, (None,)))
            return Unset

    return NoneTypeDescriptor()


def make_numeric_type_descriptor(typ: type[T]) -> ITypeDescriptor[T]:

    class IntTypeDescriptor(ExactDumpMixin, EmptyValidateMixin):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            try:
                return int(value)
            except (ValueError, TypeError):
                errors.append(ErrorFactory.invalid_integer(loc, value))
                return Unset

    class FloatTypeDescriptor(ExactDumpMixin, EmptyValidateMixin):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            try:
                return float(value)
            except (ValueError, TypeError):
                errors.append(ErrorFactory.invalid_float(loc, value))
                return Unset

    if issubclass(typ, int):
        return IntTypeDescriptor()
    if issubclass(typ, float):
        return FloatTypeDescriptor()
    raise UnsupportedTypeError(typ)


def make_str_type_descriptor() -> ITypeDescriptor:

    class StrTypeDescriptor(ExactDumpMixin, EmptyValidateMixin):
        def parse(self, errors: list[Error], loc: Loc, value: str):
            if isinstance(value, str):
                return value
            errors.append(ErrorFactory.string_value_required(loc, value))
            return Unset

    return StrTypeDescriptor()


def make_bytes_type_descriptor() -> ITypeDescriptor:

    class BytesTypeDescriptor(EmptyValidateMixin):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if isinstance(value, bytes):
                return value
            errors.append(ErrorFactory.bytes_value_required(loc, value))
            return Unset

        def dump(self, loc: Loc, value: bytes, filter: IDumpFilter):
            return filter(loc, value.decode())

    return BytesTypeDescriptor()
