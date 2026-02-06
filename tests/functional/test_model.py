from datetime import date, datetime, timezone
from enum import Enum
from typing import Annotated, Any, Literal, Mapping, Optional, Sequence, Set, Union

import pytest

from mockify.api import Mock, ordered, satisfied

from modelity.constraints import Ge, Gt, Le, LenRange, Lt, MinLen, MaxLen, Range, Regex
from modelity.error import ErrorFactory
from modelity.exc import ParsingError, ParsingError, UnsupportedTypeError, ValidationError
from modelity.interface import ITypeDescriptor
from modelity.loc import Loc
from modelity.model import FieldInfo, Model
from modelity.hooks import (
    field_validator,
    model_postvalidator,
    model_prevalidator,
)
from modelity.types import StrictOptional
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


def test_exception_is_raised_if_model_is_created_with_unsupported_type():
    with pytest.raises(UnsupportedTypeError) as excinfo:

        class Dummy(Model):
            foo: object

    assert excinfo.value.typ is object


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
            (Annotated[float, Range(Gt(0), Le(1))], None, "0.111", 0.111),
            (Annotated[str, MinLen(1), MaxLen(3)], None, "a", "a"),
            (Annotated[str, MinLen(1), MaxLen(3)], None, "foo", "foo"),
            (Annotated[str, LenRange(3, 4)], None, "foo", "foo"),
            (Annotated[str, LenRange(3, 4)], None, "spam", "spam"),
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
            (Annotated[float, Ge(0.0)], None, "-0.1", [ErrorFactory.out_of_range(Loc("foo"), -0.1, min_inclusive=0.0)]),
            (Annotated[float, Gt(0.0)], None, 0.0, [ErrorFactory.out_of_range(Loc("foo"), 0.0, min_exclusive=0.0)]),
            (Annotated[float, Le(1.0)], None, 1.1, [ErrorFactory.out_of_range(Loc("foo"), 1.1, max_inclusive=1.0)]),
            (Annotated[float, Lt(1.0)], None, 1.0, [ErrorFactory.out_of_range(Loc("foo"), 1.0, max_exclusive=1.0)]),
            (
                Annotated[float, Range(Ge(0), Le(1))],
                None,
                2.0,
                [ErrorFactory.out_of_range(Loc("foo"), 2.0, min_inclusive=0, max_inclusive=1)],
            ),
            (
                Annotated[float, Range(Ge(0), Lt(1))],
                None,
                1.0,
                [ErrorFactory.out_of_range(Loc("foo"), 1.0, min_inclusive=0, max_exclusive=1)],
            ),
            (
                Annotated[float, Range(Gt(0), Le(1))],
                None,
                0,
                [ErrorFactory.out_of_range(Loc("foo"), 0, min_exclusive=0, max_inclusive=1)],
            ),
            (
                Annotated[float, Range(Gt(0), Lt(1))],
                None,
                1,
                [ErrorFactory.out_of_range(Loc("foo"), 1, min_exclusive=0, max_exclusive=1)],
            ),
            (Annotated[str, MinLen(1)], None, "", [ErrorFactory.invalid_length(Loc("foo"), "", min_length=1)]),
            (Annotated[str, MaxLen(3)], None, "spam", [ErrorFactory.invalid_length(Loc("foo"), "spam", max_length=3)]),
            (
                Annotated[str, LenRange(3, 4)],
                None,
                "dummy",
                [ErrorFactory.invalid_length(Loc("foo"), "dummy", min_length=3, max_length=4)],
            ),
            (
                Annotated[str, LenRange(3, 4)],
                None,
                "ab",
                [ErrorFactory.invalid_length(Loc("foo"), "ab", min_length=3, max_length=4)],
            ),
            (
                Annotated[str, Regex(r"^[0-9]+$")],
                None,
                "spam",
                [ErrorFactory.invalid_string_format(Loc("foo"), "spam", r"^[0-9]+$")],
            ),
            (
                Annotated[datetime, Ge(datetime(2020, 1, 1))],
                FieldInfo(type_opts={"input_datetime_formats": ["YYYY-MM-DD"]}),
                "2019-12-31",
                [ErrorFactory.out_of_range(Loc("foo"), datetime(2019, 12, 31), min_inclusive=datetime(2020, 1, 1))],
            ),
            (dict, None, 123, [ErrorFactory.invalid_type(Loc("foo"), 123, [dict], [Mapping])]),
            (dict[str, int], None, {1: 1}, [ErrorFactory.invalid_type(Loc("foo", "_"), 1, [str])]),
            (
                dict[str, int],
                None,
                {"one": "invalid"},
                [ErrorFactory.parse_error(Loc("foo", "one"), "invalid", int)],
            ),
            (int, None, "spam", [ErrorFactory.parse_error(Loc("foo"), "spam", int)]),
            (
                list,
                None,
                "spam",
                [ErrorFactory.invalid_type(Loc("foo"), "spam", [list], [Sequence], [str, bytes])],
            ),
            (list[int], None, [1, 2, "invalid"], [ErrorFactory.parse_error(Loc("foo", 2), "invalid", int)]),
            (set, None, 123, [ErrorFactory.invalid_type(Loc("foo"), 123, [set], [Set, Sequence], [str, bytes])]),
            (set[int], None, 123, [ErrorFactory.invalid_type(Loc("foo"), 123, [set], [Set, Sequence], [str, bytes])]),
            (
                set[int],
                None,
                [1, 2, "three", 4, "five"],
                [
                    ErrorFactory.parse_error(Loc("foo") + Loc.irrelevant(), "three", int),
                    ErrorFactory.parse_error(Loc("foo") + Loc.irrelevant(), "five", int),
                ],
            ),
            (tuple, None, 123, [ErrorFactory.invalid_type(Loc("foo"), 123, [tuple], [Sequence], [str, bytes])]),
            (tuple[int, ...], None, [1, 2, "three"], [ErrorFactory.parse_error(Loc("foo", 2), "three", int)]),
            (
                tuple[int, float],
                None,
                [1, 2.71, "spam"],
                [ErrorFactory.invalid_tuple_length(Loc("foo"), [1, 2.71, "spam"], (int, float))],
            ),
            (tuple[int, float], None, [1], [ErrorFactory.invalid_tuple_length(Loc("foo"), [1], (int, float))]),
            (Nested, None, 123, [ErrorFactory.invalid_type(Loc("foo"), 123, [Nested], [Mapping])]),
            (Nested, None, {"bar": "invalid"}, [ErrorFactory.parse_error(Loc("foo", "bar"), "invalid", int)]),
            (bool, None, "foo", [ErrorFactory.parse_error(Loc("foo"), "foo", bool)]),
            (
                bool,
                FieldInfo(type_opts={"true_literals": ["on"]}),
                "foo",
                [ErrorFactory.parse_error(Loc("foo"), "foo", bool, true_literals=["on"])],
            ),
            (
                bool,
                FieldInfo(type_opts={"false_literals": ["off"]}),
                "foo",
                [ErrorFactory.parse_error(Loc("foo"), "foo", bool, false_literals=["off"])],
            ),
            (
                bool,
                FieldInfo(type_opts={"true_literals": ["on"], "false_literals": ["off"]}),
                "foo",
                [ErrorFactory.parse_error(Loc("foo"), "foo", bool, true_literals=["on"], false_literals=["off"])],
            ),
            (
                datetime,
                None,
                "spam",
                [
                    ErrorFactory.invalid_datetime_format(
                        Loc("foo"),
                        "spam",
                        expected_formats=[
                            "YYYY-MM-DDThh:mm:ssZZZZ",
                            "YYYY-MM-DDThh:mm:ss",
                            "YYYY-MM-DD hh:mm:ssZZZZ",
                            "YYYY-MM-DD hh:mm:ss ZZZZ",
                            "YYYY-MM-DD hh:mm:ss",
                            "YYYYMMDDThhmmssZZZZ",
                            "YYYYMMDDThhmmss",
                            "YYYYMMDDhhmmssZZZZ",
                            "YYYYMMDDhhmmss",
                        ],
                    )
                ],
            ),
            (datetime, None, 123, [ErrorFactory.invalid_type(Loc("foo"), 123, [datetime, str])]),
            (
                datetime,
                FieldInfo(type_opts={"input_datetime_formats": ["YYYY-MM-DD"]}),
                "1999-01-31T10:11:22",
                [ErrorFactory.invalid_datetime_format(Loc("foo"), "1999-01-31T10:11:22", ["YYYY-MM-DD"])],
            ),
            (date, None, 123, [ErrorFactory.invalid_type(Loc("foo"), 123, [date, str])]),
            (
                date,
                FieldInfo(type_opts={"input_date_formats": ["DD-MM-YYYY"]}),
                "1999-01-01",
                [ErrorFactory.invalid_date_format(Loc("foo"), "1999-01-01", ["DD-MM-YYYY"])],
            ),
            (EDummy, None, 123, [ErrorFactory.invalid_enum_value(Loc("foo"), 123, EDummy)]),
            (Literal[1, 2, "foo"], None, "spam", [ErrorFactory.invalid_value(Loc("foo"), "spam", [1, 2, "foo"])]),
            (type(None), None, "spam", [ErrorFactory.invalid_value(Loc("foo"), "spam", [None])]),
            (int, None, "invalid", [ErrorFactory.parse_error(Loc("foo"), "invalid", int)]),
            (float, None, "invalid", [ErrorFactory.parse_error(Loc("foo"), "invalid", float)]),
            (str, None, 123, [ErrorFactory.invalid_type(Loc("foo"), 123, [str])]),
            (bytes, None, 123, [ErrorFactory.invalid_type(Loc("foo"), 123, [bytes])]),
            (Optional[int], None, "invalid", [ErrorFactory.parse_error(Loc("foo"), "invalid", int)]),
            (StrictOptional[int], None, "invalid", [ErrorFactory.parse_error(Loc("foo"), "invalid", int)]),
            (StrictOptional[int], None, None, [ErrorFactory.none_not_allowed(Loc("foo"), StrictOptional[int])]),
            (
                Union[int, str],
                None,
                {},
                [
                    ErrorFactory.invalid_type(Loc("foo"), {}, [int, str]),
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
                {"foo": "1999-01-31T10:11:22.000000+0000"},
            ),
            # TODO: Remove output_datetime_format
            #             (
            #                 datetime,
            #                 FieldInfo(type_opts={"output_datetime_format": "YYYY-MM-DD"}),
            #                 datetime(1999, 1, 31, 10, 11, 22, tzinfo=timezone.utc),
            #                 {"foo": "1999-01-31"},
            #             ),
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
                [ErrorFactory.invalid_length(Loc("foo"), [], min_length=1)],
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
            ({}, "spam", [ErrorFactory.parse_error(Loc("bar"), "spam", int)]),
            (SUT.Foo(), "spam", [ErrorFactory.parse_error(Loc("bar"), "spam", int)]),
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
        [({"foo": {}}, "one", "spam", [ErrorFactory.parse_error(Loc("one"), "spam", int)])],
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
        assert excinfo.value.errors == (ErrorFactory.parse_error(Loc("one"), "spam", int),)


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
            ([], "spam", [ErrorFactory.parse_error(Loc(0), "spam", int)]),
            ([1, 2, 3], "spam", [ErrorFactory.parse_error(Loc(3), "spam", int)]),
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
