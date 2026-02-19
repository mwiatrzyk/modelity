import datetime
import enum
import ipaddress
import pathlib
from typing import Any, Literal

import pytest

from mockify.api import ordered

from modelity._parsing.type_handlers.scalar import (
    BoolTypeHandler,
    BytesTypeHandler,
    DateTimeTypeHandler,
    EnumTypeHandler,
    IPAddressTypeHandler,
    LiteralTypeHandler,
    NumericTypeHandler,
    PathTypeHandler,
    StrTypeHandler,
)
from modelity.error import ErrorFactory
from modelity.unset import Unset
from modelity.loc import Loc

from .common import loc, UUT

now = datetime.datetime.now(datetime.timezone.utc)


class TestBoolTypeHandler:

    @pytest.fixture
    def true_literals(self):
        return None

    @pytest.fixture
    def false_literals(self):
        return None

    @pytest.fixture
    def uut(self, true_literals, false_literals):
        return BoolTypeHandler(true_literals=true_literals, false_literals=false_literals)

    @pytest.mark.parametrize(
        "true_literals, false_literals, loc, value, expected_output, expected_errors",
        [
            (None, None, loc, True, True, []),
            (None, None, loc, False, False, []),
            ([1, "on"], None, loc, 1, True, []),
            ([1, "on"], None, loc, "on", True, []),
            (None, [0, "off"], loc, 0, False, []),
            (None, [0, "off"], loc, "off", False, []),
            (None, None, loc, 123, Unset, [ErrorFactory.parse_error(loc, 123, bool)]),
        ],
    )
    def test_parse(self, uut: UUT, loc: Loc, value: Any, expected_output: Any, expected_errors: list):
        errors = []
        assert uut.parse(errors, loc, value) == expected_output
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "loc, value, visit_name",
        [
            (loc, True, "visit_scalar"),
            (loc, False, "visit_scalar"),
        ],
    )
    def test_accept(self, uut: UUT, visitor_mock, loc, value, visit_name):
        getattr(visitor_mock, visit_name).expect_call(loc, value)
        with ordered(visitor_mock):
            uut.accept(visitor_mock, loc, value)


class TestDateTimeTypeHandler:

    @pytest.fixture
    def uut(self, typ, expected_formats):
        return DateTimeTypeHandler(typ, expected_formats)

    @pytest.mark.parametrize(
        "typ, expected_formats, loc, value, expected_output, expected_errors",
        [
            (datetime.datetime, ["YYYY-MM-DD hh:mm:ss.ffffff ZZZZ"], loc, now, now, []),
            (
                datetime.datetime,
                ["YYYY-MM-DD hh:mm:ss.ffffffZZZZ"],
                loc,
                "2026-01-31 11:22:33.444444+0000",
                datetime.datetime(2026, 1, 31, 11, 22, 33, 444444, datetime.timezone(datetime.timedelta(0))),
                [],
            ),
            (
                datetime.datetime,
                ["YYYY-MM-DD hh:mm:ss.ffffff ZZZZ"],
                loc,
                123,
                Unset,
                [ErrorFactory.invalid_type(loc, 123, [datetime.datetime], [str])],
            ),
            (
                datetime.datetime,
                ["YYYY-MM-DD hh:mm:ss.ffffff ZZZZ"],
                loc,
                "spam",
                Unset,
                [ErrorFactory.invalid_datetime_format(loc, "spam", ["YYYY-MM-DD hh:mm:ss.ffffff ZZZZ"])],
            ),
            (datetime.date, ["YYYY-MM-DD"], loc, now.date(), now.date(), []),
            (
                datetime.date,
                ["YYYY-MM-DD"],
                loc,
                "2026-01-31",
                datetime.date(2026, 1, 31),
                [],
            ),
            (
                datetime.date,
                ["YYYY-MM-DD"],
                loc,
                123,
                Unset,
                [ErrorFactory.invalid_type(loc, 123, [datetime.date], [str])],
            ),
            (
                datetime.date,
                ["YYYY-MM-DD"],
                loc,
                "spam",
                Unset,
                [ErrorFactory.invalid_date_format(loc, "spam", ["YYYY-MM-DD"])],
            ),
        ],
    )
    def test_parse(self, uut: UUT, loc: Loc, value: Any, expected_output: Any, expected_errors: list):
        errors = []
        assert uut.parse(errors, loc, value) == expected_output
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "typ, expected_formats, loc, value, visit_name",
        [
            (datetime.datetime, ["YYYY-MM-DD hh:mm:ss"], loc, now, "visit_scalar"),
            (datetime.date, ["YYYY-MM-DD"], loc, now.date(), "visit_scalar"),
        ],
    )
    def test_accept(self, uut: UUT, visitor_mock, loc, value, visit_name):
        getattr(visitor_mock, visit_name).expect_call(loc, value)
        with ordered(visitor_mock):
            uut.accept(visitor_mock, loc, value)


