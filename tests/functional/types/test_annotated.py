from typing import Annotated

import pytest

from mockify.api import ordered, Return

from modelity.constraints import Ge
from modelity.error import ErrorFactory
from modelity.loc import Loc
from modelity.model import Model

from tests.functional.types import common


class TestAnnotated:

    class SUT(Model):
        foo: Annotated[int, Ge(0)]

    @pytest.fixture(
        params=[
            (0, 0, 0),
            ("1", 1, 1),
        ]
    )
    def data(self, request):
        return request.param

    @pytest.fixture(
        params=[
            (None, [ErrorFactory.parse_error(common.loc, None, int)]),
            ("spam", [ErrorFactory.parse_error(common.loc, "spam", int)]),
            (-1, [ErrorFactory.out_of_range(common.loc, -1, min_inclusive=0)]),
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
        sut = self.SUT(foo=0)
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_scalar.expect_call(Loc("foo"), 0)
        mock.visit_model_field_end.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_model_end.expect_call(Loc(), sut)
        sut.accept(mock, Loc())

    def test_when_visit_model_field_begin_returns_true_then_field_is_skipped(self, mock):
        sut = self.SUT(foo=0)
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"]).will_once(Return(True))
        mock.visit_model_end.expect_call(Loc(), sut)
        with ordered(mock):
            sut.accept(mock, Loc())
