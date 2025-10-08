import pytest

from mockify.api import ordered, Return

from modelity.error import ErrorFactory
from modelity.loc import Loc
from modelity.model import Model

from tests.functional.types import common


class TestAnySet:

    class SUT(Model):
        foo: set

    @pytest.fixture(
        params=[
            ([], set(), []),
            ([1], {1}, [1]),
            ([1, 3.14, "spam"], {1, 3.14, "spam"}, lambda x: set(x) == {1, 3.14, "spam"}),
        ]
    )
    def data(self, request):
        return request.param

    @pytest.fixture(
        params=[
            (None, [ErrorFactory.set_parsing_error(common.loc, None)]),
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
        sut = self.SUT(foo={1, 3.14, "spam"})
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_set_begin.expect_call(Loc("foo"), sut.foo)
        mock.visit_any.expect_call(Loc("foo", "_"), 1)
        mock.visit_any.expect_call(Loc("foo", "_"), 3.14)
        mock.visit_any.expect_call(Loc("foo", "_"), "spam")
        mock.visit_set_end.expect_call(Loc("foo"), sut.foo)
        mock.visit_model_field_end.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_model_end.expect_call(Loc(), sut)
        sut.accept(mock, Loc())

    def test_when_visit_set_begin_returns_true_then_visiting_set_is_skipped(self, mock):
        sut = self.SUT(foo={1, 3.14, "spam"})
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_set_begin.expect_call(Loc("foo"), sut.foo).will_once(Return(True))
        mock.visit_model_field_end.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_model_end.expect_call(Loc(), sut)
        with ordered(mock):
            sut.accept(mock, Loc())


class TestTypedSet:

    class SUT(Model):
        foo: set[int]

    @pytest.fixture(
        params=[
            ([], set(), []),
            ([1], {1}, [1]),
            ([1, 2.71, "3"], {1, 2, 3}, lambda x: set(x) == {1, 2, 3}),
        ]
    )
    def data(self, request):
        return request.param

    @pytest.fixture(
        params=[
            (None, [ErrorFactory.set_parsing_error(common.loc, None)]),
            ([1, "spam"], [ErrorFactory.integer_parsing_error(common.loc + Loc.irrelevant(), "spam")]),
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
        sut = self.SUT(foo={1, 2, 3})
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_set_begin.expect_call(Loc("foo"), sut.foo)
        mock.visit_number.expect_call(Loc("foo", "_"), 1)
        mock.visit_number.expect_call(Loc("foo", "_"), 2)
        mock.visit_number.expect_call(Loc("foo", "_"), 3)
        mock.visit_set_end.expect_call(Loc("foo"), sut.foo)
        mock.visit_model_field_end.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_model_end.expect_call(Loc(), sut)
        sut.accept(mock, Loc())

    def test_when_visit_set_begin_returns_true_then_visiting_set_is_skipped(self, mock):
        sut = self.SUT(foo={1, 2, 3})
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_set_begin.expect_call(Loc("foo"), sut.foo).will_once(Return(True))
        mock.visit_model_field_end.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_model_end.expect_call(Loc(), sut)
        with ordered(mock):
            sut.accept(mock, Loc())
