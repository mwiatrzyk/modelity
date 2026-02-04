import pytest

from modelity.error import Error, ErrorCode, ErrorFactory
from modelity.exc import ParsingError, UserError
from modelity.hooks import field_preprocessor
from modelity.loc import Loc
from modelity.model import Model
from modelity.unset import Unset


@pytest.mark.parametrize(
    "factory, expected_error",
    [
        (lambda: UserError("a message"), Error(Loc("foo"), ErrorCode.USER_ERROR, "a message", "spam", {})),
        (
            lambda: UserError("a message", code=ErrorCode.PARSE_ERROR),
            Error(Loc("foo"), ErrorCode.PARSE_ERROR, "a message", "spam", {}),
        ),
        (
            lambda: UserError("a message", loc=Loc("bar")),
            Error(Loc("bar"), ErrorCode.USER_ERROR, "a message", "spam", {}),
        ),
        (
            lambda: UserError("a message", value=123),
            Error(Loc("foo"), ErrorCode.USER_ERROR, "a message", 123, {}),
        ),
        (
            lambda: UserError("a message", data={"min": 0, "max": 10}),
            Error(Loc("foo"), ErrorCode.USER_ERROR, "a message", "spam", {"min": 0, "max": 10}),
        ),
    ],
)
def test_user_error_raised_is_converted_to_error(factory, expected_error):

    class SUT(Model):
        foo: int

        @field_preprocessor("foo")
        def _preprocess_foo(value):
            raise factory()

    with pytest.raises(ParsingError) as excinfo:
        SUT(foo="spam")
    assert excinfo.value.errors == (expected_error,)
