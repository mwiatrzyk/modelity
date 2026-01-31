import pytest

from modelity.error import ErrorFactory
from modelity.exc import ModelError, ParsingError, UnsupportedTypeError, ValidationError
from modelity.loc import Loc
from modelity.model import Model


class TestUnsupportedTypeError:

    def test_str(self):
        assert str(UnsupportedTypeError(int)) == "unsupported type used: <class 'int'>"


class TestModelError:

    # fmt: off
    @pytest.mark.parametrize(
        "errors, params, expected_result",
        [
            (
                [
                    ErrorFactory.required_missing(Loc("foo")),
                    ErrorFactory.required_missing(Loc("bar")),
                ],
                {},
                "foo:\n"
                "  This field is required\n"
                "bar:\n"
                "  This field is required"
            ),
            (
                [
                    ErrorFactory.required_missing(Loc("foo")),
                    ErrorFactory.required_missing(Loc("bar")),
                ],
                {"sort_key": lambda x: x.loc},
                "bar:\n"
                "  This field is required\n"
                "foo:\n"
                "  This field is required"
            ),
            (
                [
                    ErrorFactory.invalid_type(Loc("foo"), 123, [str], [bytes]),
                ],
                {},
                "foo:\n"
                "  Not a valid value; expected a str",
            ),
            (
                [
                    ErrorFactory.required_missing(Loc("foo")),
                    ErrorFactory.required_missing(Loc("bar")),
                ],
                {"show_code": True},
                "foo:\n"
                "  This field is required [code=modelity.REQUIRED_MISSING]\n"
                "bar:\n"
                "  This field is required [code=modelity.REQUIRED_MISSING]",
            ),
            (
                [
                    ErrorFactory.invalid_type(Loc("foo"), 123, [str], [bytes]),
                ],
                {"show_value": True},
                "foo:\n"
                "  Not a valid value; expected a str [value=123]",
            ),
            (
                [
                    ErrorFactory.invalid_type(Loc("foo"), 123, [str], [bytes]),
                ],
                {"show_value_type": True},
                "foo:\n"
                "  Not a valid value; expected a str [value_type=int]",
            ),
            (
                [
                    ErrorFactory.invalid_type(Loc("foo"), 123, [str], [bytes], [int, float]),
                ],
                {"show_data": True},
                "foo:\n"
                "  Not a valid value; expected a str [expected_types=[str], allowed_types=[bytes], forbidden_types=[int, float]]",
            ),
        ],
    )
    # fmt: on
    def test_format_errors(self, errors, params, expected_result):
        uut = ModelError(object, errors)
        assert uut.format_errors(**params) == expected_result


class TestParsingError:

    # fmt: off
    @pytest.mark.parametrize("exc, expected_result", [
        (
            ParsingError(int, (ErrorFactory.parse_error(Loc("foo"), "foo", int),)),
            "Found 1 parsing error for type 'int':\n"
            "  foo:\n"
            "    Not a valid int value [code=modelity.PARSE_ERROR, value_type=str, expected_type=int]"
        ),
        (
            ParsingError(
                int,
                (
                    ErrorFactory.parse_error(Loc("foo"), "foo", int),
                    ErrorFactory.parse_error(Loc("bar"), "bar", float)
                )
            ),
            "Found 2 parsing errors for type 'int':\n"
            "  bar:\n"
            "    Not a valid float value [code=modelity.PARSE_ERROR, value_type=str, expected_type=float]\n"
            "  foo:\n"
            "    Not a valid int value [code=modelity.PARSE_ERROR, value_type=str, expected_type=int]"
        ),
    ])
    # fmt: on
    def test_format_as_string(self, exc, expected_result):
        assert str(exc) == expected_result


class TestValidationError:

    class Dummy(Model):
        pass

    # fmt: off
    @pytest.mark.parametrize("exc, expected_result", [
        (
            ValidationError(Dummy(), (ErrorFactory.required_missing(Loc("foo")),)),
            "Found 1 validation error for model 'TestValidationError.Dummy':\n"
            "  foo:\n"
            "    This field is required [code=modelity.REQUIRED_MISSING]"
        ),
        (
            ValidationError(
                Dummy(),
                (
                    ErrorFactory.required_missing(Loc("foo")),
                    ErrorFactory.required_missing(Loc("bar"))
                )
            ),
            "Found 2 validation errors for model 'TestValidationError.Dummy':\n"
            "  bar:\n"
            "    This field is required [code=modelity.REQUIRED_MISSING]\n"
            "  foo:\n"
            "    This field is required [code=modelity.REQUIRED_MISSING]"
        ),
    ])
    # fmt: on
    def test_format_as_string(self, exc, expected_result):
        assert str(exc) == expected_result
