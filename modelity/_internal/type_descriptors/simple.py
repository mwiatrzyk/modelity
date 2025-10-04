"""Parser factories for the built-in simple types."""

from ctypes import Union
from datetime import date, datetime
from enum import Enum
import ipaddress
from numbers import Number
import pathlib
from typing import Any, Literal, TypeVar, cast, get_args

from modelity._internal.registry import TypeDescriptorFactoryRegistry
from modelity.error import Error, ErrorFactory
from modelity.interface import IModelVisitor, ITypeDescriptor
from modelity.loc import Loc
from modelity.unset import Unset, UnsetType

T = TypeVar("T")

_DEFAULT_INPUT_DATETIME_FORMATS = [
    "YYYY-MM-DDThh:mm:ssZZZZ",
    "YYYY-MM-DD hh:mm:ssZZZZ",
    "YYYY-MM-DD hh:mm:ss ZZZZ",
    "YYYY-MM-DDThh:mm:ss",
    "YYYY-MM-DD hh:mm:ss",
    "YYYYMMDDThhmmssZZZZ",
    "YYYYMMDDThhmmss",
    "YYYYMMDDhhmmssZZZZ",
    "YYYYMMDDhhmmss",
]

_DEFAULT_INPUT_DATE_FORMATS = ["YYYY-MM-DD"]

_DEFAULT_OUTPUT_DATETIME_FORMAT = "YYYY-MM-DDThh:mm:ssZZZZ"

_DEFAULT_OUTPUT_DATE_FORMAT = "YYYY-MM-DD"

registry = TypeDescriptorFactoryRegistry()


@registry.type_descriptor_factory(UnsetType)
def make_unset_type_descriptor():

    class UnsetTypeDescriptor(ITypeDescriptor):
        def parse(self, errors, loc, value):
            if value is Unset:
                return value
            errors.append(ErrorFactory.value_not_allowed(loc, value, (Unset,)))
            return Unset

        def accept(self, visitor, loc, value):
            visitor.visit_unset(loc, value)

    return UnsetTypeDescriptor()


@registry.type_descriptor_factory(Any)
def make_any_type_descriptor():

    class AnyTypeDescriptor(ITypeDescriptor):
        def parse(self, errors, loc, value):
            return value

        def accept(self, visitor, loc, value):
            visitor.visit_any(loc, value)

    return AnyTypeDescriptor()


@registry.type_descriptor_factory(bool)
def make_bool_type_descriptor(type_opts: dict):

    class BoolTypeDescriptor(ITypeDescriptor):
        def parse(self, errors, loc, value):
            if isinstance(value, bool):
                return value
            if value in true_literals:
                return True
            if value in false_literals:
                return False
            errors.append(
                ErrorFactory.bool_parsing_error(loc, value, true_literals=true_literals, false_literals=false_literals)
            )
            return Unset

        def accept(self, visitor, loc, value):
            visitor.visit_bool(loc, value)

    true_literals = set(type_opts.get("true_literals") or [])
    false_literals = set(type_opts.get("false_literals") or [])
    return BoolTypeDescriptor()


@registry.type_descriptor_factory(datetime)
def make_datetime_type_descriptor(type_opts: dict):

    class DateTimeTypeDescriptor(ITypeDescriptor):
        def parse(self, errors, loc, value):
            if isinstance(value, datetime):
                return value
            if not isinstance(value, str):
                errors.append(ErrorFactory.datetime_parsing_error(loc, value))
                return Unset
            for fmt in compiled_input_formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    pass
            errors.append(ErrorFactory.unsupported_datetime_format(loc, value, input_formats))
            return Unset

        def accept(self, visitor, loc, value):
            visitor.visit_string(loc, value.strftime(compiled_output_format))

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

    input_formats = type_opts.get("input_datetime_formats") or _DEFAULT_INPUT_DATETIME_FORMATS
    output_format = type_opts.get("output_datetime_format") or _DEFAULT_OUTPUT_DATETIME_FORMAT
    compiled_input_formats = [compile_format(x) for x in input_formats]
    compiled_output_format = compile_format(output_format)
    return DateTimeTypeDescriptor()


@registry.type_descriptor_factory(date)
def make_date_type_descriptor(type_opts: dict):
    # TODO: This is almost copy-paste; refactor date and datetime to some common thing

    class DateTypeDescriptor(ITypeDescriptor):
        def parse(self, errors, loc, value):
            if isinstance(value, date):
                return value
            if not isinstance(value, str):
                errors.append(ErrorFactory.date_parsing_error(loc, value))
                return Unset
            for fmt in compiled_input_formats:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    pass
            errors.append(ErrorFactory.unsupported_date_format(loc, value, input_formats))
            return Unset

        def accept(self, visitor, loc, value):
            visitor.visit_string(loc, value.strftime(compiled_output_format))

    def compile_format(fmt: str) -> str:
        return fmt.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")

    input_formats = type_opts.get("input_date_formats") or _DEFAULT_INPUT_DATE_FORMATS
    output_format = type_opts.get("output_date_format") or _DEFAULT_OUTPUT_DATE_FORMAT
    compiled_input_formats = [compile_format(x) for x in input_formats]
    compiled_output_format = compile_format(output_format)
    return DateTypeDescriptor()


