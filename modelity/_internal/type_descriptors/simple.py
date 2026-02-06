"""Parser factories for the built-in simple types."""

from datetime import date, datetime
from enum import Enum
import ipaddress
import pathlib
from typing import Any, Literal, TypeVar, get_args

from modelity import _utils
from modelity._internal.registry import TypeDescriptorFactoryRegistry
from modelity.error import Error, ErrorFactory
from modelity.interface import IModelVisitor, ITypeDescriptor
from modelity.loc import Loc
from modelity.unset import Unset, UnsetType

T = TypeVar("T")

_DEFAULT_EXPECTED_DATETIME_FORMATS = [
    "YYYY-MM-DDThh:mm:ssZZZZ",
    "YYYY-MM-DDThh:mm:ss",
    "YYYY-MM-DD hh:mm:ssZZZZ",
    "YYYY-MM-DD hh:mm:ss ZZZZ",
    "YYYY-MM-DD hh:mm:ss",
    "YYYYMMDDThhmmssZZZZ",
    "YYYYMMDDThhmmss",
    "YYYYMMDDhhmmssZZZZ",
    "YYYYMMDDhhmmss",
]

_DEFAULT_EXPECTED_DATE_FORMATS = ["YYYY-MM-DD"]

registry = TypeDescriptorFactoryRegistry()


@registry.type_descriptor_factory(UnsetType)
def make_unset_type_descriptor():

    class UnsetTypeDescriptor(ITypeDescriptor):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if value is Unset:
                return value
            errors.append(ErrorFactory.invalid_value(loc, value, [Unset]))
            return Unset

        def accept(self, visitor: IModelVisitor, loc: Loc, value: Any):
            visitor.visit_unset(loc, value)

    return UnsetTypeDescriptor()


@registry.type_descriptor_factory(Any)
def make_any_type_descriptor():

    class AnyTypeDescriptor(ITypeDescriptor):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            return value

        def accept(self, visitor: IModelVisitor, loc: Loc, value: Any):
            visitor.visit_any(loc, value)

    return AnyTypeDescriptor()


@registry.type_descriptor_factory(bool)
def make_bool_type_descriptor(typ: type, type_opts: dict):

    class BoolTypeDescriptor(ITypeDescriptor):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if isinstance(value, bool):
                return value
            if value in true_literals:
                return True
            if value in false_literals:
                return False
            errors.append(
                ErrorFactory.parse_error(loc, value, typ, **extra_data),
            )
            return Unset

        def accept(self, visitor: IModelVisitor, loc: Loc, value: Any):
            visitor.visit_scalar(loc, value)

    true_literals = set(type_opts.get("true_literals") or [])
    false_literals = set(type_opts.get("false_literals") or [])
    extra_data = {}
    if true_literals:
        extra_data["true_literals"] = list(true_literals)
    if false_literals:
        extra_data["false_literals"] = list(false_literals)
    return BoolTypeDescriptor()


@registry.type_descriptor_factory(datetime)
def make_datetime_type_descriptor(type_opts: dict):

    class DateTimeTypeDescriptor(ITypeDescriptor):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if isinstance(value, datetime):
                return value
            if not isinstance(value, str):
                errors.append(ErrorFactory.invalid_type(loc, value, [datetime, str]))
                return Unset
            for fmt in compiled_expected_formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    pass
            errors.append(ErrorFactory.invalid_datetime_format(loc, value, expected_formats))
            return Unset

        def accept(self, visitor: IModelVisitor, loc: Loc, value: Any):
            visitor.visit_scalar(loc, value)

    expected_formats = type_opts.get("expected_datetime_formats") or _DEFAULT_EXPECTED_DATETIME_FORMATS
    compiled_expected_formats = [_utils.compile_datetime_format(x) for x in expected_formats]
    return DateTimeTypeDescriptor()


@registry.type_descriptor_factory(date)
def make_date_type_descriptor(type_opts: dict):
    # TODO: This is almost copy-paste; refactor date and datetime to some common thing

    class DateTypeDescriptor(ITypeDescriptor):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if isinstance(value, date):
                return value
            if not isinstance(value, str):
                errors.append(ErrorFactory.invalid_type(loc, value, [date, str]))
                return Unset
            for fmt in compiled_formats:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    pass
            errors.append(ErrorFactory.invalid_date_format(loc, value, expected_formats))
            return Unset

        def accept(self, visitor: IModelVisitor, loc: Loc, value: Any):
            visitor.visit_scalar(loc, value)

    expected_formats = type_opts.get("expected_date_formats") or _DEFAULT_EXPECTED_DATE_FORMATS
    compiled_formats = [_utils.compile_datetime_format(x) for x in expected_formats]
    return DateTypeDescriptor()


@registry.type_descriptor_factory(Enum)
def make_enum_type_descriptor(typ: type[Enum]):

    class EnumTypeDescriptor(ITypeDescriptor):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            try:
                return typ(value)
            except ValueError:
                errors.append(ErrorFactory.invalid_enum_value(loc, value, typ))
                return Unset

        def accept(self, visitor: IModelVisitor, loc: Loc, value: Any):
            # visitor.visit_any(loc, value.value)
            visitor.visit_scalar(loc, value)

    return EnumTypeDescriptor()


