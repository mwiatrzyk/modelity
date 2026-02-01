import pytest

from modelity.error import ErrorFactory
from modelity.exc import ModelError, ParsingError, UnsupportedTypeError, ValidationError
from modelity.loc import Loc
from modelity.model import Model


class TestUnsupportedTypeError:

    def test_str(self):
        assert str(UnsupportedTypeError(int)) == "unsupported type used: <class 'int'>"


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
