from typing import Any, Sequence
import pytest

from mockify.api import ordered, Return

from modelity.error import ErrorFactory
from modelity.loc import Loc
from modelity.model import Model, field_info

from modelity.types import Deferred
from modelity.unset import Unset
from tests.functional.types import common


@pytest.mark.parametrize(
    "typ",
    [
        list,
        list[Any],
    ],
)
class TestAnyList:

    @pytest.fixture
    def SUT(self, typ):

        class SUT(Model):
            foo: Deferred[typ] = Unset  # type: ignore

        return SUT

    @pytest.fixture(autouse=True)
    def setup(self, SUT):
        self.SUT = SUT

    @pytest.fixture(
        params=[
            ([], [], []),
            ([1], [1], [1]),
            ([1, 3.14, "spam"], [1, 3.14, "spam"], [1, 3.14, "spam"]),
        ]
    )
    def data(self, request):
        return request.param

    @pytest.fixture(
        params=[
            (None, [ErrorFactory.invalid_type(common.loc, None, [list], [Sequence], [str, bytes])]),
        ]
    )
    def invalid_data(self, request):
        return request.param

    def test_construct_successfully(self, input, expected_output):
        common.test_construct_successfully(self, input, expected_output)

    def test_assign_successfully(self, input, expected_output):
        common.test_assign_successfully(self, input, expected_output)

    def test_validate_successfully(self, input, expected_output):
        common.test_validate_successfully(self, input, expected_output)

    def test_dump_successfully(self, input, expected_dump_output):
        common.test_dump_successfully(self, input, expected_dump_output)

    def test_constructing_fails_for_invalid_input(self, invalid_input, expected_errors):
        common.test_constructing_fails_for_invalid_input(self, invalid_input, expected_errors)

    def test_assignment_fails_for_invalid_input(self, invalid_input, expected_errors):
        common.test_assignment_fails_for_invalid_input(self, invalid_input, expected_errors)

    def test_accept_visitor(self, mock):
        sut = self.SUT(foo=[1, 3.14, "spam"])
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_sequence_begin.expect_call(Loc("foo"), sut.foo)
        mock.visit_any.expect_call(Loc("foo", 0), 1)
        mock.visit_any.expect_call(Loc("foo", 1), 3.14)
        mock.visit_any.expect_call(Loc("foo", 2), "spam")
        mock.visit_sequence_end.expect_call(Loc("foo"), sut.foo)
        mock.visit_model_field_end.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_model_end.expect_call(Loc(), sut)
        with ordered(mock):
            sut.accept(mock, Loc())

    def test_when_visit_sequence_begin_returns_true_then_visiting_sequence_is_skipped(self, mock):
        sut = self.SUT(foo=[1, 3.14, "spam"])
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_sequence_begin.expect_call(Loc("foo"), sut.foo).will_once(Return(True))
        mock.visit_model_field_end.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_model_end.expect_call(Loc(), sut)
        with ordered(mock):
            sut.accept(mock, Loc())


class TestTypedList:

    class SUT(Model):
        foo: list[int] = field_info(default_factory=list)

    @pytest.fixture(
        params=[
            ([], [], []),
            ([1], [1], [1]),
            ([1, 2.71, "3"], [1, 2, 3], [1, 2, 3]),
        ]
    )
    def data(self, request):
        return request.param

    @pytest.fixture(
        params=[
            (None, [ErrorFactory.invalid_type(common.loc, None, [list], [Sequence], [str, bytes])]),
            ([1, 2, "spam"], [ErrorFactory.parse_error(common.loc + Loc(2), "spam", int)]),
        ]
    )
    def invalid_data(self, request):
        return request.param

    def test_construct_successfully(self, input, expected_output):
        common.test_construct_successfully(self, input, expected_output)

    def test_assign_successfully(self, input, expected_output):
        common.test_assign_successfully(self, input, expected_output)

    def test_validate_successfully(self, input, expected_output):
        common.test_validate_successfully(self, input, expected_output)

    def test_dump_successfully(self, input, expected_dump_output):
        common.test_dump_successfully(self, input, expected_dump_output)

    def test_constructing_fails_for_invalid_input(self, invalid_input, expected_errors):
        common.test_constructing_fails_for_invalid_input(self, invalid_input, expected_errors)

    def test_assignment_fails_for_invalid_input(self, invalid_input, expected_errors):
        common.test_assignment_fails_for_invalid_input(self, invalid_input, expected_errors)

    def test_accept_visitor(self, mock):
        sut = self.SUT(foo=[1, 2])
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_sequence_begin.expect_call(Loc("foo"), sut.foo)
        mock.visit_scalar.expect_call(Loc("foo", 0), 1)
        mock.visit_scalar.expect_call(Loc("foo", 1), 2)
        mock.visit_sequence_end.expect_call(Loc("foo"), sut.foo)
        mock.visit_model_field_end.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_model_end.expect_call(Loc(), sut)
        with ordered(mock):
            sut.accept(mock, Loc())

    def test_when_visit_sequence_begin_returns_true_then_visiting_sequence_is_skipped(self, mock):
        sut = self.SUT(foo=[1, 2, 3])
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_sequence_begin.expect_call(Loc("foo"), sut.foo).will_once(Return(True))
        mock.visit_model_field_end.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_model_end.expect_call(Loc(), sut)
        with ordered(mock):
            sut.accept(mock, Loc())
