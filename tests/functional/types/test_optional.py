from typing import Optional

import pytest

from mockify.api import ordered

from modelity.helpers import validate
from modelity.model import Model
from modelity.error import ErrorFactory
from modelity.loc import Loc
from modelity.types import LooseOptional, StrictOptional
from modelity.unset import Unset, UnsetType

from .base import ParsingErrorTestBase, ValidationErrorTestBase, ValidInputTestBase

loc = Loc("foo")


@pytest.fixture
def field_info():
    return None


@pytest.mark.parametrize("field_type", [Optional[int]])
class TestOptional:

    @pytest.mark.parametrize(
        "given_input, expected_output, expected_dump_output",
        [
            (1, 1, 1),
            ("2", 2, 2),
            (None, None, None),
        ],
    )
    class TestValidInput(ValidInputTestBase):
        pass

    @pytest.mark.parametrize(
        "given_input, expected_errors",
        [
            ("spam", [ErrorFactory.parse_error(loc, "spam", int)]),
        ],
    )
    class TestParsingErrors(ParsingErrorTestBase):
        pass

    @pytest.mark.parametrize(
        "given_input, expected_errors",
        [
            (Unset, [ErrorFactory.unset_not_allowed(loc, Optional[int])]),
        ],
    )
    class TestValidationErrors(ValidationErrorTestBase):
        pass

    @pytest.mark.parametrize(
        "given_input, expected_output, visit_name",
        [
            (1, 1, "visit_scalar"),
            ("2", 2, "visit_scalar"),
            (None, None, "visit_none"),
        ],
    )
    def test_accept_visitor(self, sut: Model, mock, given_input, expected_output, visit_name):
        sut.foo = given_input
        validate(sut)
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), expected_output, sut.__model_fields__["foo"])
        getattr(mock, visit_name).expect_call(Loc("foo"), expected_output)
        mock.visit_model_field_end.expect_call(Loc("foo"), expected_output, sut.__model_fields__["foo"])
        mock.visit_model_end.expect_call(Loc(), sut)
        with ordered(mock):
            sut.accept(mock, Loc())


@pytest.mark.parametrize("field_type", [StrictOptional[int]])
class TestStrictOptional:

    @pytest.mark.parametrize(
        "given_input, expected_output, expected_dump_output",
        [
            (1, 1, 1),
            ("2", 2, 2),
            (Unset, Unset, Unset),
        ],
    )
    class TestValidInput(ValidInputTestBase):
        pass

    @pytest.mark.parametrize(
        "given_input, expected_errors",
        [
            ("spam", [ErrorFactory.parse_error(loc, "spam", int)]),
            (None, [ErrorFactory.none_not_allowed(loc, StrictOptional[int])]),
        ],
    )
    class TestParsingErrors(ParsingErrorTestBase):
        pass

    @pytest.mark.parametrize(
        "given_input, expected_output, visit_name",
        [
            (1, 1, "visit_scalar"),
            ("2", 2, "visit_scalar"),
            (Unset, Unset, "visit_unset"),
        ],
    )
    def test_accept_visitor(self, sut: Model, mock, given_input, expected_output, visit_name):
        sut.foo = given_input
        validate(sut)
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), expected_output, sut.__model_fields__["foo"])
        getattr(mock, visit_name).expect_call(Loc("foo"), expected_output)
        mock.visit_model_field_end.expect_call(Loc("foo"), expected_output, sut.__model_fields__["foo"])
        mock.visit_model_end.expect_call(Loc(), sut)
        with ordered(mock):
            sut.accept(mock, Loc())


@pytest.mark.parametrize("field_type", [LooseOptional[int]])
class TestLooseOptional:

    @pytest.mark.parametrize(
        "given_input, expected_output, expected_dump_output",
        [
            (1, 1, 1),
            ("2", 2, 2),
            (Unset, Unset, Unset),
            (None, None, None),
        ],
    )
    class TestValidInput(ValidInputTestBase):
        pass

    @pytest.mark.parametrize(
        "given_input, expected_errors",
        [
            ("spam", [ErrorFactory.invalid_type(loc, "spam", [int, type(None), UnsetType])]),
        ],
    )
    class TestParsingErrors(ParsingErrorTestBase):
        pass

    @pytest.mark.parametrize(
        "given_input, expected_output, visit_name",
        [
            (1, 1, "visit_scalar"),
            ("2", 2, "visit_scalar"),
            (None, None, "visit_none"),
            (Unset, Unset, "visit_unset"),
        ],
    )
    def test_accept_visitor(self, sut: Model, mock, given_input, expected_output, visit_name):
        sut.foo = given_input
        validate(sut)
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), expected_output, sut.__model_fields__["foo"])
        getattr(mock, visit_name).expect_call(Loc("foo"), expected_output)
        mock.visit_model_field_end.expect_call(Loc("foo"), expected_output, sut.__model_fields__["foo"])
        mock.visit_model_end.expect_call(Loc(), sut)
        with ordered(mock):
            sut.accept(mock, Loc())
