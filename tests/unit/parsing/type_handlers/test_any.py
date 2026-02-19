from typing import Any

import pytest

from mockify.api import ordered

from modelity._parsing.type_handlers.any import AnyTypeHandler
from modelity.loc import Loc
from modelity.unset import Unset

from .common import loc, UUT


class TestAnyTypeHandler:

    @pytest.fixture
    def uut(self):
        return AnyTypeHandler()

    @pytest.mark.parametrize(
        "loc, value, expected_output, expected_errors",
        [
            (loc, Unset, Unset, []),
            (loc, None, None, []),
            (loc, 123, 123, []),
            (loc, 3.14, 3.14, []),
            (loc, "spam", "spam", []),
        ],
    )
    def test_parse(self, uut: UUT, loc: Loc, value: Any, expected_output: Any, expected_errors: list):
        errors = []
        assert uut.parse(errors, loc, value) == expected_output
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "loc, value, visit_name",
        [
            (loc, Unset, "visit_unset"),
            (loc, None, "visit_none"),
            (loc, 123, "visit_any"),
            (loc, "spam", "visit_any"),
        ],
    )
    def test_accept(self, uut: UUT, visitor_mock, loc, value, visit_name):
        getattr(visitor_mock, visit_name).expect_call(loc, value)
        with ordered(visitor_mock):
            uut.accept(visitor_mock, loc, value)
