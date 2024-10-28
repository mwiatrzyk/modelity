from numbers import Number
from typing import Any, Tuple, Type
from modelity.error import Error
from modelity.loc import Loc


class ErrorFactoryHelper:

    @staticmethod
    def integer_required(loc: Loc) -> Error:
        return Error.create(loc, "modelity.IntegerRequired")

    @staticmethod
    def unsupported_type(loc: Loc, supported_types: tuple) -> Error:
        return Error.create(loc, "modelity.UnsupportedType", supported_types=supported_types)

    @staticmethod
    def required_missing(loc: Loc) -> Error:
        return Error.create(loc, "modelity.RequiredMissing")

    @staticmethod
    def none_required(loc: Loc) -> Error:
        return Error.create(loc, "modelity.NoneRequired")

    @staticmethod
    def float_required(loc: Loc) -> Error:
        return Error.create(loc, "modelity.FloatRequired")

    @staticmethod
    def string_required(loc: Loc) -> Error:
        return Error.create(loc, "modelity.StringRequired")

    @staticmethod
    def bytes_required(loc: Loc) -> Error:
        return Error.create(loc, "modelity.BytesRequired")

    @staticmethod
    def unicode_decode_error(loc: Loc, encoding: str):
        return Error.create(loc, "modelity.UnicodeDecodeError", encoding=encoding)

    @staticmethod
    def boolean_required(loc: Loc) -> Error:
        return Error.create(loc, "modelity.BooleanRequired")

    @staticmethod
    def iterable_required(loc: Loc) -> Error:
        return Error.create(loc, "modelity.IterableRequired")

    @staticmethod
    def hashable_required(loc: Loc) -> Error:
        return Error.create(loc, "modelity.HashableRequired")

    @staticmethod
    def mapping_required(loc: Loc) -> Error:
        return Error.create(loc, "modelity.MappingRequired")

    @staticmethod
    def datetime_required(loc: Loc) -> Error:
        return Error.create(loc, "modelity.DatetimeRequired")

    @staticmethod
    def unknown_datetime_format(loc: Loc, supported_formats: tuple) -> Error:
        return Error.create(loc, "modelity.UnknownDatetimeFormat", supported_formats=supported_formats)

    @staticmethod
    def invalid_enum(loc: Loc, supported_values: tuple):
        return Error.create(loc, "modelity.InvalidEnum", supported_values=supported_values)

    @staticmethod
    def invalid_literal(loc: Loc, supported_values: tuple):
        return Error.create(loc, "modelity.InvalidLiteral", supported_values=supported_values)

    @staticmethod
    def invalid_tuple_format(loc: Loc, expected_format: tuple):
        return Error.create(loc, "modelity.InvalidTupleFormat", expected_format=expected_format)

    @staticmethod
    def value_too_low(loc: Loc, min_inclusive: Any = None, min_exclusive: Any = None):
        return Error.create(loc, "modelity.ValueTooLow", min_inclusive=min_inclusive, min_exclusive=min_exclusive)

    @staticmethod
    def value_too_high(loc: Loc, max_inclusive: Any = None, max_exclusive: Any = None):
        return Error.create(loc, "modelity.ValueTooHigh", max_inclusive=max_inclusive, max_exclusive=max_exclusive)

    @staticmethod
    def value_too_short(loc: Loc, min_length: int):
        return Error.create(loc, "modelity.ValueTooShort", min_length=min_length)

    @staticmethod
    def value_too_long(loc: Loc, max_length: int):
        return Error.create(loc, "modelity.ValueTooLong", max_length=max_length)

    @staticmethod
    def value_error(loc: Loc, message: str):
        return Error.create(loc, "modelity.ValueError", message=message)

    @staticmethod
    def type_error(loc: Loc, message: str):
        return Error.create(loc, "modelity.TypeError", message=message)
