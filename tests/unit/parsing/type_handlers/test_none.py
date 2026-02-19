from typing import Any

import pytest

from mockify.api import ordered

from modelity._parsing.type_handlers.none import NoneTypeHandler
from modelity.error import ErrorFactory
from modelity.loc import Loc
from modelity.unset import Unset

from .common import loc, UUT


class TestNoneTypeHandler:

    @pytest.fixture
    def uut(self):
        return NoneTypeHandler()

    @pytest.mark.parametrize(
        "loc, value, expected_output, expected_errors",
        [
            (loc, None, None, []),
            (loc, 123, Unset, [ErrorFactory.invalid_value(loc, 123, [None])]),
        ],
    )
    def test_parse(self, uut: UUT, loc: Loc, value: Any, expected_output: Any, expected_errors: list):
        errors = []
        assert uut.parse(errors, loc, value) == expected_output
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "loc, value, visit_name",
        [
            (loc, None, "visit_none"),
        ],
    )
    def test_accept(self, uut: UUT, visitor_mock, loc, value, visit_name):
        getattr(visitor_mock, visit_name).expect_call(loc, value)
        with ordered(visitor_mock):
            uut.accept(visitor_mock, loc, value)
