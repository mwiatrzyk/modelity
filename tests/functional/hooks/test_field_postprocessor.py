import pytest

from modelity.error import Error, ErrorCode
from modelity.exc import ParsingError, UserError
from modelity.hooks import field_postprocessor
from modelity.loc import Loc
from modelity.model import Model


@pytest.mark.parametrize(
    "factory, expected_error",
    [
        (lambda: UserError("a message"), Error(Loc("foo"), ErrorCode.USER_ERROR, "a message", 123, {})),
        (
            lambda: UserError("a message", code=ErrorCode.PARSE_ERROR),
            Error(Loc("foo"), ErrorCode.PARSE_ERROR, "a message", 123, {}),
        ),
        (
            lambda: UserError("a message", loc=Loc("bar")),
            Error(Loc("bar"), ErrorCode.USER_ERROR, "a message", 123, {}),
        ),
        (
            lambda: UserError("a message", value=456),
            Error(Loc("foo"), ErrorCode.USER_ERROR, "a message", 456, {}),
        ),
        (
            lambda: UserError("a message", data={"min": 0, "max": 10}),
            Error(Loc("foo"), ErrorCode.USER_ERROR, "a message", 123, {"min": 0, "max": 10}),
        ),
    ],
)
def test_user_error_raised_is_converted_to_error(factory, expected_error):

    class SUT(Model):
        foo: int

        @field_postprocessor("foo")
        def _postprocess_foo(value):
            raise factory()

    with pytest.raises(ParsingError) as excinfo:
        SUT(foo=123)
    assert excinfo.value.errors == (expected_error,)
