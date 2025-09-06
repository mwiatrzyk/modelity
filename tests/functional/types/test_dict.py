from typing import Any
import pytest

from mockify.api import Return, ordered

from modelity.error import ErrorFactory
from modelity.loc import Loc
from modelity.model import Model

from . import common


@pytest.mark.parametrize('typ', [
    dict,
    dict[Any, Any],
])
class TestAnyDict:

    @pytest.fixture
    def SUT(self, typ):

        class SUT(Model):
            foo: typ

        return SUT

    @pytest.fixture(autouse=True)
    def setup(self, SUT):
        self.SUT = SUT

    @pytest.fixture(params=[
        ({}, {}, {}),
        ({'foo': 1, 'bar': True}, {'foo': 1, 'bar': True}, {'foo': 1, 'bar': True}),
    ])
    def data(self, request):
        return request.param

    @pytest.fixture(params=[
        (None, [ErrorFactory.dict_parsing_error(common.loc, None)]),
    ])
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
        sut = self.SUT(foo={'one': 1, 'two': 'spam'})
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_mapping_begin.expect_call(Loc('foo'), sut.foo)
        mock.visit_any.expect_call(Loc('foo', 'one'), 1)
        mock.visit_any.expect_call(Loc('foo', 'two'), 'spam')
        mock.visit_mapping_end.expect_call(Loc('foo'), sut.foo)
        mock.visit_model_end.expect_call(Loc(), sut)
        with ordered(mock):
            sut.accept(mock, Loc())

    def test_when_visit_mapping_begin_returns_true_then_visiting_mapping_is_skipped(self, mock):
        sut = self.SUT(foo={'one': 1})
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_mapping_begin.expect_call(Loc('foo'), sut.foo).will_once(Return(True))
        mock.visit_model_end.expect_call(Loc(), sut)
        with ordered(mock):
            sut.accept(mock, Loc())


class TestTypedDict:

    class SUT(Model):
        foo: dict[str, int]

    @pytest.fixture(params=[
        ({}, {}, {}),
        ({'one': 1}, {'one': 1}, {'one': 1}),
        ({'two': '2'}, {'two': 2}, {'two': 2}),
    ])
    def data(self, request):
        return request.param

    @pytest.fixture(params=[
        (None, [ErrorFactory.dict_parsing_error(common.loc, None)]),
        ({1: 1}, [ErrorFactory.string_value_required(common.loc + Loc.irrelevant(), 1)]),
        ({'one': 'spam'}, [ErrorFactory.integer_parsing_error(common.loc + Loc('one'), 'spam')]),
    ])
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
        sut = self.SUT(foo={'one': 1})
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_mapping_begin.expect_call(Loc('foo'), sut.foo)
        mock.visit_number.expect_call(Loc('foo', 'one'), 1)
        mock.visit_mapping_end.expect_call(Loc('foo'), sut.foo)
        mock.visit_model_end.expect_call(Loc(), sut)
        with ordered(mock):
            sut.accept(mock, Loc())

    def test_when_visit_mapping_begin_returns_true_then_visiting_mapping_is_skipped(self, mock):
        sut = self.SUT(foo={'one': 1})
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_mapping_begin.expect_call(Loc('foo'), sut.foo).will_once(Return(True))
        mock.visit_model_end.expect_call(Loc(), sut)
        with ordered(mock):
            sut.accept(mock, Loc())
