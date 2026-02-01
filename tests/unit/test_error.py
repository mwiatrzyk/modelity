from enum import Enum
from io import StringIO
from typing import Sequence
import pytest

from modelity.error import Error, ErrorCode, ErrorFactory, ErrorWriter
from modelity.loc import Loc

loc = Loc("foo")


class EDummy(Enum):
    FOO = 1
    BAR = 2
    BAZ = 3


class TestErrorFactory:

    @pytest.mark.parametrize(
        "error, expected_error",
        [
            (
                ErrorFactory.parse_error(loc, "foo", int),
                Error(loc, ErrorCode.PARSE_ERROR, "Not a valid int value", "foo", data={"expected_type": int}),
            ),
            (
                ErrorFactory.parse_error(loc, "foo", int, msg="custom message"),
                Error(loc, ErrorCode.PARSE_ERROR, "custom message", "foo", data={"expected_type": int}),
            ),
            (
                ErrorFactory.parse_error(loc, "foo", int, additional_option=True),
                Error(
                    loc,
                    ErrorCode.PARSE_ERROR,
                    "Not a valid int value",
                    "foo",
                    data={
                        "expected_type": int,
                        "additional_option": True,
                    },
                ),
            ),
            (
                ErrorFactory.conversion_error(loc, "foo", "a reason", set),
                Error(
                    loc,
                    ErrorCode.CONVERSION_ERROR,
                    "Cannot convert str to set; a reason",
                    "foo",
                    data={
                        "expected_type": set,
                    },
                ),
            ),
            (
                ErrorFactory.invalid_value(loc, "3.0", ["2.0"]),
                Error(
                    loc,
                    ErrorCode.INVALID_VALUE,
                    "Not a valid value; expected: '2.0'",
                    "3.0",
                    data={"expected_values": ["2.0"]},
                ),
            ),
            (
                ErrorFactory.invalid_value(loc, 123, [1, 3.14, "spam"]),
                Error(
                    loc,
                    ErrorCode.INVALID_VALUE,
                    "Not a valid value; expected one of: 1, 3.14, 'spam'",
                    123,
                    data={"expected_values": [1, 3.14, "spam"]},
                ),
            ),
            (
                ErrorFactory.invalid_type(loc, "foo", [int]),
                Error(
                    loc,
                    ErrorCode.INVALID_TYPE,
                    "Not a valid value; expected: int",
                    "foo",
                    data={"expected_types": [int]},
                ),
            ),
            (
                ErrorFactory.invalid_type(loc, "foo", [int, float]),
                Error(
                    loc,
                    ErrorCode.INVALID_TYPE,
                    "Not a valid value; expected one of: int, float",
                    "foo",
                    data={"expected_types": [int, float]},
                ),
            ),
            (
                ErrorFactory.invalid_type(loc, "foo", [list], [Sequence]),
                Error(
                    loc,
                    ErrorCode.INVALID_TYPE,
                    "Not a valid value; expected: list",
                    "foo",
                    data={"expected_types": [list], "allowed_types": [Sequence]},
                ),
            ),
            (
                ErrorFactory.invalid_type(loc, "foo", [list], [Sequence], [str, bytes]),
                Error(
                    loc,
                    ErrorCode.INVALID_TYPE,
                    "Not a valid value; expected: list",
                    "foo",
                    data={
                        "expected_types": [list],
                        "allowed_types": [Sequence],
                        "forbidden_types": [str, bytes],
                    },
                ),
            ),
            (
                ErrorFactory.invalid_datetime_format(loc, "spam", ["YYYY-MM-DD"]),
                Error(
                    loc,
                    ErrorCode.INVALID_DATETIME_FORMAT,
                    "Not a valid datetime format; expected: YYYY-MM-DD",
                    "spam",
                    data={"expected_formats": ["YYYY-MM-DD"]},
                ),
            ),
            (
                ErrorFactory.invalid_datetime_format(loc, "spam", ["YYYY-MM-DD", "DD-MM-YYYY"]),
                Error(
                    loc,
                    ErrorCode.INVALID_DATETIME_FORMAT,
                    "Not a valid datetime format; expected one of: YYYY-MM-DD, DD-MM-YYYY",
                    "spam",
                    data={"expected_formats": ["YYYY-MM-DD", "DD-MM-YYYY"]},
                ),
            ),
            (
                ErrorFactory.invalid_date_format(loc, "spam", ["YYYY-MM-DD"]),
                Error(
                    loc,
                    ErrorCode.INVALID_DATE_FORMAT,
                    "Not a valid date format; expected: YYYY-MM-DD",
                    "spam",
                    data={"expected_formats": ["YYYY-MM-DD"]},
                ),
            ),
            (
                ErrorFactory.invalid_date_format(loc, "spam", ["YYYY-MM-DD", "DD-MM-YYYY"]),
                Error(
                    loc,
                    ErrorCode.INVALID_DATE_FORMAT,
                    "Not a valid date format; expected one of: YYYY-MM-DD, DD-MM-YYYY",
                    "spam",
                    data={"expected_formats": ["YYYY-MM-DD", "DD-MM-YYYY"]},
                ),
            ),
            (
                ErrorFactory.invalid_enum_value(loc, "spam", EDummy),
                Error(
                    loc,
                    ErrorCode.INVALID_ENUM_VALUE,
                    "Not a valid value; expected one of: 1, 2, 3",
                    "spam",
                    data={
                        "expected_enum_type": EDummy,
                    },
                ),
            ),
            (
                ErrorFactory.decode_error(loc, b"\xff", ["ascii"]),
                Error(
                    loc,
                    ErrorCode.DECODE_ERROR,
                    "Invalid text encoding",
                    b"\xff",
                    data={"expected_encodings": ["ascii"]},
                ),
            ),
            (
                ErrorFactory.invalid_tuple_length(loc, tuple([1, 2]), tuple([str, float, int])),
                Error(
                    loc,
                    ErrorCode.INVALID_TUPLE_LENGTH,
                    "Not a valid tuple; expected 3 elements, got 2",
                    (1, 2),
                    data={"expected_tuple": (str, float, int)},
                ),
            ),
            (
                ErrorFactory.out_of_range(loc, -1, min_inclusive=0),
                Error(
                    loc,
                    ErrorCode.OUT_OF_RANGE,
                    "Value must be >= 0",
                    -1,
                    data={
                        "min_inclusive": 0,
                    },
                ),
            ),
            (
                ErrorFactory.out_of_range(loc, -1, min_exclusive=0),
                Error(
                    loc,
                    ErrorCode.OUT_OF_RANGE,
                    "Value must be > 0",
                    -1,
                    data={
                        "min_exclusive": 0,
                    },
                ),
            ),
            (
                ErrorFactory.out_of_range(loc, 6, max_inclusive=5),
                Error(
                    loc,
                    ErrorCode.OUT_OF_RANGE,
                    "Value must be <= 5",
                    6,
                    data={
                        "max_inclusive": 5,
                    },
                ),
            ),
            (
                ErrorFactory.out_of_range(loc, 6, max_exclusive=5),
                Error(
                    loc,
                    ErrorCode.OUT_OF_RANGE,
                    "Value must be < 5",
                    6,
                    data={
                        "max_exclusive": 5,
                    },
                ),
            ),
            (
                ErrorFactory.out_of_range(loc, 6, min_inclusive=0, max_inclusive=5),
                Error(
                    loc,
                    ErrorCode.OUT_OF_RANGE,
                    "Expected value in range [0, 5]",
                    6,
                    data={
                        "min_inclusive": 0,
                        "max_inclusive": 5,
                    },
                ),
            ),
            (
                ErrorFactory.out_of_range(loc, 6, min_inclusive=0, max_exclusive=5),
                Error(
                    loc,
                    ErrorCode.OUT_OF_RANGE,
                    "Expected value in range [0, 5)",
                    6,
                    data={
                        "min_inclusive": 0,
                        "max_exclusive": 5,
                    },
                ),
            ),
            (
                ErrorFactory.out_of_range(loc, 6, min_exclusive=0, max_inclusive=5),
                Error(
                    loc,
                    ErrorCode.OUT_OF_RANGE,
                    "Expected value in range (0, 5]",
                    6,
                    data={
                        "min_exclusive": 0,
                        "max_inclusive": 5,
                    },
                ),
            ),
            (
                ErrorFactory.out_of_range(loc, 6, min_exclusive=0, max_exclusive=5),
                Error(
                    loc,
                    ErrorCode.OUT_OF_RANGE,
                    "Expected value in range (0, 5)",
                    6,
                    data={
                        "min_exclusive": 0,
                        "max_exclusive": 5,
                    },
                ),
            ),
            (
                ErrorFactory.invalid_length(loc, "spam", min_length=5),
                Error(loc, ErrorCode.INVALID_LENGTH, "Expected length >= 5", "spam", data={"min_length": 5}),
            ),
            (
                ErrorFactory.invalid_length(loc, "dummy", max_length=4),
                Error(loc, ErrorCode.INVALID_LENGTH, "Expected length <= 4", "dummy", data={"max_length": 4}),
            ),
            (
                ErrorFactory.invalid_length(loc, "dummy", min_length=1, max_length=4),
                Error(
                    loc,
                    ErrorCode.INVALID_LENGTH,
                    "Expected length in range [1, 4]",
                    "dummy",
                    data={"min_length": 1, "max_length": 4},
                ),
            ),
            (
                ErrorFactory.invalid_string_format(loc, "spam", "XX-YYYY"),
                Error(
                    loc,
                    ErrorCode.INVALID_STRING_FORMAT,
                    "String does not match the expected format",
                    "spam",
                    data={"expected_pattern": "XX-YYYY"},
                ),
            ),
            (
                ErrorFactory.invalid_string_format(loc, "spam", "XX-YYYY", msg="Not a valid postal code"),
                Error(
                    loc,
                    ErrorCode.INVALID_STRING_FORMAT,
                    "Not a valid postal code",
                    "spam",
                    data={"expected_pattern": "XX-YYYY"},
                ),
            ),
            (
                ErrorFactory.required_missing(loc),
                Error(
                    loc,
                    ErrorCode.REQUIRED_MISSING,
                    "This field is required",
                ),
            ),
            (
                ErrorFactory.exception(loc, 123, ValueError("an error")),
                Error(loc, ErrorCode.EXCEPTION, "an error", 123, data={"exc_type": ValueError}),
            ),
        ],
    )
    def test_create_error_and_check_the_result(self, error, expected_error):
        assert error == expected_error

    def test_out_of_range_fails_if_called_with_both_min_inclusive_and_min_exclusive(self):
        with pytest.raises(ValueError):
            ErrorFactory.out_of_range(loc, -1, min_inclusive=0, min_exclusive=0)

    def test_out_of_range_fails_if_called_with_both_max_inclusive_and_max_exclusive(self):
        with pytest.raises(ValueError):
            ErrorFactory.out_of_range(loc, -1, max_inclusive=5, max_exclusive=5)

    def test_out_of_range_fails_if_range_args_not_provided(self):
        with pytest.raises(TypeError):
            ErrorFactory.out_of_range(loc, -1)

    def test_invalid_length_factory_fails_when_neither_of_min_length_max_length_given(self):
        with pytest.raises(TypeError):
            ErrorFactory.invalid_length(loc, "spam")


