import pytest

from modelity.error import Error, ErrorCode
from modelity.exc import UserError, ValidationError
from modelity.helpers import validate
from modelity.hooks import model_prevalidator
from modelity.loc import Loc
from modelity.model import Model


@pytest.mark.parametrize(
    "factory, expected_error",
    [
        (lambda: UserError("a message"), Error(Loc(), ErrorCode.USER_ERROR, "a message")),
        (
            lambda: UserError("a message", code=ErrorCode.PARSE_ERROR),
            Error(Loc(), ErrorCode.PARSE_ERROR, "a message"),
        ),
        (
            lambda: UserError("a message", loc=Loc("bar")),
            Error(Loc("bar"), ErrorCode.USER_ERROR, "a message"),
        ),
        (
            lambda: UserError("a message", value=456),
            Error(Loc(), ErrorCode.USER_ERROR, "a message", 456),
        ),
        (
            lambda: UserError("a message", data={"min": 0, "max": 10}),
            Error(Loc(), ErrorCode.USER_ERROR, "a message", data={"min": 0, "max": 10}),
        ),
    ],
)
def test_user_error_raised_is_converted_to_error(factory, expected_error):

    class SUT(Model):
        foo: int

        @model_prevalidator()
        def _model_prevalidator():
            raise factory()

    sut = SUT(foo=123)
    with pytest.raises(ValidationError) as excinfo:
        validate(sut)
    assert excinfo.value.errors == (expected_error,)


def test_user_error_with_skip_set_skips_other_validators():

    class SUT(Model):
        foo: int

        @model_prevalidator()
        def _model_prevalidator():
            raise UserError("an error", skip=True)

    sut = SUT()
    with pytest.raises(ValidationError) as excinfo:
        validate(sut)
    assert excinfo.value.errors == (Error(Loc(), ErrorCode.USER_ERROR, "an error"),)
