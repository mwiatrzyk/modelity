# TODO: Refactor all other tests to use this base test case suite instead of
# common.py; it plays well with Pytest and allows to extend test suite for all
# types simply by adding new tests.

import pytest

from modelity.api import validate, dump
from modelity.exc import ParsingError, ValidationError


class ValidInputTestBase:

    @pytest.fixture(autouse=True)
    def setup(self, SUT, given_input, expected_output, expected_dump_output):
        self.SUT = SUT
        self.given_input = given_input
        self.expected_output = expected_output
        self.expected_dump_output = expected_dump_output

    def test_construct_successfully(self):
        sut = self.SUT(foo=self.given_input)
        assert sut.foo == self.expected_output

    def test_assign_successfully(self):
        sut = self.SUT()
        sut.foo = self.given_input
        assert sut.foo == self.expected_output

    def test_validate_successfully(self):
        sut = self.SUT()
        sut.foo = self.given_input
        validate(sut)
        assert sut.foo == self.expected_output

    def test_dump_successfully(self):
        sut = self.SUT()
        sut.foo = self.given_input
        assert dump(sut) == {"foo": self.expected_dump_output}


class ParsingErrorTestBase:

    @pytest.fixture(autouse=True)
    def setup(self, SUT, given_input, expected_errors):
        self.SUT = SUT
        self.given_input = given_input
        self.expected_errors = expected_errors

    def test_constructing_fails_for_invalid_input(self):
        with pytest.raises(ParsingError) as excinfo:
            self.SUT(foo=self.given_input)
        assert excinfo.value.errors == tuple(self.expected_errors)

    def test_assignment_fails_for_invalid_input(self):
        uut = self.SUT()
        with pytest.raises(ParsingError) as excinfo:
            uut.foo = self.given_input
        assert excinfo.value.errors == tuple(self.expected_errors)


class ValidationErrorTestBase:

    @pytest.fixture(autouse=True)
    def setup(self, SUT, given_input, expected_errors):
        self.SUT = SUT
        self.given_input = given_input
        self.expected_errors = expected_errors

    def test_validation_fails_if_value_breaks_model_constraints(self):
        sut = self.SUT()
        sut.foo = self.given_input
        with pytest.raises(ValidationError) as excinfo:
            validate(sut)
        assert excinfo.value.errors == tuple(self.expected_errors)