@registry.type_descriptor_factory(Literal)
def make_literal_type_descriptor(typ):

    class LiteralTypeDescriptor(ITypeDescriptor):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if value in expected_values:
                return value
            errors.append(ErrorFactory.invalid_value(loc, value, list(expected_values)))
            return Unset

        def accept(self, visitor: IModelVisitor, loc: Loc, value: Any):
            visitor.visit_scalar(loc, value)

    expected_values = get_args(typ)
    return LiteralTypeDescriptor()


@registry.type_descriptor_factory(type(None))
def make_none_type_descriptor():

    class NoneTypeDescriptor(ITypeDescriptor):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if value is None:
                return value
            errors.append(ErrorFactory.invalid_value(loc, value, [None]))
            return Unset

        def accept(self, visitor: IModelVisitor, loc: Loc, value: Any):
            visitor.visit_none(loc, value)

    return NoneTypeDescriptor()


@registry.type_descriptor_factory(int)
def make_int_type_descriptor():

    class IntTypeDescriptor(ITypeDescriptor):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            try:
                return int(value)
            except (ValueError, TypeError):
                errors.append(ErrorFactory.parse_error(loc, value, int))
                return Unset

        def accept(self, visitor: IModelVisitor, loc: Loc, value: Any):
            visitor.visit_scalar(loc, value)

    return IntTypeDescriptor()


@registry.type_descriptor_factory(float)
def make_float_type_descriptor():

    class FloatTypeDescriptor(ITypeDescriptor):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            try:
                return float(value)
            except (ValueError, TypeError):
                errors.append(ErrorFactory.parse_error(loc, value, float))
                return Unset

        def accept(self, visitor: IModelVisitor, loc: Loc, value: Any):
            visitor.visit_scalar(loc, value)

    return FloatTypeDescriptor()


@registry.type_descriptor_factory(str)
def make_str_type_descriptor():

    class StrTypeDescriptor(ITypeDescriptor):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if isinstance(value, str):
                return value
            errors.append(ErrorFactory.invalid_type(loc, value, [str]))
            return Unset

        def accept(self, visitor: IModelVisitor, loc: Loc, value: Any):
            visitor.visit_scalar(loc, value)

    return StrTypeDescriptor()


@registry.type_descriptor_factory(bytes)
def make_bytes_type_descriptor():

    class BytesTypeDescriptor(ITypeDescriptor):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if isinstance(value, bytes):
                return value
            errors.append(ErrorFactory.invalid_type(loc, value, [bytes]))
            return Unset

        def accept(self, visitor: IModelVisitor, loc: Loc, value: Any):
            visitor.visit_scalar(loc, value)

    return BytesTypeDescriptor()


@registry.type_descriptor_factory(ipaddress.IPv4Address)
def make_ipv4_address_type_descriptor():

    class IPv4TypeDescriptor(ITypeDescriptor):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if isinstance(value, ipaddress.IPv4Address):
                return value
            try:
                return ipaddress.IPv4Address(value)
            except ipaddress.AddressValueError:
                errors.append(ErrorFactory.parse_error(loc, value, ipaddress.IPv4Address, "Not a valid IPv4 address"))
                return Unset

        def accept(self, visitor: IModelVisitor, loc: Loc, value: Any):
            visitor.visit_scalar(loc, value)

    return IPv4TypeDescriptor()


@registry.type_descriptor_factory(ipaddress.IPv6Address)
def make_ipv6_address_type_descriptor():

    class IPv6TypeDescriptor(ITypeDescriptor):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if isinstance(value, ipaddress.IPv6Address):
                return value
            try:
                return ipaddress.IPv6Address(value)
            except ipaddress.AddressValueError:
                errors.append(ErrorFactory.parse_error(loc, value, ipaddress.IPv6Address, "Not a valid IPv6 address"))
                return Unset

        def accept(self, visitor: IModelVisitor, loc: Loc, value: Any):
            visitor.visit_scalar(loc, value)

    return IPv6TypeDescriptor()


@registry.type_descriptor_factory(pathlib.Path)
def make_pathlib_path_type_descriptor(typ: type, type_opts: dict):

    class PathlibPathTypeDescriptor(ITypeDescriptor):

        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if isinstance(value, pathlib.Path):
                return value
            if isinstance(value, bytes):
                try:
                    value = value.decode(bytes_encoding)
                except UnicodeDecodeError:
                    errors.append(ErrorFactory.decode_error(loc, value, [bytes_encoding]))
                    return Unset
            if not isinstance(value, str):
                errors.append(ErrorFactory.invalid_type(loc, value, [str, bytes, typ]))
                return Unset
            return pathlib.Path(value)

        def accept(self, visitor: IModelVisitor, loc: Loc, value: Any):
            visitor.visit_scalar(loc, value)

    bytes_encoding = type_opts.get("bytes_encoding", "utf-8")
    return PathlibPathTypeDescriptor()