class TestErrorFormatter:

    @pytest.fixture
    def out(self):
        return StringIO()

    @pytest.fixture
    def uut(self, out, indent_string, indent_level, show_code, show_value, show_value_type, show_data):
        return ErrorWriter(out, indent_string, indent_level, show_code, show_value, show_value_type, show_data)

    @pytest.mark.parametrize(
        "error, indent_string, indent_level, show_code, show_value, show_value_type, show_data, expected_result",
        [
            (
                ErrorFactory.parse_error(loc, "spam", int),
                "",
                0,
                False,
                False,
                False,
                False,
                f"{loc}:\nNot a valid int value\n",
            ),
            (
                ErrorFactory.parse_error(loc, "spam", int),
                "  ",
                0,
                False,
                False,
                False,
                False,
                f"{loc}:\n  Not a valid int value\n",
            ),
            (
                ErrorFactory.parse_error(loc, "spam", int),
                "  ",
                1,
                False,
                False,
                False,
                False,
                f"  {loc}:\n    Not a valid int value\n",
            ),
            (
                ErrorFactory.parse_error(loc, "spam", int),
                "",
                0,
                True,
                False,
                False,
                False,
                f"{loc}:\nNot a valid int value [code=modelity.PARSE_ERROR]\n",
            ),
            (
                ErrorFactory.parse_error(loc, "spam", int),
                "",
                0,
                False,
                True,
                False,
                False,
                f"{loc}:\nNot a valid int value [value='spam']\n",
            ),
            (
                ErrorFactory.parse_error(loc, "spam", int),
                "",
                0,
                False,
                False,
                True,
                False,
                f"{loc}:\nNot a valid int value [value_type=str]\n",
            ),
            (
                ErrorFactory.invalid_length(loc, "spam", 5, 10),
                "",
                0,
                False,
                False,
                False,
                True,
                f"{loc}:\nExpected length in range [5, 10] [min_length=5, max_length=10]\n",
            ),
            (
                ErrorFactory.invalid_length(loc, "spam", 5, 10),
                "",
                0,
                True,
                False,
                False,
                True,
                f"{loc}:\nExpected length in range [5, 10] [code=modelity.INVALID_LENGTH, min_length=5, max_length=10]\n",
            ),
            (
                ErrorFactory.invalid_length(loc, "spam", 5, 10),
                "",
                0,
                True,
                False,
                True,
                True,
                f"{loc}:\nExpected length in range [5, 10] [code=modelity.INVALID_LENGTH, value_type=str, min_length=5, max_length=10]\n",
            ),
        ],
    )
    def test_format(self, uut: ErrorWriter, out: StringIO, error, expected_result):
        uut.write(error)
        assert out.getvalue() == expected_result
