from typing import Sequence
import pytest

from mockify.api import ordered, Return

from modelity.error import ErrorFactory
from modelity.loc import Loc
from modelity.model import Model

from tests.functional.types import common


class TestAnyTuple:

    class SUT(Model):
        foo: tuple

    @pytest.fixture(
        params=[
            ([], tuple(), []),
            ([1], (1,), [1]),
            ([1, 3.14, "spam"], (1, 3.14, "spam"), [1, 3.14, "spam"]),
        ]
    )
    def data(self, request):
        return request.param

    @pytest.fixture(
        params=[
            (None, [ErrorFactory.invalid_type(common.loc, None, [tuple], [Sequence], [str, bytes])]),
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
        sut = self.SUT(foo=(1, 2))
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_sequence_begin.expect_call(Loc("foo"), sut.foo)
        mock.visit_any.expect_call(Loc("foo", 0), 1)
        mock.visit_any.expect_call(Loc("foo", 1), 2)
        mock.visit_sequence_end.expect_call(Loc("foo"), sut.foo)
        mock.visit_model_field_end.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_model_end.expect_call(Loc(), sut)
        sut.accept(mock, Loc())

    def test_when_visit_set_begin_returns_true_then_visiting_set_is_skipped(self, mock):
        sut = self.SUT(foo=(1, 3.14, "spam"))
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_sequence_begin.expect_call(Loc("foo"), sut.foo).will_once(Return(True))
        mock.visit_model_field_end.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_model_end.expect_call(Loc(), sut)
        with ordered(mock):
            sut.accept(mock, Loc())


class TestAnyLengthTypedTuple:

    class SUT(Model):
        foo: tuple[int, ...]

    @pytest.fixture(
        params=[
            ([], tuple(), []),
            ([1], (1,), [1]),
            ([1, 3.14, "5"], (1, 3, 5), [1, 3, 5]),
        ]
    )
    def data(self, request):
        return request.param

    @pytest.fixture(
        params=[
            (None, [ErrorFactory.invalid_type(common.loc, None, [tuple], [Sequence], [str, bytes])]),
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
        sut = self.SUT(foo=(1, 2))
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_sequence_begin.expect_call(Loc("foo"), sut.foo)
        mock.visit_number.expect_call(Loc("foo", 0), 1)
        mock.visit_number.expect_call(Loc("foo", 1), 2)
        mock.visit_sequence_end.expect_call(Loc("foo"), sut.foo)
        mock.visit_model_field_end.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_model_end.expect_call(Loc(), sut)
        sut.accept(mock, Loc())

    def test_when_visit_set_begin_returns_true_then_visiting_set_is_skipped(self, mock):
        sut = self.SUT(foo=(1, 3, 5))
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_sequence_begin.expect_call(Loc("foo"), sut.foo).will_once(Return(True))
        mock.visit_model_field_end.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_model_end.expect_call(Loc(), sut)
        with ordered(mock):
            sut.accept(mock, Loc())


class TestFixedLengthTypedTuple:

    class SUT(Model):
        foo: tuple[int, float, str]

    @pytest.fixture(
        params=[
            ([1, 3.14, "spam"], (1, 3.14, "spam"), [1, 3.14, "spam"]),
            (["1", "3.14", "spam"], (1, 3.14, "spam"), [1, 3.14, "spam"]),
        ]
    )
    def data(self, request):
        return request.param

    @pytest.fixture(
        params=[
            (None, [ErrorFactory.invalid_type(common.loc, None, [tuple], [Sequence], [str, bytes])]),
            ([], [ErrorFactory.invalid_tuple_length(common.loc, [], (int, float, str))]),
            ([1, 3.14], [ErrorFactory.invalid_tuple_length(common.loc, [1, 3.14], (int, float, str))]),
            (
                [1, 3.14, "spam", "more spam"],
                [ErrorFactory.invalid_tuple_length(common.loc, [1, 3.14, "spam", "more spam"], (int, float, str))],
            ),
            ([1, 3.14, 123], [ErrorFactory.invalid_type(common.loc + Loc(2), 123, [str])]),
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
        sut = self.SUT(foo=(1, 3.14, "spam"))
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_sequence_begin.expect_call(Loc("foo"), sut.foo)
        mock.visit_number.expect_call(Loc("foo", 0), 1)
        mock.visit_number.expect_call(Loc("foo", 1), 3.14)
        mock.visit_string.expect_call(Loc("foo", 2), "spam")
        mock.visit_sequence_end.expect_call(Loc("foo"), sut.foo)
        mock.visit_model_field_end.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_model_end.expect_call(Loc(), sut)
        sut.accept(mock, Loc())

    def test_when_visit_sequence_begin_returns_true_then_visiting_tuple_is_skipped(self, mock):
        sut = self.SUT(foo=(1, 3.14, "spam"))
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_sequence_begin.expect_call(Loc("foo"), sut.foo).will_once(Return(True))
        mock.visit_model_field_end.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_model_end.expect_call(Loc(), sut)
        with ordered(mock):
            sut.accept(mock, Loc())
