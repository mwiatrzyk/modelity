from typing import Mapping

import pytest

from modelity._parsing.type_handlers.model import ModelTypeHandler
from modelity.base import Model
from modelity.error import ErrorFactory
from modelity.loc import Loc
from modelity.unset import Unset

from .common import loc


class Dummy(Model):
    a: int


class TestModelTypeHandler:
    UUT = ModelTypeHandler

    @pytest.fixture
    def uut(self):
        return ModelTypeHandler(Dummy)

    @pytest.mark.parametrize("value", [Dummy(a=123)])
    def test_parse_returns_given_value_if_already_instance_of_given_model(self, uut: UUT, value):
        errors = []
        assert uut.parse(errors, loc, value) is value
        assert len(errors) == 0

    def test_parse_fails_if_input_value_is_neither_model_nor_mapping(self, uut: UUT):
        errors = []
        assert uut.parse(errors, loc, "spam") is Unset
        assert errors == [ErrorFactory.invalid_type(loc, "spam", [Dummy], [Mapping])]

    @pytest.mark.parametrize(
        "value, expected_result, expected_errors",
        [
            ({"a": 123}, Dummy(a=123), []),
            ({"a": "456"}, Dummy(a=456), []),
            ({"a": "spam"}, Unset, [ErrorFactory.parse_error(loc + Loc("a"), "spam", int)]),
        ],
    )
    def test_parse_mapping_value(self, uut: UUT, value, expected_result, expected_errors):
        errors = []
        assert uut.parse(errors, loc, value) == expected_result
        assert errors == expected_errors

    @pytest.mark.parametrize("value", [Dummy(a=123)])
    def test_accept_calls_model_accept_if_instance_match(self, uut: UUT, value: Dummy, visitor_mock):
        visitor_mock.visit_model_begin.expect_call(loc, value)
        visitor_mock.visit_model_field_begin.expect_call(loc + Loc("a"), value.a, value.__model_fields__["a"])
        visitor_mock.visit_scalar.expect_call(loc + Loc("a"), value.a)
        visitor_mock.visit_model_field_end.expect_call(loc + Loc("a"), value.a, value.__model_fields__["a"])
        visitor_mock.visit_model_end.expect_call(loc, value)
        uut.accept(visitor_mock, loc, value)

    @pytest.mark.parametrize("value", ["spam"])
    def test_accept_calls_visit_any_if_instance_does_not_match(self, uut: UUT, value, visitor_mock):
        visitor_mock.visit_any.expect_call(loc, value)
        uut.accept(visitor_mock, loc, value)