@registry.type_descriptor_factory(Enum)
def make_enum_type_descriptor(typ: type[Enum]):

    class EnumTypeDescriptor(ITypeDescriptor):
        def parse(self, errors, loc, value):
            try:
                return typ(value)
            except ValueError:
                errors.append(ErrorFactory.value_not_allowed(loc, value, allowed_values))
                return Unset

        def accept(self, visitor, loc, value):
            visitor.visit_any(loc, value.value)

    allowed_values = tuple(typ)
    return EnumTypeDescriptor()


@registry.type_descriptor_factory(Literal)
def make_literal_type_descriptor(typ):

    class LiteralTypeDescriptor(ITypeDescriptor):
        def parse(self, errors, loc, value):
            if value in allowed_values:
                return value
            errors.append(ErrorFactory.value_not_allowed(loc, value, allowed_values))
            return Unset

        def accept(self, visitor, loc, value):
            visitor.visit_any(loc, value)

    allowed_values = get_args(typ)
    return LiteralTypeDescriptor()


@registry.type_descriptor_factory(type(None))
def make_none_type_descriptor():

    class NoneTypeDescriptor(ITypeDescriptor):
        def parse(self, errors, loc, value):
            if value is None:
                return value
            errors.append(ErrorFactory.value_not_allowed(loc, value, (None,)))
            return Unset

        def accept(self, visitor, loc, value):
            visitor.visit_none(loc, value)

    return NoneTypeDescriptor()


@registry.type_descriptor_factory(int)
def make_int_type_descriptor():

    class IntTypeDescriptor(ITypeDescriptor):
        def parse(self, errors, loc, value):
            try:
                return int(value)
            except (ValueError, TypeError):
                errors.append(ErrorFactory.integer_parsing_error(loc, value))
                return Unset

        def accept(self, visitor, loc, value):
            visitor.visit_number(loc, cast(Number, value))

    return IntTypeDescriptor()


@registry.type_descriptor_factory(float)
def make_float_type_descriptor():

    class FloatTypeDescriptor(ITypeDescriptor):
        def parse(self, errors, loc, value):
            try:
                return float(value)
            except (ValueError, TypeError):
                errors.append(ErrorFactory.float_parsing_error(loc, value))
                return Unset

        def accept(self, visitor, loc, value):
            visitor.visit_number(loc, cast(Number, value))

    return FloatTypeDescriptor()


@registry.type_descriptor_factory(str)
def make_str_type_descriptor():

    class StrTypeDescriptor(ITypeDescriptor):
        def parse(self, errors, loc, value):
            if isinstance(value, str):
                return value
            errors.append(ErrorFactory.string_value_required(loc, value))
            return Unset

        def accept(self, visitor, loc, value):
            visitor.visit_string(loc, value)

    return StrTypeDescriptor()


@registry.type_descriptor_factory(bytes)
def make_bytes_type_descriptor():

    class BytesTypeDescriptor(ITypeDescriptor):
        def parse(self, errors, loc, value):
            if isinstance(value, bytes):
                return value
            errors.append(ErrorFactory.bytes_value_required(loc, value))
            return Unset

        def accept(self, visitor, loc, value):
            visitor.visit_string(loc, value.decode())  # TODO: Add support for other formats

    return BytesTypeDescriptor()


@registry.type_descriptor_factory(ipaddress.IPv4Address)
def make_ipv4_address_type_descriptor():

    class IPv4TypeDescriptor(ITypeDescriptor):
        def parse(self, errors, loc, value):
            if isinstance(value, ipaddress.IPv4Address):
                return value
            try:
                return ipaddress.IPv4Address(value)
            except ipaddress.AddressValueError:
                errors.append(ErrorFactory.parsing_error(loc, value, "not a valid IPv4 address", ipaddress.IPv4Address))
                return Unset

        def accept(self, visitor, loc, value):
            visitor.visit_string(loc, str(value))

    return IPv4TypeDescriptor()


@registry.type_descriptor_factory(ipaddress.IPv6Address)
def make_ipv6_address_type_descriptor():

    class IPv6TypeDescriptor(ITypeDescriptor):
        def parse(self, errors, loc, value):
            if isinstance(value, ipaddress.IPv6Address):
                return value
            try:
                return ipaddress.IPv6Address(value)
            except ipaddress.AddressValueError:
                errors.append(ErrorFactory.parsing_error(loc, value, "not a valid IPv6 address", ipaddress.IPv6Address))
                return Unset

        def accept(self, visitor, loc, value):
            visitor.visit_string(loc, str(value))

    return IPv6TypeDescriptor()


@registry.type_descriptor_factory(pathlib.Path)
def make_pathlib_path_type_descriptor(typ: type, type_opts: dict):

    class PathlibPathTypeDescriptor(ITypeDescriptor):

        def parse(self, errors, loc, value):
            if isinstance(value, pathlib.Path):
                return value
            if isinstance(value, bytes):
                try:
                    value = value.decode(bytes_encoding)
                except UnicodeDecodeError:
                    errors.append(
                        ErrorFactory.parsing_error(
                            loc,
                            value,
                            f"{parsing_error_msg}; could not decode bytes using {bytes_encoding!r} codec",
                            typ,
                        )
                    )
                    return Unset
            if not isinstance(value, str):
                errors.append(ErrorFactory.parsing_error(loc, value, parsing_error_msg, typ))
                return Unset
            return pathlib.Path(value)

        def accept(self, visitor, loc, value):
            visitor.visit_string(loc, str(value))

    parsing_error_msg = "not a valid path value"
    bytes_encoding = type_opts.get("bytes_encoding", "utf-8")
    return PathlibPathTypeDescriptor()