class TestEnumTypeHandler:

    class Dummy(enum.Enum):
        FOO = 1
        BAR = 2

    @pytest.fixture
    def uut(self):
        return EnumTypeHandler(self.Dummy)

    @pytest.mark.parametrize(
        "loc, value, expected_output, expected_errors",
        [
            (loc, Dummy.FOO, Dummy.FOO, []),
            (loc, 1, Dummy.FOO, []),
            (loc, 2, Dummy.BAR, []),
            (loc, "spam", Unset, [ErrorFactory.invalid_enum_value(loc, "spam", Dummy)]),
        ],
    )
    def test_parse(self, uut: UUT, loc: Loc, value: Any, expected_output: Any, expected_errors: list):
        errors = []
        assert uut.parse(errors, loc, value) == expected_output
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "loc, value, visit_name",
        [
            (loc, Dummy.FOO, "visit_scalar"),
            (loc, Dummy.BAR, "visit_scalar"),
        ],
    )
    def test_accept(self, uut: UUT, visitor_mock, loc, value, visit_name):
        getattr(visitor_mock, visit_name).expect_call(loc, value)
        with ordered(visitor_mock):
            uut.accept(visitor_mock, loc, value)


class TestLiteralTypeHandler:
    Dummy = Literal[1, 2.71, "spam"]

    @pytest.fixture
    def uut(self):
        return LiteralTypeHandler(self.Dummy)

    def test_if_not_literal_then_constructor_raises_error(self):
        with pytest.raises(TypeError):
            LiteralTypeHandler(int)

    @pytest.mark.parametrize(
        "loc, value, expected_output, expected_errors",
        [
            (loc, 1, 1, []),
            (loc, 2.71, 2.71, []),
            (loc, "spam", "spam", []),
            (loc, "invalid", Unset, [ErrorFactory.invalid_value(loc, "invalid", [1, 2.71, "spam"])]),
        ],
    )
    def test_parse(self, uut: UUT, loc: Loc, value: Any, expected_output: Any, expected_errors: list):
        errors = []
        assert uut.parse(errors, loc, value) == expected_output
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "loc, value, visit_name",
        [
            (loc, 1, "visit_scalar"),
            (loc, 2.71, "visit_scalar"),
            (loc, "spam", "visit_scalar"),
        ],
    )
    def test_accept(self, uut: UUT, visitor_mock, loc, value, visit_name):
        getattr(visitor_mock, visit_name).expect_call(loc, value)
        with ordered(visitor_mock):
            uut.accept(visitor_mock, loc, value)


class TestNumericTypeHandler:

    @pytest.fixture
    def uut(self, typ):
        return NumericTypeHandler(typ)

    @pytest.mark.parametrize(
        "typ, loc, value, expected_output, expected_errors",
        [
            (int, loc, 1, 1, []),
            (int, loc, "2", 2, []),
            (int, loc, "three", Unset, [ErrorFactory.parse_error(loc, "three", int)]),
            (float, loc, 1, 1.0, []),
            (float, loc, "2.71", 2.71, []),
            (float, loc, "three", Unset, [ErrorFactory.parse_error(loc, "three", float)]),
        ],
    )
    def test_parse(self, uut: UUT, loc: Loc, value: Any, expected_output: Any, expected_errors: list):
        errors = []
        assert uut.parse(errors, loc, value) == expected_output
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "typ, loc, value, visit_name",
        [
            (int, loc, 1, "visit_scalar"),
            (float, loc, 2.71, "visit_scalar"),
        ],
    )
    def test_accept(self, uut: UUT, visitor_mock, loc, value, visit_name):
        getattr(visitor_mock, visit_name).expect_call(loc, value)
        with ordered(visitor_mock):
            uut.accept(visitor_mock, loc, value)


class TestStrTypeHandler:

    @pytest.fixture
    def uut(self):
        return StrTypeHandler()

    @pytest.mark.parametrize(
        "loc, value, expected_output, expected_errors",
        [
            (loc, "spam", "spam", []),
            (loc, 123, Unset, [ErrorFactory.invalid_type(loc, 123, [str])]),
        ],
    )
    def test_parse(self, uut: UUT, loc: Loc, value: Any, expected_output: Any, expected_errors: list):
        errors = []
        assert uut.parse(errors, loc, value) == expected_output
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "loc, value, visit_name",
        [
            (loc, "spam", "visit_scalar"),
        ],
    )
    def test_accept(self, uut: UUT, visitor_mock, loc, value, visit_name):
        getattr(visitor_mock, visit_name).expect_call(loc, value)
        with ordered(visitor_mock):
            uut.accept(visitor_mock, loc, value)


