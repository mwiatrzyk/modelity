from typing import Any, Type

from modelity.error import Error
from modelity.interface import IModel
from modelity.loc import Loc


class ErrorFactoryHelper:

    @staticmethod
    def integer_required(loc: Loc) -> Error:
        return Error(loc, "modelity.IntegerRequired", msg="not a valid integer number")

    @staticmethod
    def unsupported_type(loc: Loc, supported_types: tuple) -> Error:
        msg = f"value of unsupported type given; supported types are: {', '.join(repr(x) for x in supported_types)}"
        return Error(loc, "modelity.UnsupportedType", {"supported_types": supported_types}, msg)

    @staticmethod
    def required_missing(loc: Loc) -> Error:
        return Error(loc, "modelity.RequiredMissing", msg="this field is required")

    @staticmethod
    def none_required(loc: Loc) -> Error:
        return Error(loc, "modelity.NoneRequired", msg="not a None value")

    @staticmethod
    def float_required(loc: Loc) -> Error:
        return Error(loc, "modelity.FloatRequired", msg="not a valid float number")

    @staticmethod
    def string_required(loc: Loc) -> Error:
        return Error(loc, "modelity.StringRequired", msg="not a valid string value")

    @staticmethod
    def bytes_required(loc: Loc) -> Error:
        return Error(loc, "modelity.BytesRequired", msg="not a valid bytes value")

    @staticmethod
    def unicode_decode_error(loc: Loc, codec: str):
        return Error(loc, "modelity.UnicodeDecodeError", {"codec": codec}, f"could not decode value using {codec!r} codec")

    @staticmethod
    def boolean_required(loc: Loc) -> Error:
        return Error(loc, "modelity.BooleanRequired", msg="not a valid boolean value")

    @staticmethod
    def iterable_required(loc: Loc) -> Error:
        return Error(loc, "modelity.IterableRequired", msg="not a valid iterable value")

    @staticmethod
    def hashable_required(loc: Loc) -> Error:
        return Error(loc, "modelity.HashableRequired", msg="not a valid hashable value")

    @staticmethod
    def mapping_required(loc: Loc) -> Error:
        return Error(loc, "modelity.MappingRequired", msg="not a valid mapping value")

    @staticmethod
    def datetime_required(loc: Loc) -> Error:
        return Error(loc, "modelity.DatetimeRequired", msg="not a valid datetime value")

    @staticmethod
    def unknown_datetime_format(loc: Loc, supported_formats: tuple) -> Error:
        msg = f"unknown datetime format; supported formats are: {', '.join(supported_formats)}"
        return Error(loc, "modelity.UnknownDatetimeFormat", {"supported_formats": supported_formats}, msg)

    @staticmethod
    def invalid_enum(loc: Loc, allowed_values: tuple):
        msg = f"not a valid enum; allowed values are: {', '.join(repr(x) for x in allowed_values)}"
        return Error(loc, "modelity.InvalidEnum", {"allowed_values": allowed_values}, msg)

    @staticmethod
    def invalid_literal(loc: Loc, allowed_values: tuple):
        msg = f"not a valid literal; allowed values are: {', '.join(repr(x) for x in allowed_values)}"
        return Error(loc, "modelity.InvalidLiteral", {"allowed_values": allowed_values}, msg)

    @staticmethod
    def invalid_model(loc: Loc, model_type: Type[IModel]):
        msg = f"not a valid {model_type.__name__!r} model value; need either a mapping, or an instance of {model_type.__name__!r} model"
        return Error(loc, "modelity.InvalidModel", {"model_type": model_type}, msg)

    @staticmethod
    def invalid_tuple_format(loc: Loc, expected_format: tuple):
        msg = f"invalid format of a tuple value; expected format is: {expected_format!r}"
        return Error(loc, "modelity.InvalidTupleFormat", {"expected_format": expected_format}, msg)

    @staticmethod
    def value_too_low(loc: Loc, min_inclusive: Any = None, min_exclusive: Any = None):
        data = {}
        msg = "value must be"
        if min_inclusive is not None:
            data["min_inclusive"] = min_inclusive
            msg = f"{msg} >= {min_inclusive}"
        elif min_exclusive is not None:
            data["min_exclusive"] = min_exclusive
            msg = f"{msg} > {min_exclusive}"
        return Error(loc, "modelity.ValueTooLow", data, msg)

    @staticmethod
    def value_too_high(loc: Loc, max_inclusive: Any = None, max_exclusive: Any = None):
        data = {}
        msg = "value must be"
        if max_inclusive is not None:
            data["max_inclusive"] = max_inclusive
            msg = f"{msg} <= {max_inclusive}"
        elif max_exclusive is not None:
            data["max_exclusive"] = max_exclusive
            msg = f"{msg} < {max_exclusive}"
        return Error(loc, "modelity.ValueTooHigh", data, msg)

    @staticmethod
    def value_too_short(loc: Loc, min_length: int):
        return Error(loc, "modelity.ValueTooShort", {'min_length': min_length}, f"value too short; minimum length is {min_length}")

    @staticmethod
    def value_too_long(loc: Loc, max_length: int):
        return Error(loc, "modelity.ValueTooLong", {'max_length': max_length}, f"value too long; maximum length is {max_length}")

    @staticmethod
    def value_error(loc: Loc, message: str):
        return Error(loc, "modelity.ValueError", msg=message)

    @staticmethod
    def type_error(loc: Loc, message: str):
        return Error(loc, "modelity.TypeError", msg=message)
