import datetime
import enum
import ipaddress
import pathlib
from typing import Any, Literal, Optional, Sequence, get_args, get_origin

from modelity import _utils
from modelity.base import ModelVisitor, TypeHandler
from modelity.error import Error, ErrorFactory
from modelity.loc import Loc
from modelity.unset import Unset, UnsetType


class BoolTypeHandler(TypeHandler):

    def __init__(self, true_literals: Optional[Sequence] = None, false_literals: Optional[Sequence] = None):
        self._true_literals_set = set(true_literals or [])
        self._false_literals_set = set(false_literals or [])
        self._extra_data = {}
        if true_literals is not None:
            self._extra_data["true_literals"] = list(true_literals)
        if false_literals is not None:
            self._extra_data["false_literals"] = list(false_literals)

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        if isinstance(value, bool):
            return value
        if value in self._true_literals_set:
            return True
        if value in self._false_literals_set:
            return False
        errors.append(
            ErrorFactory.parse_error(loc, value, bool, msg=None, **self._extra_data),
        )
        return Unset

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        visitor.visit_scalar(loc, value)


class DateTimeTypeHandler(TypeHandler):

    def __init__(self, typ: type[datetime.datetime | datetime.date], /, expected_formats: Sequence[str]):
        self._typ = typ
        self._expected_formats = list(expected_formats)
        is_date_type = typ is datetime.date
        self._parse_func = self._parse_date if is_date_type else self._parse_datetime
        self._compile_func = _utils.compile_date_format if is_date_type else _utils.compile_datetime_format
        self._invalid_format_func = (
            ErrorFactory.invalid_date_format if is_date_type else ErrorFactory.invalid_datetime_format
        )
        self._expected_formats_compiled = [self._compile_func(x) for x in self._expected_formats]

    def _parse_datetime(self, value: str, format: str) -> datetime.datetime:
        return datetime.datetime.strptime(value, format)

    def _parse_date(self, value: str, format: str) -> datetime.date:
        return datetime.datetime.strptime(value, format).date()

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        if isinstance(value, self._typ):
            return value
        if not isinstance(value, str):
            errors.append(ErrorFactory.invalid_type(loc, value, [self._typ], [str]))
            return Unset
        for fmt in self._expected_formats_compiled:
            try:
                return self._parse_func(value, fmt)
            except ValueError:
                pass
        errors.append(self._invalid_format_func(loc, value, self._expected_formats))
        return Unset

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        visitor.visit_scalar(loc, value)


class EnumTypeHandler(TypeHandler):

    def __init__(self, typ: type[enum.Enum]):
        self._typ = typ

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        try:
            return self._typ(value)
        except ValueError:
            errors.append(ErrorFactory.invalid_enum_value(loc, value, self._typ))
            return Unset

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        visitor.visit_scalar(loc, value)


class LiteralTypeHandler(TypeHandler):

    def __init__(self, typ: Any):
        if get_origin(typ) is not Literal:
            raise TypeError(f"expected Literal, got {typ!r}")
        self._expected_values_list = list(get_args(typ))
        self._expected_values_set = set(self._expected_values_list)

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        if value in self._expected_values_set:
            return value
        errors.append(ErrorFactory.invalid_value(loc, value, self._expected_values_list))
        return Unset

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        visitor.visit_scalar(loc, value)


class NumericTypeHandler(TypeHandler):

    def __init__(self, typ: type[int | float]):
        self._typ = typ

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        try:
            return self._typ(value)
        except (ValueError, TypeError):
            errors.append(ErrorFactory.parse_error(loc, value, self._typ))
            return Unset

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        visitor.visit_scalar(loc, value)


class StrTypeHandler(TypeHandler):

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        if isinstance(value, str):
            return value
        errors.append(ErrorFactory.invalid_type(loc, value, [str]))
        return Unset

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        visitor.visit_scalar(loc, value)


class BytesTypeHandler(TypeHandler):

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        if isinstance(value, bytes):
            return value
        # TODO: decode from base64 string
        errors.append(ErrorFactory.invalid_type(loc, value, [bytes]))
        return Unset

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        visitor.visit_scalar(loc, value)


class IPAddressTypeHandler(TypeHandler):

    def __init__(self, typ: type[ipaddress.IPv4Address | ipaddress.IPv6Address]):
        self._typ = typ
        self._error_type_name = "IPv4"
        if typ is ipaddress.IPv6Address:
            self._error_type_name = "IPv6"

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        if isinstance(value, self._typ):
            return value
        try:
            return self._typ(value)
        except ipaddress.AddressValueError:
            errors.append(
                ErrorFactory.parse_error(loc, value, self._typ, msg=f"Not a valid {self._error_type_name} address")
            )
            return Unset

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        visitor.visit_scalar(loc, value)


class PathTypeHandler(TypeHandler):

    def parse(self, errors: list[Error], loc: Loc, value: Any) -> Any | UnsetType:
        if isinstance(value, pathlib.Path):
            return value
        if not isinstance(value, str):
            errors.append(ErrorFactory.invalid_type(loc, value, [pathlib.Path], [str]))
            return Unset
        return pathlib.Path(value)

    def accept(self, visitor: ModelVisitor, loc: Loc, value: Any):
        visitor.visit_scalar(loc, value)