class TestBytesTypeHandler:

    @pytest.fixture
    def uut(self):
        return BytesTypeHandler()

    @pytest.mark.parametrize(
        "loc, value, expected_output, expected_errors",
        [
            (loc, b"spam", b"spam", []),
            (loc, 123, Unset, [ErrorFactory.invalid_type(loc, 123, [bytes])]),
        ],
    )
    def test_parse(self, uut: UUT, loc: Loc, value: Any, expected_output: Any, expected_errors: list):
        errors = []
        assert uut.parse(errors, loc, value) == expected_output
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "loc, value, visit_name",
        [
            (loc, b"spam", "visit_scalar"),
        ],
    )
    def test_accept(self, uut: UUT, visitor_mock, loc, value, visit_name):
        getattr(visitor_mock, visit_name).expect_call(loc, value)
        with ordered(visitor_mock):
            uut.accept(visitor_mock, loc, value)


class TestIPAddressTypeHandler:

    @pytest.fixture
    def uut(self, typ):
        return IPAddressTypeHandler(typ)

    @pytest.mark.parametrize(
        "typ, loc, value, expected_output, expected_errors",
        [
            (
                ipaddress.IPv4Address,
                loc,
                ipaddress.IPv4Address("192.168.1.1"),
                ipaddress.IPv4Address("192.168.1.1"),
                [],
            ),
            (ipaddress.IPv4Address, loc, "192.168.1.1", ipaddress.IPv4Address("192.168.1.1"), []),
            (
                ipaddress.IPv4Address,
                loc,
                None,
                Unset,
                [ErrorFactory.parse_error(loc, None, ipaddress.IPv4Address, msg="Not a valid IPv4 address")],
            ),
            (ipaddress.IPv6Address, loc, ipaddress.IPv6Address("ffff::1"), ipaddress.IPv6Address("ffff::1"), []),
            (ipaddress.IPv6Address, loc, "ffff::1", ipaddress.IPv6Address("ffff::1"), []),
            (
                ipaddress.IPv6Address,
                loc,
                None,
                Unset,
                [ErrorFactory.parse_error(loc, None, ipaddress.IPv6Address, msg="Not a valid IPv6 address")],
            ),
        ],
    )
    def test_parse(self, uut: UUT, loc: Loc, value: Any, expected_output: Any, expected_errors: list):
        errors = []
        assert uut.parse(errors, loc, value) == expected_output
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "typ, loc, value, visit_name",
        [
            (ipaddress.IPv4Address, loc, ipaddress.IPv4Address("192.168.1.1"), "visit_scalar"),
            (ipaddress.IPv6Address, loc, ipaddress.IPv6Address("ffff::1"), "visit_scalar"),
        ],
    )
    def test_accept(self, uut: UUT, visitor_mock, loc, value, visit_name):
        getattr(visitor_mock, visit_name).expect_call(loc, value)
        with ordered(visitor_mock):
            uut.accept(visitor_mock, loc, value)


class TestPathTypeHandler:

    @pytest.fixture
    def uut(self):
        return PathTypeHandler()

    @pytest.mark.parametrize(
        "loc, value, expected_output, expected_errors",
        [
            (loc, "/tmp/spam", pathlib.Path("/tmp/spam"), []),
            (loc, pathlib.Path("/tmp/spam"), pathlib.Path("/tmp/spam"), []),
            (loc, 123, Unset, [ErrorFactory.invalid_type(loc, 123, [pathlib.Path], [str])]),
        ],
    )
    def test_parse(self, uut: UUT, loc: Loc, value: Any, expected_output: Any, expected_errors: list):
        errors = []
        assert uut.parse(errors, loc, value) == expected_output
        assert errors == expected_errors

    @pytest.mark.parametrize(
        "loc, value, visit_name",
        [
            (loc, pathlib.Path("/tmp/spam"), "visit_scalar"),
        ],
    )
    def test_accept(self, uut: UUT, visitor_mock, loc, value, visit_name):
        getattr(visitor_mock, visit_name).expect_call(loc, value)
        with ordered(visitor_mock):
            uut.accept(visitor_mock, loc, value)
