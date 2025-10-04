from datetime import date, datetime, timezone
from enum import Enum
import textwrap
from typing import Annotated, Any, Literal, Optional, Union

import pytest

from mockify.api import Mock, ordered, satisfied, Raise, Return

from modelity.constraints import Ge, Gt, Le, Lt, MinLen, MaxLen, Regex
from modelity.error import Error, ErrorFactory
from modelity.exc import ParsingError, ParsingError, ValidationError
from modelity.interface import IModelVisitor, ITypeDescriptor
from modelity.loc import Loc
from modelity.model import FieldInfo, Model
from modelity.hooks import (
    field_postprocessor,
    field_preprocessor,
    field_validator,
    model_postvalidator,
    model_prevalidator,
)
from modelity.unset import Unset
from modelity.helpers import dump, validate


class EDummy(Enum):
    ONE = 1
    TWO = 2


class Nested(Model):
    bar: int


@pytest.fixture
def mock():
    mock = Mock("mock")
    with satisfied(mock):
        yield mock


@pytest.fixture
def sut(SUT):
    return SUT()


class CustomType:

    @staticmethod
    def __modelity_type_descriptor__(typ, type_opts: dict) -> ITypeDescriptor:

        class CustomTypeDescriptor(ITypeDescriptor):

            def parse(self, errors, loc, value):
                return typ(value, **type_opts)

            def accept(self, visitor, loc, value):
                visitor.visit_any(loc, value.value)

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
            (datetime, None, "1999-01-31 10:11:22+0000", datetime(1999, 1, 31, 10, 11, 22, tzinfo=timezone.utc)),
            (datetime, None, "1999-01-31 10:11:22 +0000", datetime(1999, 1, 31, 10, 11, 22, tzinfo=timezone.utc)),
            (
                datetime,
                FieldInfo(type_opts={"input_datetime_formats": ["YYYY-MM-DD"]}),
                "1999-01-31",
                datetime(1999, 1, 31),
            ),
            (date, None, "1999-01-31", date(1999, 1, 31)),
            (date, FieldInfo(type_opts={"input_date_formats": ["YYYY-MM-DD"]}), "1999-01-31", date(1999, 1, 31)),
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
            (dict, None, 123, [ErrorFactory.dict_parsing_error(Loc("foo"), 123)]),
            (dict[str, int], None, {1: 1}, [ErrorFactory.string_value_required(Loc("foo", "_"), 1)]),
            (
                dict[str, int],
                None,
                {"one": "invalid"},
                [ErrorFactory.integer_parsing_error(Loc("foo", "one"), "invalid")],
            ),
            (int, None, "spam", [ErrorFactory.integer_parsing_error(Loc("foo"), "spam")]),
            (list, None, "spam", [ErrorFactory.list_parsing_error(Loc("foo"), "spam")]),
            (list[int], None, [1, 2, "invalid"], [ErrorFactory.integer_parsing_error(Loc("foo", 2), "invalid")]),
            (set, None, 123, [ErrorFactory.set_parsing_error(Loc("foo"), 123)]),
            (set[int], None, 123, [ErrorFactory.set_parsing_error(Loc("foo"), 123)]),
            (
                set[int],
                None,
                [1, 2, "three", 4, "five"],
                [
                    ErrorFactory.integer_parsing_error(Loc("foo") + Loc.irrelevant(), "three"),
                    ErrorFactory.integer_parsing_error(Loc("foo") + Loc.irrelevant(), "five"),
                ],
            ),
            (tuple, None, 123, [ErrorFactory.tuple_parsing_error(Loc("foo"), 123)]),
            (tuple[int, ...], None, [1, 2, "three"], [ErrorFactory.integer_parsing_error(Loc("foo", 2), "three")]),
            (
                tuple[int, float],
                None,
                [1, 2.71, "spam"],
                [ErrorFactory.invalid_tuple_format(Loc("foo"), [1, 2.71, "spam"], (int, float))],
            ),
            (tuple[int, float], None, [1], [ErrorFactory.invalid_tuple_format(Loc("foo"), [1], (int, float))]),
            (Nested, None, 123, [ErrorFactory.model_parsing_error(Loc("foo"), 123, Nested)]),
            (Nested, None, {"bar": "invalid"}, [ErrorFactory.integer_parsing_error(Loc("foo", "bar"), "invalid")]),
            (bool, None, "foo", [ErrorFactory.bool_parsing_error(Loc("foo"), "foo")]),
            (
                bool,
                FieldInfo(type_opts={"true_literals": ["on"]}),
                "foo",
                [ErrorFactory.bool_parsing_error(Loc("foo"), "foo", true_literals=set(["on"]))],
            ),
            (
                bool,
                FieldInfo(type_opts={"false_literals": ["off"]}),
                "foo",
                [ErrorFactory.bool_parsing_error(Loc("foo"), "foo", false_literals=set(["off"]))],
            ),
            (
                bool,
                FieldInfo(type_opts={"true_literals": ["on"], "false_literals": ["off"]}),
                "foo",
                [
                    ErrorFactory.bool_parsing_error(
                        Loc("foo"), "foo", true_literals=set(["on"]), false_literals=set(["off"])
                    )
                ],
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
                            "YYYY-MM-DD hh:mm:ssZZZZ",
                            "YYYY-MM-DD hh:mm:ss ZZZZ",
                            "YYYY-MM-DDThh:mm:ss",
                            "YYYY-MM-DD hh:mm:ss",
                            "YYYYMMDDThhmmssZZZZ",
                            "YYYYMMDDThhmmss",
                            "YYYYMMDDhhmmssZZZZ",
                            "YYYYMMDDhhmmss",
                        ),
                    )
                ],
            ),
            (datetime, None, 123, [ErrorFactory.datetime_parsing_error(Loc("foo"), 123)]),
            (
                datetime,
                FieldInfo(type_opts={"input_datetime_formats": ["YYYY-MM-DD"]}),
                "1999-01-31T10:11:22",
                [ErrorFactory.unsupported_datetime_format(Loc("foo"), "1999-01-31T10:11:22", ("YYYY-MM-DD",))],
            ),
            (date, None, 123, [ErrorFactory.date_parsing_error(Loc("foo"), 123)]),
            (
                date,
                FieldInfo(type_opts={"input_date_formats": ["DD-MM-YYYY"]}),
                "1999-01-01",
                [ErrorFactory.unsupported_date_format(Loc("foo"), "1999-01-01", ("DD-MM-YYYY",))],
            ),
            (EDummy, None, 123, [ErrorFactory.value_not_allowed(Loc("foo"), 123, (EDummy.ONE, EDummy.TWO))]),
            (Literal[1, 2, "foo"], None, "spam", [ErrorFactory.value_not_allowed(Loc("foo"), "spam", (1, 2, "foo"))]),
            (type(None), None, "spam", [ErrorFactory.value_not_allowed(Loc("foo"), "spam", (None,))]),
            (int, None, "invalid", [ErrorFactory.integer_parsing_error(Loc("foo"), "invalid")]),
            (float, None, "invalid", [ErrorFactory.float_parsing_error(Loc("foo"), "invalid")]),
            (str, None, 123, [ErrorFactory.string_value_required(Loc("foo"), 123)]),
            (bytes, None, 123, [ErrorFactory.bytes_value_required(Loc("foo"), 123)]),
            (Optional[int], None, "invalid", [ErrorFactory.integer_parsing_error(Loc("foo"), "invalid")]),
            (
                Union[int, str],
                None,
                {},
                [
                    ErrorFactory.union_parsing_error(Loc("foo"), {}, (int, str)),
                ],
            ),
        ],
    )
    def test_parsing_failed(self, model_class: type[Model], given_value, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            model_class(foo=given_value)
        assert excinfo.value.typ is model_class
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


class TestModelWithModelField:

    class SUT(Model):

        class Foo(Model):
            bar: int

        foo: Foo

    @pytest.fixture
    def sut(self):
        return self.SUT()

    @pytest.mark.parametrize(
        "args, expected_bar",
        [
            ({"foo": {}}, Unset),
            ({"foo": {"bar": "1"}}, 1),
            ({"foo": SUT.Foo()}, Unset),
            ({"foo": SUT.Foo(bar=2)}, 2),
        ],
    )
    def test_construct(self, args, expected_bar):
        uut = self.SUT(**args)
        assert uut.foo.bar == expected_bar

    @pytest.mark.parametrize(
        "given_foo, expected_bar",
        [
            ({}, Unset),
            ({"bar": "1"}, 1),
        ],
    )
    def test_assign_value_to_field(self, sut: SUT, given_foo, expected_bar):
        sut.foo = given_foo
        assert sut.foo.bar == expected_bar

    @pytest.mark.parametrize(
        "initial_foo, initial_bar, expected_errors",
        [
            ({}, "spam", [ErrorFactory.integer_parsing_error(Loc("bar"), "spam")]),
            (SUT.Foo(), "spam", [ErrorFactory.integer_parsing_error(Loc("bar"), "spam")]),
        ],
    )
    def test_when_assigning_incorrect_value_then_parsing_error_is_raised(
        self, sut: SUT, initial_foo, initial_bar, expected_errors
    ):
        sut.foo = initial_foo
        with pytest.raises(ParsingError) as excinfo:
            sut.foo.bar = initial_bar
        assert excinfo.value.typ is type(sut.foo)
        assert excinfo.value.errors == tuple(expected_errors)


class TestModelWithDictField:

    class SUT(Model):
        foo: dict[str, int]

    @pytest.fixture
    def sut(self, args):
        return self.SUT(**args)

    @pytest.mark.parametrize(
        "args, key, value, expected_value",
        [
            ({"foo": {}}, "one", "1", 1),
            ({"foo": {}}, "two", 2, 2),
        ],
    )
    def test_set_valid_item(self, sut: SUT, key, value, expected_value):
        sut.foo[key] = value
        assert sut.foo[key] == expected_value

    @pytest.mark.parametrize(
        "args, key, value, expected_errors",
        [({"foo": {}}, "one", "spam", [ErrorFactory.integer_parsing_error(Loc("one"), "spam")])],
    )
    def test_setting_item_to_invalid_value_causes_error(self, sut: SUT, key, value, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            sut.foo[key] = value
        assert excinfo.value.errors == tuple(expected_errors)

    def test_update_dict_successfully(self):
        sut = self.SUT(foo={"three": 3})
        sut.foo.update(one=1, two=2)
        assert sut.foo == {"one": 1, "two": 2, "three": 3}

    def test_setdefault_successfully(self):
        sut = self.SUT(foo={"one": 1})
        assert sut.foo.setdefault("one", 123) == 1
        assert sut.foo.setdefault("two", "2") == 2

    def test_setdefault_fails(self):
        sut = self.SUT(foo={})
        with pytest.raises(ParsingError) as excinfo:
            sut.foo.setdefault("one", "spam")
        assert excinfo.value.typ is self.SUT.__model_fields__["foo"].typ
        assert excinfo.value.errors == (ErrorFactory.integer_parsing_error(Loc("one"), "spam"),)


class TestModelWithListField:

    class SUT(Model):
        foo: list[int]

    @pytest.fixture
    def sut(self, initial):
        return self.SUT(foo=initial)

    @pytest.mark.parametrize(
        "initial, given, expected_result",
        [
            ([], "1", [1]),
            ([1, 2], "1", [1, 2, 1]),
        ],
    )
    def test_append_successfully(self, sut: SUT, given, expected_result):
        sut.foo.append(given)
        assert sut.foo == expected_result

    @pytest.mark.parametrize(
        "initial, given, expected_errors",
        [
            ([], "spam", [ErrorFactory.integer_parsing_error(Loc(0), "spam")]),
            ([1, 2, 3], "spam", [ErrorFactory.integer_parsing_error(Loc(3), "spam")]),
        ],
    )
    def test_append_failed(self, sut: SUT, given, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            sut.foo.append(given)
        assert excinfo.value.typ is self.SUT.__model_fields__["foo"].typ
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize(
        "initial, given, expected_result",
        [
            ([], "1", [1]),
            ([1, 2], "12", [1, 2, 1, 2]),
        ],
    )
    def test_extend_successfully(self, sut: SUT, given, expected_result):
        sut.foo.extend(given)
        assert sut.foo == expected_result


class TestModelWithModelPrevalidators:

    def test_invoke_model_prevalidator_without_args(self, mock):

        class SUT(Model):

            @model_prevalidator()
            def foo():
                mock.foo()

        sut = SUT()
        mock.foo.expect_call()
        with ordered(mock):
            validate(sut)

    def test_value_error_exception_is_converted_into_error(self, mock):

        class SUT(Model):

            @model_prevalidator()
            def foo():
                mock.foo()

        sut = SUT()
        mock.foo.expect_call().will_once(Raise(ValueError("an error")))
        with pytest.raises(ValidationError) as excinfo:
            validate(sut)
        assert excinfo.value.errors == (ErrorFactory.exception(Loc(), Unset, "an error", ValueError),)

    @pytest.mark.parametrize(
        "arg_name, expect_call_arg",
        [
            ("cls", "SUT"),
            ("self", "sut"),
            ("root", "sut"),
            ("ctx", "{1, 2, 3}"),
            ("errors", "[]"),
            ("loc", "Loc()"),
        ],
    )
    def test_invoke_model_prevalidator_with_single_arg(self, mock, arg_name, expect_call_arg):
        code = textwrap.dedent(
            f"""
        class SUT(Model):

            @model_prevalidator()
            def foo({arg_name}):
                mock.foo({arg_name})

        sut = SUT()
        mock.foo.expect_call({expect_call_arg})
        with ordered(mock):
            validate(sut, ctx=ctx)
        """
        )
        ctx = {1, 2, 3}
        g = dict(globals())
        g.update({"mock": mock, "ctx": ctx})
        exec(code, g)

    def test_invoke_nested_model_prevalidator_with_self_and_root_arguments(self, mock):

        class SUT(Model):

            class Nested(Model):
                @model_prevalidator()
                def foo(self, root):
                    mock.foo(self, root)

            nested: Nested

        sut = SUT(nested={})
        mock.foo.expect_call(sut.nested, sut)
        with ordered(mock):
            validate(sut)

    def test_invoke_model_prevalidator_with_all_params(self, mock):

        class SUT(Model):

            @model_prevalidator()
            def foo(cls, self, root, ctx, errors, loc):
                mock.foo(cls, self, root, ctx, errors, loc)

        sut = SUT()
        mock.foo.expect_call(SUT, sut, sut, None, [], Loc())
        with ordered(mock):
            validate(sut)

    def test_two_model_prevalidators_are_executed_in_declaration_order(self, mock):

        class SUT(Model):

            @model_prevalidator()
            def foo():
                mock.foo()

            @model_prevalidator()
            def bar():
                mock.bar()

        sut = SUT()
        mock.foo.expect_call()
        mock.bar.expect_call()
        with ordered(mock):
            validate(sut)

    def test_prevalidators_defined_in_base_model_are_also_executed_for_child_model(self, mock):

        class Base(Model):

            @model_prevalidator()
            def foo():
                mock.foo()

        class SUT(Base):

            @model_prevalidator()
            def bar():
                mock.bar()

        sut = SUT()
        mock.foo.expect_call()
        mock.bar.expect_call()
        with ordered(mock):
            validate(sut)

    def test_model_prevalidator_can_return_true_to_skip_other_validators_including_built_in_ones(self, mock):

        class SUT(Model):
            foo: int

            @model_prevalidator()
            def prevalidate_model():
                return mock.prevalidate_model()

        sut = SUT()
        mock.prevalidate_model.expect_call().will_once(Return(True))  # Disable other validators
        validate(sut)  # Will pass, as model prevalidator disabled built-in validation

    def test_model_prevalidator_can_be_provided_by_mixin(self, mock):
        class Mixin:

            @model_prevalidator()
            def _prevalidate_model():
                return mock.prevalidate_model()

        class SUT(Model, Mixin):
            foo: int

        sut = SUT()
        mock.prevalidate_model.expect_call().will_once(Return(True))
        validate(sut)


class TestModelWithModelPostvalidators:

    def test_invoke_model_postvalidator_without_args(self, mock):

        class SUT(Model):

            @model_postvalidator()
            def foo():
                mock.foo()

        sut = SUT()
        mock.foo.expect_call()
        with ordered(mock):
            validate(sut)

    def test_value_error_exception_is_converted_into_error(self, mock):

        class SUT(Model):

            @model_postvalidator()
            def foo():
                mock.foo()

        sut = SUT()
        mock.foo.expect_call().will_once(Raise(ValueError("an error")))
        with pytest.raises(ValidationError) as excinfo:
            validate(sut)
        assert excinfo.value.errors == (ErrorFactory.exception(Loc(), Unset, "an error", ValueError),)

    @pytest.mark.parametrize(
        "arg_name, expect_call_arg",
        [
            ("cls", "SUT"),
            ("self", "sut"),
            ("root", "sut"),
            ("ctx", "{1, 2, 3}"),
            ("errors", "[]"),
            ("loc", "Loc()"),
        ],
    )
    def test_invoke_model_postvalidator_with_single_arg(self, mock, arg_name, expect_call_arg):
        code = textwrap.dedent(
            f"""
        class SUT(Model):

            @model_postvalidator()
            def foo({arg_name}):
                mock.foo({arg_name})

        sut = SUT()
        mock.foo.expect_call({expect_call_arg})
        with ordered(mock):
            validate(sut, ctx=ctx)
        """
        )
        ctx = {1, 2, 3}
        g = dict(globals())
        g.update({"mock": mock, "ctx": ctx})
        exec(code, g)

    def test_invoke_nested_model_postvalidator_with_self_and_root_arguments(self, mock):

        class SUT(Model):

            class Nested(Model):
                @model_postvalidator()
                def foo(self, root):
                    mock.foo(self, root)

            nested: Nested

        sut = SUT(nested={})
        mock.foo.expect_call(sut.nested, sut)
        with ordered(mock):
            validate(sut)

    def test_invoke_model_postvalidator_with_all_params(self, mock):

        class SUT(Model):

            @model_postvalidator()
            def foo(cls, self, root, ctx, errors, loc):
                mock.foo(cls, self, root, ctx, errors, loc)

        sut = SUT()
        mock.foo.expect_call(SUT, sut, sut, None, [], Loc())
        with ordered(mock):
            validate(sut)

    def test_two_model_postvalidators_are_executed_in_declaration_order(self, mock):

        class SUT(Model):

            @model_postvalidator()
            def foo():
                mock.foo()

            @model_postvalidator()
            def bar():
                mock.bar()

        sut = SUT()
        mock.foo.expect_call()
        mock.bar.expect_call()
        with ordered(mock):
            validate(sut)

    def test_postvalidators_defined_in_base_model_are_also_executed_for_child_model(self, mock):

        class Base(Model):

            @model_postvalidator()
            def foo():
                mock.foo()

        class SUT(Base):

            @model_postvalidator()
            def bar():
                mock.bar()

        sut = SUT()
        mock.foo.expect_call()
        mock.bar.expect_call()
        with ordered(mock):
            validate(sut)

    def test_model_postvalidator_can_be_provided_by_mixin(self, mock):
        class Mixin:

            @model_postvalidator()
            def _postvalidate_model():
                mock.postvalidate_model()

        class SUT(Model, Mixin):
            foo: int

        sut = SUT(foo=123)
        mock.postvalidate_model.expect_call()
        validate(sut)


class TestModelWithFieldValidators:

    def test_declare_field_validator_without_args(self, mock):

        class SUT(Model):
            foo: int

            @field_validator("foo")
            def _validate_foo():
                mock.foo()

        sut = SUT(foo=1)
        mock.foo.expect_call()
        with ordered(mock):
            validate(sut)

    def test_value_error_exception_is_converted_into_error(self, mock):

        class SUT(Model):
            foo: int

            @field_validator("foo")
            def _validate_foo():
                mock.foo()

        sut = SUT(foo=1)
        mock.foo.expect_call().will_once(Raise(ValueError("an error")))
        with pytest.raises(ValidationError) as excinfo:
            validate(sut)
        assert excinfo.value.errors == (ErrorFactory.exception(Loc("foo"), 1, "an error", ValueError),)

    @pytest.mark.parametrize(
        "arg_name, expected_call_arg",
        [
            ("cls", "SUT"),
            ("self", "sut"),
            ("root", "sut"),
            ("ctx", "{1, 2, 3}"),
            ("errors", "[]"),
            ("loc", "Loc('foo')"),
            ("value", "123"),
        ],
    )
    def test_declare_field_validator_with_single_arg(self, mock, arg_name, expected_call_arg):
        code = textwrap.dedent(
            f"""
        class SUT(Model):
            foo: int

            @field_validator("foo")
            def _validate_foo({arg_name}):
                mock.foo({arg_name})

        sut = SUT(foo=123)
        assert sut.foo == 123
        mock.foo.expect_call({expected_call_arg})
        with ordered(mock):
            validate(sut, ctx=ctx)
        """
        )
        ctx = {1, 2, 3}
        g = dict(globals())
        g.update({"mock": mock, "ctx": ctx})
        exec(code, g)

    def test_declare_field_validator_with_all_args(self, mock):

        class SUT(Model):
            foo: int

            @field_validator("foo")
            def _validate_foo(cls, self, root, ctx, errors, loc, value):
                mock.foo(cls, self, root, ctx, errors, loc, value)

        ctx = object()
        sut = SUT(foo=123)
        mock.foo.expect_call(SUT, sut, sut, ctx, [], Loc("foo"), 123)
        with ordered(mock):
            validate(sut, ctx=ctx)

    def test_declare_field_validator_in_nested_model_with_self_and_root_args(self, mock):

        class SUT(Model):

            class Nested(Model):
                foo: int

                @field_validator("foo")
                def _validate_foo(self, root):
                    mock.foo(self, root)

            nested: Nested

        sut = SUT(nested={"foo": 123})
        mock.foo.expect_call(sut.nested, sut)
        with ordered(mock):
            validate(sut)

    def test_two_field_validators_are_executed_in_declaration_order(self, mock):

        class SUT(Model):
            foo: int

            @field_validator("foo")
            def _validate_foo():
                mock.foo()

            @field_validator("foo")
            def _validate_bar():
                mock.bar()

        sut = SUT(foo=123)
        mock.foo.expect_call()
        mock.bar.expect_call()
        with ordered(mock):
            validate(sut)

    def test_inherited_field_validators_are_executed_in_declaration_order(self, mock):

        class Base(Model):

            @field_validator()
            def _validate_foo():
                mock.foo()

        class SUT(Base):
            foo: int

            @field_validator("foo")
            def _validate_bar():
                mock.bar()

        sut = SUT(foo=123)
        mock.foo.expect_call()
        mock.bar.expect_call()
        with ordered(mock):
            validate(sut)

    def test_field_validator_declared_without_field_names_is_applied_to_all_fields(self, mock):

        class SUT(Model):
            foo: int
            bar: int

            @field_validator()
            def _validate_foo(loc, value):
                mock.foo(loc, value)

        sut = SUT(foo=123, bar=456)
        mock.foo.expect_call(Loc("foo"), 123)
        mock.foo.expect_call(Loc("bar"), 456)
        with ordered(mock):
            validate(sut)

    def test_field_validator_is_not_called_if_value_is_not_set(self, mock):

        class SUT(Model):
            foo: Optional[int]

            @field_validator("foo")
            def _validate_foo():
                mock.foo()

        sut = SUT()
        mock.foo.expect_call().times(0)
        with ordered(mock):
            validate(sut)

    def test_field_validator_can_be_provided_by_mixin(self, mock):
        class Mixin:

            @field_validator()
            def _validate_field(loc, value):
                mock.validate_field(loc, value)

        class SUT(Model, Mixin):
            foo: int

        sut = SUT(foo=123)
        mock.validate_field.expect_call(Loc("foo"), 123)
        validate(sut)


class TestModelWithPrePostAndFieldValidators:

    def test_first_invoke_model_prevalidator_then_field_validator_and_finally_model_postvalidator(self, mock):

        class SUT(Model):
            foo: Optional[int]

            @model_prevalidator()
            def _prevalidate(self):
                mock.prevalidate(self)

            @model_postvalidator()
            def _postvalidate(self):
                mock.postvalidate(self)

            @field_validator("foo")
            def _validate_foo(self, loc, value):
                mock.validate_foo(self, loc, value)

        sut = SUT()
        sut.foo = 123
        mock.prevalidate.expect_call(sut)
        mock.validate_foo.expect_call(sut, Loc("foo"), 123)
        mock.postvalidate.expect_call(sut)
        with ordered(mock):
            validate(sut)


class TestModelWithFieldPreprocessors:

    def test_declare_preprocessor_without_args(self, mock):

        class SUT(Model):
            foo: int

            @field_preprocessor("foo")
            def _preprocess():
                return mock.preprocess()

        sut = SUT()
        mock.preprocess.expect_call().will_once(Return("123"))
        sut.foo = 1
        assert sut.foo == 123

    @pytest.mark.parametrize(
        "arg_name, expect_call_arg, given_foo, mock_return, expected_foo",
        [
            ("cls", "SUT", 1, "123", 123),
            ("errors", "[]", 1, "123", 123),
            ("loc", "Loc('foo')", 1, "123", 123),
            ("value", 1, 1, "123", 123),
            ("value", 2, 2, "2", 2),
        ],
    )
    def test_declare_preprocessor_with_single_arg(
        self, mock, arg_name, expect_call_arg, given_foo, mock_return, expected_foo
    ):
        code = textwrap.dedent(
            f"""
        class SUT(Model):
            foo: int

            @field_preprocessor("foo")
            def _preprocess({arg_name}):
                return mock.preprocess({arg_name})

        sut = SUT()
        mock.preprocess.expect_call({expect_call_arg}).will_once(Return({mock_return!r}))
        sut.foo = {given_foo!r}
        assert sut.foo == {expected_foo!r}
        """
        )
        g = globals()
        g.update({"mock": mock})
        exec(code, g)

    def test_preprocessor_declared_without_field_names_is_executed_for_all_fields(self, mock):

        class SUT(Model):
            foo: int
            bar: int

            @field_preprocessor()
            def _preprocess(loc, value):
                return mock.foo(loc, value)

        mock.foo.expect_call(Loc("foo"), 1).will_once(Return(1))
        mock.foo.expect_call(Loc("bar"), 2).will_once(Return(2))
        with ordered(mock):
            sut = SUT(foo=1, bar=2)
            assert sut.foo == 1
            assert sut.bar == 2

    def test_two_preprocessors_are_chained_in_declaration_order(self, mock):

        class SUT(Model):
            foo: int

            @field_preprocessor("foo")
            def _first(value):
                return mock.first(value)

            @field_preprocessor("foo")
            def _second(value):
                return mock.second(value)

        mock.first.expect_call(1).will_once(Return(12))
        mock.second.expect_call(12).will_once(Return(123))
        with ordered(mock):
            sut = SUT(foo=1)
            assert sut.foo == 123

    def test_inherited_preprocessors_are_chained_in_declaration_order(self, mock):

        class Base(Model):

            @field_preprocessor()
            def _first(value):
                return mock.first(value)

        class SUT(Base):
            foo: int

            @field_preprocessor("foo")
            def _second(value):
                return mock.second(value)

        mock.first.expect_call(1).will_once(Return(12))
        mock.second.expect_call(12).will_once(Return(123))
        with ordered(mock):
            sut = SUT(foo=1)
            assert sut.foo == 123

    def test_when_preprocessor_throws_type_error_then_it_is_converted_to_error(self, mock):

        class SUT(Model):
            foo: int

            @field_preprocessor("foo")
            def _preprocess_foo(value):
                return mock.preprocess_foo(value)

        mock.preprocess_foo.expect_call(123).will_once(Raise(TypeError("an error")))
        sut = SUT()
        with pytest.raises(ParsingError) as excinfo:
            sut.foo = 123
        assert excinfo.value.typ is SUT
        assert excinfo.value.errors == (ErrorFactory.exception(Loc("foo"), 123, "an error", TypeError),)

    def test_field_preprocessor_can_be_provided_by_mixin(self, mock):
        class Mixin:

            @field_preprocessor()
            def _preprocess_field(loc, value):
                return mock.preprocess_field(loc, value)

        class SUT(Model, Mixin):
            foo: int

        mock.preprocess_field.expect_call(Loc("foo"), "123").will_once(Return("456"))
        sut = SUT(foo="123")
        assert sut.foo == 456


class TestModelWithFieldPostprocessors:

    def test_declare_preprocessor_without_args(self, mock):

        class SUT(Model):
            foo: int

            @field_postprocessor("foo")
            def _postprocess_foo(value):
                return mock.postprocess_foo(value)

        sut = SUT()
        mock.postprocess_foo.expect_call(1).will_once(Return(12))
        sut.foo = "1"
        assert sut.foo == 12

    @pytest.mark.parametrize(
        "arg_name, expect_call_arg, given_foo, mock_return",
        [
            ("cls", "SUT", 1, 123),
            ("self", "sut", 1, 123),
            ("errors", "[]", 1, 123),
            ("loc", "Loc('foo')", 1, 123),
            ("value", 1, 1, 123),
            ("value", 2, 2, 2),
        ],
    )
    def test_declare_postprocessor_with_single_arg(self, mock, arg_name, expect_call_arg, given_foo, mock_return):
        code = textwrap.dedent(
            f"""
        class SUT(Model):
            foo: int

            @field_postprocessor("foo")
            def _postprocess_foo({arg_name}):
                return mock.postprocess_foo({arg_name})

        sut = SUT()
        mock.postprocess_foo.expect_call({expect_call_arg}).will_once(Return({mock_return!r}))
        sut.foo = {given_foo!r}
        assert sut.foo == {mock_return!r}
        """
        )
        g = globals()
        g.update({"mock": mock})
        exec(code, g)

    def test_postprocessor_declared_without_field_names_is_executed_for_all_fields(self, mock):

        class SUT(Model):
            foo: int
            bar: int

            @field_postprocessor()
            def _postprocess(loc, value):
                return mock.foo(loc, value)

        mock.foo.expect_call(Loc("foo"), 1).will_once(Return(1))
        mock.foo.expect_call(Loc("bar"), 2).will_once(Return(2))
        with ordered(mock):
            sut = SUT(foo=1, bar=2)
            assert sut.foo == 1
            assert sut.bar == 2

    def test_two_postprocessors_are_chained_in_declaration_order(self, mock):

        class SUT(Model):
            foo: int

            @field_postprocessor("foo")
            def _first(value):
                return mock.first(value)

            @field_postprocessor("foo")
            def _second(value):
                return mock.second(value)

        mock.first.expect_call(1).will_once(Return(12))
        mock.second.expect_call(12).will_once(Return(123))
        with ordered(mock):
            sut = SUT(foo=1)
            assert sut.foo == 123

    def test_inherited_postprocessors_are_chained_in_declaration_order(self, mock):

        class Base(Model):

            @field_postprocessor()
            def _first(value):
                return mock.first(value)

        class SUT(Base):
            foo: int

            @field_postprocessor("foo")
            def _second(value):
                return mock.second(value)

        mock.first.expect_call(1).will_once(Return(12))
        mock.second.expect_call(12).will_once(Return(123))
        with ordered(mock):
            sut = SUT(foo=1)
            assert sut.foo == 123

    def test_when_postprocessor_throws_type_error_then_it_is_converted_to_error(self, mock):

        class SUT(Model):
            foo: int

            @field_postprocessor("foo")
            def _postprocess_foo(value):
                return mock.postprocess_foo(value)

        mock.postprocess_foo.expect_call(123).will_once(Raise(TypeError("an error")))
        sut = SUT()
        with pytest.raises(ParsingError) as excinfo:
            sut.foo = 123
        assert excinfo.value.typ is SUT
        assert excinfo.value.errors == (ErrorFactory.exception(Loc("foo"), 123, "an error", TypeError),)

    def test_field_postprocessor_can_be_provided_by_mixin(self, mock):
        class Mixin:

            @field_postprocessor()
            def _postprocess_field(loc, value):
                return mock.postprocess_field(loc, value)

        class SUT(Model, Mixin):
            foo: int

        mock.postprocess_field.expect_call(Loc("foo"), 123).will_once(Return(456))
        sut = SUT(foo="123")
        assert sut.foo == 456
