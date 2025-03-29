from datetime import datetime, timezone
from enum import Enum
import json
from typing import Annotated, Any, Literal, Optional, Union

import pytest

from modelity.constraints import Ge, Gt, Le, Lt, MinLen, MaxLen, Regex
from modelity.error import ErrorFactory
from modelity.exc import ModelParsingError, ValidationError
from modelity.interface import ITypeDescriptor
from modelity.loc import Loc
from modelity.model import FieldInfo, Model, dump, validate
from modelity.unset import Unset


class EDummy(Enum):
    ONE = 1
    TWO = 2


class Nested(Model):
    bar: int


class CustomType:

    @staticmethod
    def __modelity_type_descriptor__(typ, **opts) -> ITypeDescriptor:

        class CustomTypeDescriptor:

            def parse(self, errors, loc, value):
                return typ(value, **opts)

            def dump(self, loc, value, filter) -> Any:
                return value.value

            def validate(self, root, ctx, errors, loc, value):
                return

        return CustomTypeDescriptor()

    def __init__(self, value, **opts):
        self.value = value
        self.opts = opts

    def __eq__(self, other):
        return self.value == other.value and self.opts == other.opts


class TestModelWithOneField:

    @pytest.fixture
    def model_class(self, field_type: type, field_info: Optional[FieldInfo]):
        if field_info is None:

            class Dummy(Model):
                foo: field_type  # type: ignore

        else:

            class Dummy(Model):
                foo: field_type = field_info  # type: ignore

        return Dummy

    @pytest.fixture
    def model(self, model_class, given_value):
        return model_class(foo=given_value)

    @pytest.mark.parametrize(
        "field_type, field_info, given_value, expected_value",
        [
            (Annotated[float, Ge(0.0), Le(1.0)], None, "0.0", 0.0),
            (Annotated[float, Ge(0.0), Le(1.0)], None, "1.0", 1.0),
            (Annotated[float, Ge(0.0), Lt(1.0)], None, "0.999", 0.999),
            (Annotated[float, Gt(0.0), Le(1.0)], None, "0.111", 0.111),
            (Annotated[str, MinLen(1), MaxLen(3)], None, "a", "a"),
            (Annotated[str, MinLen(1), MaxLen(3)], None, "foo", "foo"),
            (Annotated[str, Regex(r"^[0-9]+$")], None, "0123456789", "0123456789"),
            (
                Annotated[datetime, Ge(datetime(2020, 1, 1))],
                FieldInfo(type_opts={"input_datetime_formats": ["YYYY-MM-DD"]}),
                "2020-01-01",
                datetime(2020, 1, 1),
            ),
            (Any, None, 1, 1),
            (Any, None, 3.14, 3.14),
            (Any, None, "spam", "spam"),
            (dict, None, {}, {}),
            (dict[str, int], None, {}, {}),
            (dict[str, int], None, {"one": "1"}, {"one": 1}),
            (Annotated[dict[str, int], MinLen(1)], None, {"one": "1"}, {"one": 1}),
            (list, None, [], []),
            (list[int], None, ["1", "2", "3"], [1, 2, 3]),
            (set, None, [1, 2, 3], {1, 2, 3}),
            (set[int], None, [1, "2", 3], {1, 2, 3}),
            (tuple, None, [1, "2", 3.14], (1, "2", 3.14)),
            (tuple[int], None, ["123"], (123,)),
            (tuple[int, float, str], None, ["123", "3.14", "spam"], (123, 3.14, "spam")),
            (
                tuple[int, ...],
                None,
                ["1", "2", "3"],
                (
                    1,
                    2,
                    3,
                ),
            ),
            (Nested, None, {}, Nested()),
            (Nested, None, {"bar": "123"}, Nested(bar=123)),
            (Nested, None, Nested(bar=123), Nested(bar=123)),
            (bool, None, True, True),
            (bool, None, False, False),
            (bool, FieldInfo(type_opts={"true_literals": [1]}), 1, True),
            (bool, FieldInfo(type_opts={"false_literals": [0]}), 0, False),
            (datetime, None, "1999-01-31T10:11:22", datetime(1999, 1, 31, 10, 11, 22)),
            (datetime, None, "1999-01-31T10:11:22+0000", datetime(1999, 1, 31, 10, 11, 22, tzinfo=timezone.utc)),
            (
                datetime,
                FieldInfo(type_opts={"input_datetime_formats": ["YYYY-MM-DD"]}),
                "1999-01-31",
                datetime(1999, 1, 31),
            ),
            (EDummy, None, 1, EDummy.ONE),
            (EDummy, None, EDummy.ONE, EDummy.ONE),
            (EDummy, None, 2, EDummy.TWO),
            (EDummy, None, EDummy.TWO, EDummy.TWO),
            (Literal[1, "2", 3.14], None, 1, 1),
            (Literal[1, "2", 3.14], None, "2", "2"),
            (Literal[1, "2", 3.14], None, 3.14, 3.14),
            (type(None), None, None, None),
            (int, None, 1, 1),
            (int, None, "2", 2),
            (float, None, 3.14, 3.14),
            (float, None, "2.71", 2.71),
            (str, None, "foo", "foo"),
            (bytes, None, b"bar", b"bar"),
            (Optional[str], None, "spam", "spam"),
            (Optional[str], None, None, None),
            (Union[str, int], None, "123", "123"),
            (Union[str, int], None, 123, 123),
            (Union[str, int], None, "spam", "spam"),
            (CustomType, None, 1, CustomType(1)),
            (CustomType, FieldInfo(type_opts={"foo": 1}), 1, CustomType(1, foo=1)),
        ],
    )
    def test_parse_successfully(self, model: Model, expected_value):
        assert model.foo == expected_value

    @pytest.mark.parametrize(
        "field_type, field_info, given_value, expected_errors",
        [
            (Annotated[float, Ge(0.0)], None, "-0.1", [ErrorFactory.ge_constraint_failed(Loc("foo"), -0.1, 0.0)]),
            (Annotated[float, Gt(0.0)], None, 0.0, [ErrorFactory.gt_constraint_failed(Loc("foo"), 0.0, 0.0)]),
            (Annotated[float, Le(1.0)], None, 1.1, [ErrorFactory.le_constraint_failed(Loc("foo"), 1.1, 1.0)]),
            (Annotated[float, Lt(1.0)], None, 1.0, [ErrorFactory.lt_constraint_failed(Loc("foo"), 1.0, 1.0)]),
            (Annotated[str, MinLen(1)], None, "", [ErrorFactory.min_len_constraint_failed(Loc("foo"), "", 1)]),
            (Annotated[str, MaxLen(3)], None, "spam", [ErrorFactory.max_len_constraint_failed(Loc("foo"), "spam", 3)]),
            (
                Annotated[str, Regex(r"^[0-9]+$")],
                None,
                "spam",
                [ErrorFactory.regex_constraint_failed(Loc("foo"), "spam", r"^[0-9]+$")],
            ),
            (
                Annotated[datetime, Ge(datetime(2020, 1, 1))],
                FieldInfo(type_opts={"input_datetime_formats": ["YYYY-MM-DD"]}),
                "2019-12-31",
                [ErrorFactory.ge_constraint_failed(Loc("foo"), datetime(2019, 12, 31), datetime(2020, 1, 1))],
            ),
            (dict, None, 123, [ErrorFactory.invalid_dict(Loc("foo"), 123)]),
            (dict[str, int], None, {1: 1}, [ErrorFactory.string_value_required(Loc("foo"), 1)]),
            (dict[str, int], None, {"one": "invalid"}, [ErrorFactory.invalid_integer(Loc("foo", "one"), "invalid")]),
            (int, None, "spam", [ErrorFactory.invalid_integer(Loc("foo"), "spam")]),
            (list, None, "spam", [ErrorFactory.invalid_list(Loc("foo"), "spam")]),
            (list[int], None, [1, 2, "invalid"], [ErrorFactory.invalid_integer(Loc("foo", 2), "invalid")]),
            (set, None, 123, [ErrorFactory.invalid_set(Loc("foo"), 123)]),
            (set[int], None, 123, [ErrorFactory.invalid_set(Loc("foo"), 123)]),
            (
                set[int],
                None,
                [1, 2, "three", 4, "five"],
                [ErrorFactory.invalid_integer(Loc("foo"), "three"), ErrorFactory.invalid_integer(Loc("foo"), "five")],
            ),
            (tuple, None, 123, [ErrorFactory.invalid_tuple(Loc("foo"), 123)]),
            (tuple[int, ...], None, [1, 2, "three"], [ErrorFactory.invalid_integer(Loc("foo", 2), "three")]),
            (
                tuple[int, float],
                None,
                [1, 2.71, "spam"],
                [ErrorFactory.unsupported_tuple_format(Loc("foo"), [1, 2.71, "spam"], (int, float))],
            ),
            (tuple[int, float], None, [1], [ErrorFactory.unsupported_tuple_format(Loc("foo"), [1], (int, float))]),
            (Nested, None, 123, [ErrorFactory.invalid_model(Loc("foo"), 123, Nested)]),
            (Nested, None, {"bar": "invalid"}, [ErrorFactory.invalid_integer(Loc("foo", "bar"), "invalid")]),
            (bool, None, "foo", [ErrorFactory.invalid_bool(Loc("foo"), "foo")]),
            (
                bool,
                FieldInfo(type_opts={"true_literals": ["on"]}),
                "foo",
                [ErrorFactory.invalid_bool(Loc("foo"), "foo", true_literals=set(["on"]))],
            ),
            (
                bool,
                FieldInfo(type_opts={"false_literals": ["off"]}),
                "foo",
                [ErrorFactory.invalid_bool(Loc("foo"), "foo", false_literals=set(["off"]))],
            ),
            (
                bool,
                FieldInfo(type_opts={"true_literals": ["on"], "false_literals": ["off"]}),
                "foo",
                [ErrorFactory.invalid_bool(Loc("foo"), "foo", true_literals=set(["on"]), false_literals=set(["off"]))],
            ),
            (
                datetime,
                None,
                "spam",
                [
                    ErrorFactory.unsupported_datetime_format(
                        Loc("foo"),
                        "spam",
                        supported_formats=(
                            "YYYY-MM-DDThh:mm:ssZZZZ",
                            "YYYY-MM-DDThh:mm:ss",
                            "YYYY-MM-DD hh:mm:ssZZZZ",
                            "YYYY-MM-DD hh:mm:ss",
                            "YYYYMMDDThhmmssZZZZ",
                            "YYYYMMDDThhmmss",
                            "YYYYMMDDhhmmssZZZZ",
                            "YYYYMMDDhhmmss",
                        ),
                    )
                ],
            ),
            (datetime, None, 123, [ErrorFactory.invalid_datetime(Loc("foo"), 123)]),
            (
                datetime,
                FieldInfo(type_opts={"input_datetime_formats": ["YYYY-MM-DD"]}),
                "1999-01-31T10:11:22",
                [ErrorFactory.unsupported_datetime_format(Loc("foo"), "1999-01-31T10:11:22", ("YYYY-MM-DD",))],
            ),
            (EDummy, None, 123, [ErrorFactory.value_out_of_range(Loc("foo"), 123, (EDummy.ONE, EDummy.TWO))]),
            (Literal[1, 2, "foo"], None, "spam", [ErrorFactory.value_out_of_range(Loc("foo"), "spam", (1, 2, "foo"))]),
            (type(None), None, "spam", [ErrorFactory.value_out_of_range(Loc("foo"), "spam", (None,))]),
            (int, None, "invalid", [ErrorFactory.invalid_integer(Loc("foo"), "invalid")]),
            (float, None, "invalid", [ErrorFactory.invalid_float(Loc("foo"), "invalid")]),
            (str, None, 123, [ErrorFactory.string_value_required(Loc("foo"), 123)]),
            (bytes, None, 123, [ErrorFactory.bytes_value_required(Loc("foo"), 123)]),
            (Optional[int], None, "invalid", [ErrorFactory.invalid_integer(Loc("foo"), "invalid")]),
            (
                Union[int, str],
                None,
                {},
                [ErrorFactory.invalid_integer(Loc("foo"), {}), ErrorFactory.string_value_required(Loc("foo"), {})],
            ),
        ],
    )
    def test_parsing_failed(self, model_class: type[Model], given_value, expected_errors):
        with pytest.raises(ModelParsingError) as excinfo:
            model_class(foo=given_value)
        assert type(excinfo.value.model) is model_class
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize(
        "field_type, field_info, given_value, expected_output",
        [
            (Annotated[int, Ge(0), Le(255)], None, "123", {"foo": 123}),
            (Any, None, 1, {"foo": 1}),
            (Any, None, 3.14, {"foo": 3.14}),
            (Any, None, "spam", {"foo": "spam"}),
            (Any, None, [], {"foo": []}),
            (dict, None, {}, {"foo": {}}),
            (dict, None, {"a": 1}, {"foo": {"a": 1}}),
            (dict[int, str], None, {"1": "one"}, {"foo": {1: "one"}}),
            (dict[str, list[int]], None, {"foo": ["1", "2", "3"]}, {"foo": {"foo": [1, 2, 3]}}),
            (list, None, [1, "2", "spam"], {"foo": [1, "2", "spam"]}),
            (list[int], None, [1, "2", "3"], {"foo": [1, 2, 3]}),
            (set, None, [1], {"foo": [1]}),
            (set[int], None, ["2"], {"foo": [2]}),
            (tuple, None, [1, "2"], {"foo": [1, "2"]}),
            (tuple[int, ...], None, [1, "2"], {"foo": [1, 2]}),
            (tuple[int], None, ["1"], {"foo": [1]}),
            (Nested, None, {"bar": "123"}, {"foo": {"bar": 123}}),
            (bool, None, True, {"foo": True}),
            (bool, None, False, {"foo": False}),
            (
                datetime,
                None,
                datetime(1999, 1, 31, 10, 11, 22, tzinfo=timezone.utc),
                {"foo": "1999-01-31T10:11:22+0000"},
            ),
            (
                datetime,
                FieldInfo(type_opts={"output_datetime_format": "YYYY-MM-DD"}),
                datetime(1999, 1, 31, 10, 11, 22, tzinfo=timezone.utc),
                {"foo": "1999-01-31"},
            ),
            (EDummy, None, EDummy.ONE, {"foo": 1}),
            (EDummy, None, EDummy.TWO, {"foo": 2}),
            (Literal[1, 3.14, "spam"], None, 1, {"foo": 1}),
            (Literal[1, 3.14, "spam"], None, 3.14, {"foo": 3.14}),
            (Literal[1, 3.14, "spam"], None, "spam", {"foo": "spam"}),
            (type(None), None, None, {"foo": None}),
            (int, None, "123", {"foo": 123}),
            (float, None, "3.14", {"foo": 3.14}),
            (str, None, "spam", {"foo": "spam"}),
            (bytes, None, b"spam", {"foo": "spam"}),
            (Optional[int], None, 123, {"foo": 123}),
            (Optional[int], None, None, {"foo": None}),
            (Union[int, Nested], None, 123, {"foo": 123}),
            (Union[int, Nested], None, {"bar": "123"}, {"foo": {"bar": 123}}),
            (Union[int, Nested, float], None, "3.14", {"foo": 3.14}),
            (Union[int, Nested, float], None, Unset, {"foo": Unset}),
            (CustomType, None, 1, {"foo": 1}),
        ],
    )
    def test_dump(self, model: Model, expected_output):
        assert dump(model) == expected_output

    @pytest.mark.parametrize(
        "field_type, field_info, given_value, dump_opts, expected_output",
        [
            (Nested, None, {}, {"exclude_unset": True}, {"foo": {}}),
            (Nested, None, Unset, {"exclude_unset": True}, {}),
            (Nested, None, {"bar": 123}, {"exclude_if": lambda l, v: Loc("foo", "bar").is_parent_of(l)}, {"foo": {}}),
            (Nested, None, {"bar": 123}, {"exclude_if": lambda l, v: Loc("foo").is_parent_of(l)}, {}),
            (int, None, Unset, {"exclude_unset": True}, {}),
            (type(None), None, Unset, {"exclude_unset": True}, {}),
            (type(None), None, Unset, {"exclude_if": lambda l, v: v is Unset}, {}),
            (type(None), None, None, {"exclude_unset": True}, {"foo": None}),
            (type(None), None, None, {"exclude_none": True}, {}),
            (type(None), None, None, {"exclude_if": lambda l, v: v is None}, {}),
            (Optional[int], None, None, {"exclude_none": True}, {}),
            (Optional[int], None, 123, {"exclude_none": True}, {"foo": 123}),
        ],
    )
    def test_dump_with_options(self, model: Model, dump_opts, expected_output):
        assert dump(model, **dump_opts) == expected_output

    @pytest.mark.parametrize(
        "field_type, field_info, given_value, expected_output",
        [
            (Annotated[list, MinLen(1)], None, [1], [1]),
            (Any, None, 1, 1),
            (dict, None, {"one": "1"}, {"one": "1"}),
            (dict[str, int], None, {"one": "1"}, {"one": 1}),
            (dict[str, Nested], None, {"one": {"bar": 123}}, {"one": Nested(bar=123)}),
            (list, None, [], []),
            (list[Nested], None, [{"bar": 123}], [Nested(bar=123)]),
            (set, None, [], set()),
            (set[int], None, [123], {123}),
            (tuple, None, [1, 2, 3], (1, 2, 3)),
            (tuple[int, ...], None, [1, 2, 3], (1, 2, 3)),
            (tuple[Nested, ...], None, [{"bar": 1}, {"bar": 2}], (Nested(bar=1), Nested(bar=2))),
            (tuple[int, float], None, [1, 3.14], (1, 3.14)),
            (Nested, None, {"bar": 1}, Nested(bar=1)),
            (bool, None, True, True),
            (datetime, None, "1999-01-01T00:00:00", datetime(1999, 1, 1, 0, 0, 0)),
            (EDummy, None, 1, EDummy.ONE),
            (Literal[1, 3.14, "foo"], None, 1, 1),
            (type(None), None, None, None),
            (int, None, 1, 1),
            (float, None, 3.14, 3.14),
            (str, None, "foo", "foo"),
            (bytes, None, b"foo", b"foo"),
            (Optional[Nested], None, {"bar": 1}, Nested(bar=1)),
            (Optional[Nested], None, None, None),
            (Union[int, Nested], None, 1, 1),
            (Union[int, Nested], None, {"bar": 2}, Nested(bar=2)),
            (CustomType, None, 1, CustomType(1)),
        ],
    )
    def test_validate_model_successfully(self, model: Model, expected_output):
        assert model.foo == expected_output
        validate(model)

    def clear_foo(model: Model):
        model.foo.clear()

    @pytest.mark.parametrize(
        "field_type, field_info, given_value, modifier_func, expected_errors",
        [
            (
                Annotated[list, MinLen(1)],
                None,
                [1],
                clear_foo,
                [ErrorFactory.min_len_constraint_failed(Loc("foo"), [], 1)],
            ),
            (dict[str, Nested], None, {"one": {}}, None, [ErrorFactory.required_missing(Loc("foo", "one", "bar"))]),
            (list[Nested], None, [{}], None, [ErrorFactory.required_missing(Loc("foo", 0, "bar"))]),
            (tuple[Nested, ...], None, [{}], None, [ErrorFactory.required_missing(Loc("foo", 0, "bar"))]),
            (
                tuple[int, str, Nested],
                None,
                [1, "foo", {}],
                None,
                [ErrorFactory.required_missing(Loc("foo", 2, "bar"))],
            ),
            (Nested, None, {}, None, [ErrorFactory.required_missing(Loc("foo", "bar"))]),
            (Optional[Nested], None, {}, None, [ErrorFactory.required_missing(Loc("foo", "bar"))]),
            (Union[int, Nested], None, {}, None, [ErrorFactory.required_missing(Loc("foo", "bar"))]),
        ],
    )
    def test_validation_fails_if_model_is_not_valid(self, model: Model, modifier_func, expected_errors):
        if modifier_func:
            modifier_func(model)
        with pytest.raises(ValidationError) as excinfo:
            validate(model)
        assert excinfo.value.model is model
        assert excinfo.value.errors == tuple(expected_errors)
