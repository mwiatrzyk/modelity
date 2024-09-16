import pytest

from mockify.api import Mock, satisfied, Return, Raise

from modelity.loc import Loc
from modelity._utils import is_subsequence, make_noexcept_func

from tests.helpers import ErrorFactoryHelper


@pytest.mark.parametrize(
    "candidate, sequence, expected_result",
    [
        ([1], [1], True),
        ([1], [2], False),
        ([1, 2], [2], False),
        ([1, 3], [0, 1, 2, 3], True),
        ([1, 3, 4], [1], False),
        ([1, 3], [0, 3, 2, 1], False),
    ],
)
def test_is_subsequence(candidate, sequence, expected_result):
    assert is_subsequence(candidate, sequence) == expected_result


class TestMakeNoexceptFunc:

    @pytest.fixture
    def mock(self):
        mock = Mock("mock")
        with satisfied(mock):
            yield mock

    @pytest.mark.parametrize(
        "args, kwargs",
        [
            ([], {}),
            ([1, 2], {}),
            ([], {"a": 1}),
            ([1, 2], {"a": 1}),
        ],
    )
    def test_new_function_returns_whatever_wrapped_function_returns(self, mock, args, kwargs):

        def func(*args, **kwargs):
            return mock(*args, **kwargs)

        mock.expect_call(*args, **kwargs).will_once(Return(123))
        wrapped = make_noexcept_func(func)
        assert wrapped(*args, **kwargs) == 123

    @pytest.mark.parametrize(
        "exc, loc, expected_error",
        [
            (ValueError("foo"), Loc(), ErrorFactoryHelper.value_error(Loc(), "foo")),
            (ValueError("foo"), Loc("dummy"), ErrorFactoryHelper.value_error(Loc("dummy"), "foo")),
            (TypeError("bar"), Loc(), ErrorFactoryHelper.type_error(Loc(), "bar")),
            (TypeError("bar"), Loc("dummy"), ErrorFactoryHelper.type_error(Loc("dummy"), "bar")),
        ],
    )
    def test_when_wrapped_function_raises_known_exception_then_it_is_converted_to_error(
        self, mock, exc, loc, expected_error
    ):

        def func():
            return mock()

        mock.expect_call().will_once(Raise(exc))
        wrapped = make_noexcept_func(func, loc)
        assert wrapped() == expected_error
