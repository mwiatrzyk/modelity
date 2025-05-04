from datetime import date, datetime, timedelta, timezone
from enum import Enum
from ipaddress import IPv4Address, IPv6Address
from typing import Annotated, Any, Literal, Optional, Union

from modelity.constraints import Ge, Gt, Le, Lt, MaxLen, MinLen, Regex
from modelity.error import ErrorFactory
from modelity.exc import ParsingError, ValidationError
from modelity.interface import DISCARD
from modelity.loc import Loc
from modelity.model import FieldInfo, Model, dump, make_type_descriptor, validate
from modelity.unset import Unset

import pytest

loc = Loc("foo")


@pytest.fixture
def type_opts():
    return {}


@pytest.fixture
def model_type(typ, type_opts):
    if type_opts:

        class Dummy(Model):
            foo: typ = FieldInfo(type_opts=type_opts)

    else:

        class Dummy(Model):
            foo: typ

    return Dummy


@pytest.fixture
def model(model_type, input_value):
    return model_type(foo=input_value)


@pytest.mark.parametrize("typ", [IPv4Address])
class TestIPv4:

    @pytest.mark.parametrize(
        "input_value, output_value",
        [
            (IPv4Address("192.168.0.1"), IPv4Address("192.168.0.1")),
            ("192.168.0.1", IPv4Address("192.168.0.1")),
        ],
    )
    def test_successful_parsing(self, model, output_value):
        assert model.foo == output_value

    @pytest.mark.parametrize(
        "input_value, expected_errors",
        [
            (
                None,
                [
                    ErrorFactory.parsing_error(
                        Loc("foo"),
                        None,
                        "not a valid IPv4 address",
                        IPv4Address,
                    )
                ],
            ),
        ],
    )
    def test_parse_with_error(self, model_type, input_value, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            model_type(foo=input_value)
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize(
        "input_value, output_value",
        [
            ("1.1.1.1", {"foo": "1.1.1.1"}),
        ],
    )
    def test_dump(self, model, output_value):
        assert dump(model) == output_value

    @pytest.mark.parametrize("input_value", ["1.1.1.2"])
    def test_validate_successfully(self, model):
        validate(model)


@pytest.mark.parametrize("typ", [IPv6Address])
class TestIPv6:

    @pytest.mark.parametrize(
        "input_value, output_value",
        [
            (IPv6Address("ffff::0001"), IPv6Address("ffff::0001")),
            ("ffff::0002", IPv6Address("ffff::0002")),
        ],
    )
    def test_successful_parsing(self, model, output_value):
        assert model.foo == output_value

    @pytest.mark.parametrize(
        "input_value, expected_errors",
        [
            (
                None,
                [
                    ErrorFactory.parsing_error(
                        Loc("foo"),
                        None,
                        "not a valid IPv6 address",
                        IPv6Address,
                    )
                ],
            ),
        ],
    )
    def test_failed_parsing(self, model_type, input_value, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            model_type(foo=input_value)
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize(
        "input_value, output_value",
        [
            ("ffff::0001", {"foo": "ffff::1"}),
        ],
    )
    def test_dump(self, model, output_value):
        assert dump(model) == output_value

    @pytest.mark.parametrize("input_value", ["ffff::1"])
    def test_validate_successfully(self, model):
        validate(model)

# TODO: add tests for dump and validate for the rest

@pytest.mark.parametrize("typ", [Any])
class TestAnyTypeDescriptor:

    @pytest.mark.parametrize(
        "input_value",
        [
            1,
            3.14,
            "foo",
            [],
            {},
            set(),
            tuple(),
        ],
    )
    def test_parse_successfully(self, model, input_value):
        assert model.foo == input_value

    @pytest.mark.parametrize("input_value, expected_output", [
        (1, {"foo": 1}),
        (3.14, {"foo": 3.14}),
        ("spam", {"foo": "spam"}),
    ])
    def test_dump(self, model, expected_output):
        assert dump(model) == expected_output

    @pytest.mark.parametrize("input_value", [1, 3.14, "spam"])
    def test_validate_successfully(self, model):
        validate(model)


@pytest.mark.parametrize("typ", [bool])
class TestBoolTypeDescriptor:

    @pytest.fixture
    def true_literals(self):
        return None

    @pytest.fixture
    def false_literals(self):
        return None

    @pytest.fixture
    def type_opts(self, true_literals, false_literals):
        return {"true_literals": true_literals, "false_literals": false_literals}

    @pytest.mark.parametrize(
        "true_literals, false_literals, input_value, output_value",
        [
            (None, None, True, True),
            (None, None, False, False),
            (["y"], ["n"], "y", True),
            (["y"], ["n"], "n", False),
        ],
    )
    def test_parse_successfully(self, model, output_value):
        assert model.foo == output_value

    @pytest.mark.parametrize(
        "true_literals, false_literals, input_value, expected_errors",
        [
            (None, None, 3.14, [ErrorFactory.invalid_bool(loc, 3.14)]),
            (["y"], None, "Y", [ErrorFactory.invalid_bool(loc, "Y", true_literals=set(["y"]))]),
            (None, ["n"], "N", [ErrorFactory.invalid_bool(loc, "N", false_literals=set(["n"]))]),
            (
                ["y"],
                ["n"],
                "N",
                [ErrorFactory.invalid_bool(loc, "N", true_literals=set(["y"]), false_literals=set(["n"]))],
            ),
        ],
    )
    def test_parse_expecting_parsing_error(self, model_type, input_value, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            model_type(foo=input_value)
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize("true_literals, false_literals, input_value, expected_output", [
        (['y'], None, 'y', {"foo": True}),
        (None, ['n'], 'n', {"foo": False}),
        (None, None, True, {"foo": True}),
        (None, None, False, {"foo": False}),
    ])
    def test_dump(self, model, expected_output):
        assert dump(model) == expected_output

    @pytest.mark.parametrize("input_value", [True, False])
    def test_validate_successfully(self, model):
        validate(model)


@pytest.mark.parametrize("typ", [datetime])
class TestDateTimeTypeDescriptor:

    @pytest.fixture
    def input_datetime_formats(self):
        return None

    @pytest.fixture
    def output_datetime_format(self):
        return None

    @pytest.fixture
    def type_opts(self, input_datetime_formats, output_datetime_format):
        return {"input_datetime_formats": input_datetime_formats, "output_datetime_format": output_datetime_format}

    @pytest.mark.parametrize(
        "input_datetime_formats, input_value, output_value",
        [
            (None, datetime(2025, 2, 22, 10, 11, 22), datetime(2025, 2, 22, 10, 11, 22)),
            (None, "2025-02-22T10:11:22", datetime(2025, 2, 22, 10, 11, 22)),
            (None, "2025-02-22T10:11:22+00:00", datetime(2025, 2, 22, 10, 11, 22, tzinfo=timezone.utc)),
            (
                None,
                "2025-02-22T10:11:22+02:00",
                datetime(2025, 2, 22, 10, 11, 22, tzinfo=timezone(timedelta(seconds=7200))),
            ),
            (None, "20250222101122", datetime(2025, 2, 22, 10, 11, 22)),
            (None, "20250222T101122", datetime(2025, 2, 22, 10, 11, 22)),
            (None, "20250222101122+0000", datetime(2025, 2, 22, 10, 11, 22, tzinfo=timezone.utc)),
            (None, "20250222T101122+0000", datetime(2025, 2, 22, 10, 11, 22, tzinfo=timezone.utc)),
            (
                None,
                "20250222101122+0200",
                datetime(2025, 2, 22, 10, 11, 22, tzinfo=timezone(timedelta(seconds=7200))),
            ),
            (["DD-MM-YYYY"], "22-02-2025", datetime(2025, 2, 22)),
        ],
    )
    def test_parse_successfully(self, model, output_value):
        assert model.foo == output_value

    @pytest.mark.parametrize(
        "input_datetime_formats, input_value, expected_errors",
        [
            (None, 123, [ErrorFactory.invalid_datetime(loc, 123)]),
            (["YYYY-MM-DD"], "spam", [ErrorFactory.unsupported_datetime_format(loc, "spam", ["YYYY-MM-DD"])]),
        ],
    )
    def test_parse_expecting_parsing_error(self, model_type, input_value, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            model_type(foo=input_value)
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize("output_datetime_format, input_value, output_value", [
        (None, "2024-01-31 11:22:33", {"foo": "2024-01-31T11:22:33"}),
        ("YYYY-MM-DD", "2024-01-31 11:22:33", {"foo": "2024-01-31"}),
    ])
    def test_dump(self, model, output_value):
        assert dump(model) == output_value

    @pytest.mark.parametrize("input_value", ["2024-01-31 11:22:33"])
    def test_validate_successfully(self, model):
        validate(model)


@pytest.mark.parametrize("typ", [date])
class TestDateTypeDescriptor:

    @pytest.fixture
    def input_date_formats(self):
        return None

    @pytest.fixture
    def output_date_format(self):
        return None

    @pytest.fixture
    def type_opts(self, input_date_formats, output_date_format):
        return {"input_date_formats": input_date_formats, "output_date_format": output_date_format}

    @pytest.mark.parametrize(
        "input_date_formats, input_value, output_value",
        [
            (None, date(2025, 2, 22), date(2025, 2, 22)),
            (None, "2025-02-22", date(2025, 2, 22)),
            (["DD-MM-YYYY"], "22-02-2025", date(2025, 2, 22)),
        ],
    )
    def test_parse_successfully(self, model, output_value):
        assert model.foo == output_value

    @pytest.mark.parametrize(
        "input_date_formats, input_value, expected_errors",
        [
            (None, 123, [ErrorFactory.invalid_date(loc, 123)]),
            (["YYYY-MM-DD"], "spam", [ErrorFactory.unsupported_date_format(loc, "spam", ["YYYY-MM-DD"])]),
        ],
    )
    def test_parse_expecting_parsing_error(self, model_type, input_value, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            model_type(foo=input_value)
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize("output_date_format, input_value, output_value", [
        (None, "2024-01-31", {"foo": "2024-01-31"}),
        ("DD-MM-YYYY", "2024-01-31", {"foo": "31-01-2024"}),
    ])
    def test_dump(self, model, output_value):
        assert dump(model) == output_value

    @pytest.mark.parametrize("input_value", ["2024-01-31"])
    def test_validate_successfully(self, model):
        validate(model)


class Dummy(Enum):
    FOO = 1
    BAR = 2
    BAZ = 3


@pytest.mark.parametrize("typ", [Dummy])
class TestEnumTypeDescriptor:

    @pytest.mark.parametrize(
        "input_value, output_value",
        [
            (Dummy.FOO, Dummy.FOO),
            (Dummy.BAR, Dummy.BAR),
            (Dummy.BAZ, Dummy.BAZ),
            (1, Dummy.FOO),
            (2, Dummy.BAR),
            (3, Dummy.BAZ),
        ],
    )
    def test_parse_successfully(self, model, output_value):
        assert model.foo == output_value

    @pytest.mark.parametrize("input_value, expected_errors", [
        (4, [ErrorFactory.value_out_of_range(loc, 4, (Dummy.FOO, Dummy.BAR, Dummy.BAZ))]),
    ])
    def test_parse_expecting_parsing_errors(self, model_type, input_value, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            model_type(foo=input_value)
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize("input_value, output_value", [
        (Dummy.FOO, {"foo": Dummy.FOO.value}),
        (Dummy.BAR, {"foo": Dummy.BAR.value}),
        (Dummy.BAZ, {"foo": Dummy.BAZ.value}),
    ])
    def test_dump(self, model, output_value):
        assert dump(model) == output_value

    @pytest.mark.parametrize("input_value", [Dummy.FOO])
    def test_validate_successfully(self, model):
        validate(model)


@pytest.mark.parametrize("typ", [Literal[1, 3.14, "spam"]])
class TestLiteralTypeDescriptor:

    @pytest.mark.parametrize(
        "input_value, output_value",
        [
            (1, 1),
            (3.14, 3.14),
            ("spam", "spam"),
        ],
    )
    def test_parse_successfully(self, model, output_value):
        assert model.foo == output_value

    @pytest.mark.parametrize("input_value, expected_errors", [
        ("1", [ErrorFactory.value_out_of_range(loc, "1", (1, 3.14, "spam"))]),
    ])
    def test_parse_expecting_parsing_errors(self, model_type, input_value, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            model_type(foo=input_value)
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize("input_value, output_value", [
        (1, {"foo": 1}),
        (3.14, {"foo": 3.14}),
        ("spam", {"foo": "spam"}),
    ])
    def test_dump(self, model, output_value):
        assert dump(model) == output_value

    @pytest.mark.parametrize("input_value", [1, 3.14, "spam"])
    def test_validate_successfully(self, model):
        validate(model)


@pytest.mark.parametrize("typ", [type(None)])
class TestNoneTypeDescriptor:

    @pytest.mark.parametrize(
        "input_value, output_value",
        [
            (None, None),
        ],
    )
    def test_parse_successfully(self, model, output_value):
        assert model.foo == output_value

    @pytest.mark.parametrize("input_value, expected_errors", [
        ("spam", [ErrorFactory.value_out_of_range(loc, "spam", (None,))]),
    ])
    def test_parse_expecting_parsing_errors(self, model_type, input_value, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            model_type(foo=input_value)
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize("input_value, output_value", [
        (None, {"foo": None}),
    ])
    def test_dump(self, model, output_value):
        assert dump(model) == output_value

    @pytest.mark.parametrize("input_value", [None])
    def test_validate_successfully(self, model):
        validate(model)


@pytest.mark.parametrize("typ", [int])
class TestIntegerTypeDescriptor:

    @pytest.mark.parametrize(
        "input_value, output_value",
        [
            (1, 1),
            ("2", 2),
        ],
    )
    def test_parse_successfully(self, model, output_value):
        assert model.foo == output_value

    @pytest.mark.parametrize("input_value, expected_errors", [
        ("spam", [ErrorFactory.invalid_integer(loc, "spam")]),
        (None, [ErrorFactory.invalid_integer(loc, None)]),
    ])
    def test_parse_expecting_parsing_errors(self, model_type, input_value, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            model_type(foo=input_value)
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize("input_value, output_value", [
        (123, {"foo": 123}),
    ])
    def test_dump(self, model, output_value):
        assert dump(model) == output_value

    @pytest.mark.parametrize("input_value", [123])
    def test_validate_successfully(self, model):
        validate(model)


@pytest.mark.parametrize("typ", [float])
class TestFloatTypeDescriptor:

    @pytest.mark.parametrize(
        "input_value, output_value",
        [
            (1, 1),
            ("2", 2),
            ("3.14", 3.14),
        ],
    )
    def test_parse_successfully(self, model, output_value):
        assert model.foo == output_value

    @pytest.mark.parametrize("input_value, expected_errors", [
        ("spam", [ErrorFactory.invalid_float(loc, "spam")]),
        (None, [ErrorFactory.invalid_float(loc, None)]),
    ])
    def test_parse_expecting_parsing_errors(self, model_type, input_value, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            model_type(foo=input_value)
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize("input_value, output_value", [
        (3.14, {"foo": 3.14}),
    ])
    def test_dump(self, model, output_value):
        assert dump(model) == output_value

    @pytest.mark.parametrize("input_value", [3.14])
    def test_validate_successfully(self, model):
        validate(model)


@pytest.mark.parametrize("typ", [str])
class TestStrTypeDescriptor:

    @pytest.mark.parametrize(
        "input_value, output_value",
        [
            ("spam", "spam"),
        ],
    )
    def test_parse_successfully(self, model, output_value):
        assert model.foo == output_value

    @pytest.mark.parametrize("input_value, expected_errors", [
        (123, [ErrorFactory.string_value_required(loc, 123)]),
    ])
    def test_parse_expecting_parsing_errors(self, model_type, input_value, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            model_type(foo=input_value)
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize("input_value, output_value", [
        ("spam", {"foo": "spam"}),
    ])
    def test_dump(self, model, output_value):
        assert dump(model) == output_value

    @pytest.mark.parametrize("input_value", ["spam"])
    def test_validate_successfully(self, model):
        validate(model)


@pytest.mark.parametrize("typ", [bytes])
class TestBytesTypeDescriptor:

    @pytest.mark.parametrize(
        "input_value, output_value",
        [
            (b"more spam", b"more spam"),
        ],
    )
    def test_parse_successfully(self, model, output_value):
        assert model.foo == output_value

    @pytest.mark.parametrize("input_value, expected_errors", [
        (123, [ErrorFactory.bytes_value_required(loc, 123)]),
    ])
    def test_parse_expecting_parsing_errors(self, model_type, input_value, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            model_type(foo=input_value)
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize("input_value, output_value", [
        (b"spam", {"foo": "spam"}),
    ])
    def test_dump(self, model, output_value):
        assert dump(model) == output_value

    @pytest.mark.parametrize("input_value", [b"spam"])
    def test_validate_successfully(self, model):
        validate(model)


class TestAnnotatedTypeDescriptor:

    @pytest.mark.parametrize(
        "typ, input_value, output_value",
        [
            (Annotated[int, Ge(0), Le(5)], "0", 0),
            (Annotated[int, Ge(0), Le(5)], "5", 5),
            (Annotated[float, Gt(0), Lt(1)], 0.5, 0.5),
            (Annotated[str, MinLen(1), MaxLen(5)], "a", "a"),
            (Annotated[str, MinLen(1), MaxLen(5)], "12345", "12345"),
            (Annotated[str, Regex("^[a-z]+$")], "abc", "abc"),
        ],
    )
    def test_parse_successfully(self, model, output_value):
        assert model.foo == output_value

    @pytest.mark.parametrize("typ, input_value, expected_errors", [
        (Annotated[int, Ge(0), Le(5)], -1, [ErrorFactory.ge_constraint_failed(loc, -1, 0)]),
        (Annotated[int, Ge(0), Le(5)], 6, [ErrorFactory.le_constraint_failed(loc, 6, 5)]),
        (Annotated[float, Gt(0), Lt(1)], 0, [ErrorFactory.gt_constraint_failed(loc, 0, 0)]),
        (Annotated[float, Gt(0), Lt(1)], 1, [ErrorFactory.lt_constraint_failed(loc, 1, 1)]),
        (Annotated[str, MinLen(1), MaxLen(5)], "", [ErrorFactory.min_len_constraint_failed(loc, "", 1)]),
        (
            Annotated[str, MinLen(1), MaxLen(5)],
            "spam more spam",
            [ErrorFactory.max_len_constraint_failed(loc, "spam more spam", 5)],
        ),
        (
            Annotated[str, Regex("^[a-z]+$")],
            "123",
            [ErrorFactory.regex_constraint_failed(loc, "123", "^[a-z]+$")],
        ),
    ])
    def test_parse_expecting_parsing_errors(self, model_type, input_value, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            model_type(foo=input_value)
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize("typ, input_value, output_value", [
        (Annotated[int, Ge(0), Le(10)], 5, {"foo": 5}),
    ])
    def test_dump(self, model, output_value):
        assert dump(model) == output_value

    @pytest.mark.parametrize("typ, input_value", [
        (Annotated[int, Ge(0), Le(2)], 0),
        (Annotated[int, Ge(0), Le(2)], 1),
        (Annotated[int, Ge(0), Le(2)], 2),
    ])
    def test_validate_successfully(self, model):
        validate(model)

    @pytest.mark.parametrize("typ, input_value", [
        (Annotated[list, MaxLen(3)], []),
    ])
    def test_validation_fails_if_constraint_is_no_longer_satisfied(self, model):
        assert isinstance(model.foo, list)
        assert model.foo == []
        validate(model)
        model.foo.extend([1, 2, 3])
        validate(model)
        model.foo.append(4)  # The length will exceed the limit after this
        with pytest.raises(ValidationError) as excinfo:
            validate(model)
        assert excinfo.value.errors == (ErrorFactory.max_len_constraint_failed(Loc("foo"), [1, 2, 3, 4], 3),)


class TestUnionTypeDescriptor:

    @pytest.fixture
    def type_descriptor(self, typ):
        return make_type_descriptor(typ)

    @pytest.mark.parametrize(
        "typ, value, expected_result, expected_errors",
        [
        ],
    )
    def test_parsing(self, type_descriptor, errors, value, expected_result, expected_errors):
        assert type_descriptor.parse(errors, loc, value) == expected_result
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "typ, input_value, output_value",
        [
            (Optional[str], "spam", "spam"),
            (Optional[str], None, None),
            (Union[int, str], "spam", "spam"),
            (Union[int, str], "123", "123"),
            (Union[int, str], 123, 123),
        ],
    )
    def test_parse_successfully(self, model, output_value):
        assert model.foo == output_value

    @pytest.mark.parametrize("typ, input_value, expected_errors", [
        (
            Union[int, str],
            None,
            [
                ErrorFactory.invalid_integer(loc, None),
                ErrorFactory.string_value_required(loc, None),
            ],
        ),
    ])
    def test_parse_expecting_parsing_errors(self, model_type, input_value, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            model_type(foo=input_value)
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize("typ, input_value, output_value", [
        (Optional[str], "spam", {"foo": "spam"}),
        (Optional[str], None, {"foo": None}),
        (Union[int, str], "dummy", {"foo": "dummy"}),
        (Union[int, str], 123, {"foo": 123}),
    ])
    def test_dump(self, model, output_value):
        assert dump(model) == output_value

    @pytest.mark.parametrize("typ, input_value", [
        (Optional[str], "spam"),
        (Optional[str], None),
    ])
    def test_validate_successfully(self, model):
        validate(model)


class TestTupleTypeDescriptor:

    @pytest.mark.parametrize(
        "typ, input_value, output_value",
        [
            (tuple, [], tuple()),
            (tuple, [1, "2", 3.14], (1, "2", 3.14)),
            (tuple[int, ...], ["1"], tuple([1])),
            (tuple[int, ...], ["1", "2", "3"], tuple([1, 2, 3])),
            (tuple[int, float, str], [1, "3.14", "spam"], tuple([1, 3.14, "spam"])),
        ],
    )
    def test_parse_successfully(self, model, output_value):
        assert model.foo == output_value

    @pytest.mark.parametrize("typ, input_value, expected_errors", [
        (tuple, 123, [ErrorFactory.invalid_tuple(loc, 123)]),
        (tuple, "foo", [ErrorFactory.invalid_tuple(loc, "foo")]),
        (tuple, b"bar", [ErrorFactory.invalid_tuple(loc, b"bar")]),
        (tuple[int, ...], ["1", "a", "2"], [ErrorFactory.invalid_integer(loc + Loc(1), "a")]),
        (
            tuple[int, float, str],
            ["foo", "3.14", "spam"],
            [ErrorFactory.invalid_integer(loc + Loc(0), "foo")],
        ),
        (
            tuple[int, float, str],
            [1, "3.14"],
            [ErrorFactory.unsupported_tuple_format(loc, [1, "3.14"], (int, float, str))],
        ),
        (
            tuple[int, float, str],
            [1, "3.14", "spam", "more spam"],
            [ErrorFactory.unsupported_tuple_format(loc, [1, "3.14", "spam", "more spam"], (int, float, str))],
        ),
    ])
    def test_parse_expecting_parsing_errors(self, model_type, input_value, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            model_type(foo=input_value)
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize("typ, input_value, output_value", [
        (tuple, [1, 3.14, "spam"], {"foo": [1, 3.14, "spam"]},),
        (tuple[int, ...], [1, 2, 3], {"foo": [1, 2, 3]},),
        (tuple[int, float, str], [1, 3.14, "spam"], {"foo": [1, 3.14, "spam"]},),
    ])
    def test_dump(self, model, output_value):
        assert dump(model) == output_value

    @pytest.mark.parametrize("typ, input_value", [
        (tuple, [1, 3.14, "spam"],),
        (tuple[int, ...], [1, 2, 3],),
        (tuple[int, float, str], [1, 3.14, "spam"],),
    ])
    def test_validate_successfully(self, model):
        validate(model)


class TestDictTypeDescriptor:

    @pytest.fixture
    def typ(self):
        return dict[int, float]

    @pytest.fixture
    def out(self, model_type):
        return model_type(foo={}).foo

    @pytest.mark.parametrize(
        "typ, input_value, output_value",
        [
            (dict, {}, {}),
            (dict, {1: "one"}, {1: "one"}),
            (dict[str, int], {"foo": "123"}, {"foo": 123}),
        ],
    )
    def test_parse_successfully(self, model, output_value):
        assert model.foo == output_value

    @pytest.mark.parametrize("typ, input_value, expected_errors", [
        (dict, "foo", [ErrorFactory.invalid_dict(loc, "foo")]),
        (dict, 123, [ErrorFactory.invalid_dict(loc, 123)]),
        (dict[str, int], {1: 2}, [ErrorFactory.string_value_required(loc, 1)]),
        (
            dict[str, int],
            {1: "two"},
            [ErrorFactory.string_value_required(loc, 1), ErrorFactory.invalid_integer(loc + Loc(1), "two")],
        ),
        (dict[str, int], {"two": "two"}, [ErrorFactory.invalid_integer(loc + Loc("two"), "two")]),
    ])
    def test_parse_expecting_parsing_errors(self, model_type, input_value, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            model_type(foo=input_value)
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize("typ, input_value, output_value", [
        (dict, {}, {"foo": {}}),
        (dict[str, int], {"one": "1"}, {"foo": {"one": 1}}),
    ])
    def test_dump(self, model, output_value):
        assert dump(model) == output_value

    @pytest.mark.parametrize("typ, input_value", [
        (dict, {}),
        (dict[str, int], {"one": "1"}),
    ])
    def test_validate_successfully(self, model):
        validate(model)

    @pytest.mark.parametrize(
        "typ, input_value, expected_repr",
        [
            (dict, {}, "{}"),
            (dict[int, float], {"1": "3.14"}, "{1: 3.14}"),
        ],
    )
    def test_repr(self, model, expected_repr):
        assert repr(model.foo) == expected_repr

    @pytest.mark.parametrize(
        "typ, a, b, is_same",
        [
            (dict, {}, {}, True),
            (dict, {1: 2}, {}, False),
            (dict, {1: 2}, {2: 1}, False),
            (dict, {1: 2}, {1: 2}, True),
            (dict[int, int], {}, {}, True),
            (dict[int, int], {1: 2}, {}, False),
            (dict[int, int], {1: 2}, {2: 1}, False),
            (dict[int, int], {1: 2}, {1: 2}, True),
        ],
    )
    def test_eq(self, model_type, a, b, is_same):
        one = model_type(foo=a)
        two = model_type(foo=b)
        assert (one.foo == two.foo) is is_same

    def test_setting_item_converts_keys(self, out: dict):
        out["123"] = 3.14
        assert list(out) == [123]
        assert out[123] == 3.14

    def test_setting_item_converts_values(self, out: dict):
        out[1] = "3.14"
        assert list(out) == [1]
        assert out[1] == 3.14

    def test_parsing_error_is_raised_when_setting_invalid_key(self, out: dict):
        with pytest.raises(ParsingError) as excinfo:
            out["spam"] = 3.14
        assert excinfo.value.errors == tuple([ErrorFactory.invalid_integer(Loc(), "spam")])

    def test_parsing_error_is_raised_when_setting_invalid_value(self, out: dict):
        with pytest.raises(ParsingError) as excinfo:
            out[123] = "spam"
        assert excinfo.value.errors == tuple([ErrorFactory.invalid_float(Loc(123), "spam")])

    def test_set_item_and_delete_it(self, out: dict):
        out[1] = 2
        assert out[1] == 2
        del out[1]
        assert list(out) == []

    def test_check_length(self, out: dict):
        assert len(out) == 0
        out[1] = 3.14
        assert len(out) == 1
        del out[1]
        assert len(out) == 0


class TestListTypeDescriptor:

    @pytest.mark.parametrize(
        "typ, input_value, output_value",
        [
            (list, [], []),
            (list, ["1", "2", "3"], ["1", "2", "3"]),
            (list[int], ["123"], [123]),
            (list[int], ["1", 2, "3"], [1, 2, 3]),
        ],
    )
    def test_parse_successfully(self, model, output_value):
        assert model.foo == output_value

    @pytest.mark.parametrize("typ, input_value, expected_errors", [
        (list, None, [ErrorFactory.invalid_list(loc, None)]),
        (list, 123, [ErrorFactory.invalid_list(loc, 123)]),
        (list, "spam", [ErrorFactory.invalid_list(loc, "spam")]),
        (list, b"more spam", [ErrorFactory.invalid_list(loc, b"more spam")]),
        (list[int], 123, [ErrorFactory.invalid_list(loc, 123)]),
        (list[int], "spam", [ErrorFactory.invalid_list(loc, "spam")]),
        (list[int], b"more spam", [ErrorFactory.invalid_list(loc, b"more spam")]),
        (list[int], ["1", "2", "spam"], [ErrorFactory.invalid_integer(loc + Loc(2), "spam")]),
    ])
    def test_parse_expecting_parsing_errors(self, model_type, input_value, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            model_type(foo=input_value)
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize("typ, input_value, output_value", [
        (list, [1, 3.14, "spam"], {"foo": [1, 3.14, "spam"]}),
        (list[Any], [1, 3.14, "spam"], {"foo": [1, 3.14, "spam"]}),
        (list[int], [1, 3.14, 5], {"foo": [1, 3, 5]}),
    ])
    def test_dump(self, model, output_value):
        assert dump(model) == output_value

    @pytest.mark.parametrize("typ, input_value", [
        (list, [1, 3.14, "spam"]),
        (list[Any], [1, 3.14, "spam"]),
        (list[int], [1, 3.14, 5]),
    ])
    def test_validate_successfully(self, model):
        validate(model)

    @pytest.mark.parametrize(
        "typ, input_value, expected_repr",
        [
            (list, [], "[]"),
            (list, [1, "2"], "[1, '2']"),
            (list[int], [1, "2"], "[1, 2]"),
        ],
    )
    def test_repr(self, model, expected_repr):
        assert repr(model.foo) == expected_repr

    @pytest.mark.parametrize(
        "typ, a, b, is_same",
        [
            (list, [], [], True),
            (list, [1], [], False),
            (list, [1], [2], False),
            (list, [1], [1], True),
            (list[int], [], [], True),
            (list[int], [1], [], False),
            (list[int], [1], [2], False),
            (list[int], [1], [1], True),
        ],
    )
    def test_eq(self, model_type, a, b, is_same):
        left = model_type(foo=a)
        right = model_type(foo=b)
        assert (left == right) is is_same

    @pytest.mark.parametrize("typ", [list[int]])
    def test_setting_getting_and_deleting_items(self, model_type):
        l = model_type(foo=[1]).foo
        assert len(l) == 1
        assert l[0] == 1
        l[0] = "2"
        assert l[0] == 2
        del l[0]
        assert len(l) == 0

    @pytest.mark.parametrize("typ", [list[int]])
    def test_inserting_or_appending_items(self, model_type):
        l = model_type(foo=[1]).foo
        assert l == [1]
        l.insert(0, "123")
        assert l == [123, 1]
        l.append("4")
        assert l == [123, 1, 4]

    @pytest.mark.parametrize(
        "typ, initial, index, value, expected_errors",
        [
            (list[int], [1], 0, "spam", [ErrorFactory.invalid_integer(Loc(0), "spam")]),
        ],
    )
    def test_setting_to_invalid_value_causes_parsing_error(
        self, model_type, initial, index, value, expected_errors
    ):
        l = model_type(foo=initial).foo
        with pytest.raises(ParsingError) as excinfo:
            l[index] = value
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize(
        "typ, initial, index, value, expected_errors",
        [
            (list[int], [1], 0, "spam", [ErrorFactory.invalid_integer(Loc(0), "spam")]),
        ],
    )
    def test_inserting_invalid_value_causes_parsing_error(
        self, model_type, initial, index, value, expected_errors
    ):
        l = model_type(foo=initial).foo
        with pytest.raises(ParsingError) as excinfo:
            l.insert(index, value)
        assert excinfo.value.errors == tuple(expected_errors)


class TestSetTypeDescriptor:

    @pytest.mark.parametrize(
        "typ, input_value, output_value",
        [
            (set, [], set()),
            (set, [1, 3.14, "spam"], {1, 3.14, "spam"}),
            (set[int], [1, 2, "3", 3, "4"], {1, 2, 3, 4}),
        ],
    )
    def test_parse_successfully(self, model, output_value):
        assert model.foo == output_value

    @pytest.mark.parametrize("typ, input_value, expected_errors", [
        (set, 123, [ErrorFactory.invalid_set(loc, 123)]),
        (set, "123", [ErrorFactory.invalid_set(loc, "123")]),
        (set, b"123", [ErrorFactory.invalid_set(loc, b"123")]),
        (set, [[123]], [ErrorFactory.invalid_set(loc, [[123]])]),
        (set[int], 123, [ErrorFactory.invalid_set(loc, 123)]),
        (set[int], "123", [ErrorFactory.invalid_set(loc, "123")]),
        (set[int], b"123", [ErrorFactory.invalid_set(loc, b"123")]),
    ])
    def test_parse_expecting_parsing_errors(self, model_type, input_value, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            model_type(foo=input_value)
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize("typ, input_value, output_value", [
        (set, [1, 2, 2, 3, 4], {"foo": [1, 2, 3, 4]}),
        (set[int], [1, 2, "2", 3, 4], {"foo": [1, 2, 3, 4]}),
    ])
    def test_dump(self, model, output_value):
        assert dump(model) == output_value

    @pytest.mark.parametrize("typ, input_value", [
        (set, [1, 2, 2, 3, 4]),
        (set[int], [1, 2, "2", 3, 4]),
    ])
    def test_validate_successfully(self, model):
        validate(model)

    @pytest.mark.parametrize("typ", [set[list], set[123]])
    def test_making_set_with_non_hashable_type_causes_type_error(self, typ):
        with pytest.raises(TypeError) as excinfo:
            class Dummy(Model):
                foo: typ
        assert str(excinfo.value) == "'T' must be hashable type to be used with 'set[T]' generic type"

    @pytest.mark.parametrize(
        "typ, input_value, expected_repr",
        [
            (set, [], "set()"),
            (set, ["2"], "{'2'}"),
            (set[int], ["2"], "{2}"),
        ],
    )
    def test_repr(self, model, expected_repr):
        assert repr(model.foo) == expected_repr

    @pytest.mark.parametrize(
        "typ, a, b, is_same",
        [
            (set, [], [], True),
            (set, [1, 1, 1], [1], True),
            (set[int], ["123"], [123], True),
        ],
    )
    def test_eq(self, model_type, a, b, is_same):
        left = model_type(foo=a)
        right = model_type(foo=b)
        assert (left == right) is is_same

    @pytest.mark.parametrize("typ", [set[int]])
    def test_adding_item_converts_it_according_to_item_type(self, model_type):
        s = model_type(foo=[]).foo
        s.add("123")
        assert s == {123}

    @pytest.mark.parametrize("typ", [set[int]])
    def test_adding_invalid_item_causes_parsing_error(self, model_type):
        s = model_type(foo=[]).foo
        with pytest.raises(ParsingError) as excinfo:
            s.add("dummy")
        assert excinfo.value.errors == tuple([ErrorFactory.invalid_integer(Loc(), "dummy")])

    @pytest.mark.parametrize("typ", [set[int]])
    def test_add_value_and_discard_it(self, model_type):
        s = model_type(foo=[]).foo
        s.add("123")
        assert s == {123}
        s.discard(123)
        assert s == set()

    @pytest.mark.parametrize("typ", [set[int]])
    def test_contains_and_len(self, model_type):
        s = model_type(foo=[]).foo
        assert s is not Unset
        assert 123 not in s
        assert len(s) == 0
        s.add("123")
        assert 123 in s
        assert len(s) == 1
        s.discard(123)
        assert len(s) == 0

    @pytest.mark.parametrize("typ", [set[int]])
    def test_iter(self, model_type):
        s = model_type(foo=[]).foo
        assert list(s) == []
        s.add(1)
        s.add(2)
        s.add("3")
        assert list(s) == [1, 2, 3]


class TestModelTypeDescriptor:

    class Dummy(Model):
        class Nested(Model):
            a: int

        nested: Nested

    @pytest.fixture
    def type_descriptor(self, typ):
        return make_type_descriptor(typ)

    @pytest.mark.parametrize(
        "typ, value, expected_result, expected_errors",
        [
        ],
    )
    def test_parsing(self, type_descriptor, errors, value, expected_result, expected_errors):
        assert type_descriptor.parse(errors, loc, value) == expected_result
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "typ, input_value, output_value",
        [
            (Dummy, {}, Dummy()),
            (Dummy, {"nested": {}}, Dummy(nested=Dummy.Nested())),
            (Dummy, {"nested": {"a": "123"}}, Dummy(nested=Dummy.Nested(a=123))),
        ],
    )
    def test_parse_successfully(self, model, output_value):
        assert model.foo == output_value

    @pytest.mark.parametrize("typ, input_value, expected_errors", [
        (Dummy, 123, [ErrorFactory.invalid_model(loc, 123, Dummy)]),
        (Dummy, {"nested": {"a": "spam"}}, [ErrorFactory.invalid_integer(loc + Loc("nested", "a"), "spam")]),
    ])
    def test_parse_expecting_parsing_errors(self, model_type, input_value, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            model_type(foo=input_value)
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize("typ, filter, input_value, output_value", [
        (Dummy, lambda l, v: v, {}, {"foo": {"nested": Unset}}),
        (Dummy, lambda l, v: v if v is not Unset else DISCARD, {}, {"foo": {}}),
        (Dummy, lambda l, v: v if l.last != "foo" else DISCARD, {}, {}),
    ])
    def test_dump(self, model, filter, output_value):
        assert model.dump(Loc(), filter) == output_value

    @pytest.mark.parametrize("typ, input_value", [
        (Dummy, {"nested": {"a": 123}}),
    ])
    def test_validate_successfully(self, model):
        validate(model)

    @pytest.mark.parametrize("typ, input_value, expected_errors", [
        (Dummy, {"nested": {}}, [ErrorFactory.required_missing(Loc("foo", "nested", "a"))]),
        (Dummy, {}, [ErrorFactory.required_missing(Loc("foo", "nested"))]),
        (Dummy, Unset, [ErrorFactory.required_missing(Loc("foo"))]),
    ])
    def test_validate_with_validation_errors(self, model, expected_errors):
        with pytest.raises(ValidationError) as excinfo:
            validate(model)
        assert excinfo.value.errors == tuple(expected_errors)
