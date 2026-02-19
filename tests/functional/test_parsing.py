import datetime
import enum
import ipaddress
import pathlib
from typing import (
    Annotated,
    Any,
    Literal,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Optional,
    Sequence,
    Set,
    Union,
)

import pytest

from modelity._parsing.type_handler_factory import create_type_handler
from modelity.base import Model
from modelity.constraints import Ge
from modelity.error import ErrorFactory
from modelity.exc import UnsupportedTypeError
from modelity.loc import Loc
from modelity.types import Deferred, LooseOptional, StrictOptional
from modelity.unset import Unset, UnsetType

LOC = Loc("foo")

NOW = datetime.datetime.now(datetime.timezone.utc)

DEFAULT_EXPECTED_DATETIME_FORMATS = [
    "YYYY-MM-DDThh:mm:ssZZZZ",
    "YYYY-MM-DDThh:mm:ss.ffffffZZZZ",
    "YYYY-MM-DDThh:mm:ss",
    "YYYY-MM-DDThh:mm:ss.ffffff",
    "YYYY-MM-DD hh:mm:ss ZZZZ",
    "YYYY-MM-DD hh:mm:ss.ffffff ZZZZ",
    "YYYY-MM-DD hh:mm:ss",
    "YYYY-MM-DD hh:mm:ss.ffffff",
    "YYYYMMDDThhmmssZZZZ",
    "YYYYMMDDThhmmss.ffffffZZZZ",
    "YYYYMMDDThhmmss",
    "YYYYMMDDThhmmss.ffffff",
    "YYYYMMDDhhmmssZZZZ",
    "YYYYMMDDhhmmss.ffffffZZZZ",
    "YYYYMMDDhhmmss",
    "YYYYMMDDhhmmss.ffffff",
]

DEFAULT_EXPECTED_DATE_FORMAT = ["YYYY-MM-DD"]


class EDummy(enum.Enum):
    FOO = 1
    BAR = 2


class User(Model):
    name: str
    age: int


@pytest.mark.parametrize(
    "typ, type_opts, input_value, expected_output_value, expected_errors",
    [
        # Any
        # ---
        (Any, {}, 1, 1, []),
        (Any, {}, 3.14, 3.14, []),
        (Any, {}, "spam", "spam", []),
        # type(None)
        # ----------
        (type(None), {}, None, None, []),
        (type(None), {}, 1, Unset, [ErrorFactory.invalid_value(LOC, 1, [None])]),
        # bool
        # ----
        (bool, {}, True, True, []),
        (bool, {}, False, False, []),
        (bool, {"true_literals": [1, "on"], "false_literals": [0, "off"]}, 1, True, []),
        (bool, {"true_literals": [1, "on"], "false_literals": [0, "off"]}, "on", True, []),
        (bool, {"true_literals": [1, "on"], "false_literals": [0, "off"]}, 0, False, []),
        (bool, {"true_literals": [1, "on"], "false_literals": [0, "off"]}, "off", False, []),
        (bool, {}, "spam", Unset, [ErrorFactory.parse_error(LOC, "spam", bool)]),
        # datetime.datetime
        # -----------------
        (datetime.datetime, {}, NOW, NOW, []),
        (
            datetime.datetime,
            {},
            "1999-01-31T11:22:33+0000",
            datetime.datetime(1999, 1, 31, 11, 22, 33, tzinfo=datetime.timezone.utc),
            [],
        ),
        (
            datetime.datetime,
            {},
            "1999-01-31T11:22:33.123456+0000",
            datetime.datetime(1999, 1, 31, 11, 22, 33, 123456, tzinfo=datetime.timezone.utc),
            [],
        ),
        (
            datetime.datetime,
            {},
            "1999-01-31T11:22:33",
            datetime.datetime(1999, 1, 31, 11, 22, 33),
            [],
        ),
        (
            datetime.datetime,
            {},
            "1999-01-31T11:22:33.123456",
            datetime.datetime(1999, 1, 31, 11, 22, 33, 123456),
            [],
        ),
        (
            datetime.datetime,
            {},
            "1999-01-31 11:22:33 +0000",
            datetime.datetime(1999, 1, 31, 11, 22, 33, tzinfo=datetime.timezone.utc),
            [],
        ),
        (
            datetime.datetime,
            {},
            "1999-01-31 11:22:33.123456 +0000",
            datetime.datetime(1999, 1, 31, 11, 22, 33, 123456, tzinfo=datetime.timezone.utc),
            [],
        ),
        (
            datetime.datetime,
            {},
            "1999-01-31 11:22:33",
            datetime.datetime(1999, 1, 31, 11, 22, 33),
            [],
        ),
        (
            datetime.datetime,
            {},
            "1999-01-31 11:22:33.123456",
            datetime.datetime(1999, 1, 31, 11, 22, 33, 123456),
            [],
        ),
        (
            datetime.datetime,
            {},
            "19990131T112233+0000",
            datetime.datetime(1999, 1, 31, 11, 22, 33, tzinfo=datetime.timezone.utc),
            [],
        ),
        (
            datetime.datetime,
            {},
            "19990131T112233.123456+0000",
            datetime.datetime(1999, 1, 31, 11, 22, 33, 123456, tzinfo=datetime.timezone.utc),
            [],
        ),
        (
            datetime.datetime,
            {},
            "19990131T112233",
            datetime.datetime(1999, 1, 31, 11, 22, 33),
            [],
        ),
        (
            datetime.datetime,
            {},
            "19990131T112233.123456",
            datetime.datetime(1999, 1, 31, 11, 22, 33, 123456),
            [],
        ),
        (
            datetime.datetime,
            {},
            "19990131112233+0000",
            datetime.datetime(1999, 1, 31, 11, 22, 33, tzinfo=datetime.timezone.utc),
            [],
        ),
        (
            datetime.datetime,
            {},
            "19990131112233.123456+0000",
            datetime.datetime(1999, 1, 31, 11, 22, 33, 123456, tzinfo=datetime.timezone.utc),
            [],
        ),
        (
            datetime.datetime,
            {},
            "19990131112233",
            datetime.datetime(1999, 1, 31, 11, 22, 33),
            [],
        ),
        (
            datetime.datetime,
            {},
            "19990131112233.123456",
            datetime.datetime(1999, 1, 31, 11, 22, 33, 123456),
            [],
        ),
        (
            datetime.datetime,
            {},
            "invalid",
            Unset,
            [ErrorFactory.invalid_datetime_format(LOC, "invalid", DEFAULT_EXPECTED_DATETIME_FORMATS)],
        ),
        # datetime.date
        # -------------
        (datetime.date, {}, NOW.date(), NOW.date(), []),
        (datetime.date, {}, "1999-01-31", datetime.date(1999, 1, 31), []),
        (
            datetime.date,
            {},
            "invalid",
            Unset,
            [ErrorFactory.invalid_date_format(LOC, "invalid", DEFAULT_EXPECTED_DATE_FORMAT)],
        ),
        # enum.Enum
        # ---------
        (EDummy, {}, EDummy.FOO, EDummy.FOO, []),
        (EDummy, {}, EDummy.BAR, EDummy.BAR, []),
        (EDummy, {}, 1, EDummy.FOO, []),
        (EDummy, {}, 2, EDummy.BAR, []),
        (EDummy, {}, "invalid", Unset, [ErrorFactory.invalid_enum_value(LOC, "invalid", EDummy)]),
        # typing.Literal
        # --------------
        (Literal[1, 3.14, "spam"], {}, 1, 1, []),
        (Literal[1, 3.14, "spam"], {}, 3.14, 3.14, []),
        (Literal[1, 3.14, "spam"], {}, "spam", "spam", []),
        (
            Literal[1, 3.14, "spam"],
            {},
            "invalid",
            Unset,
            [ErrorFactory.invalid_value(LOC, "invalid", [1, 3.14, "spam"])],
        ),
        # int
        # ---
        (int, {}, 1, 1, []),
        (int, {}, "2", 2, []),
        (int, {}, "invalid", Unset, [ErrorFactory.parse_error(LOC, "invalid", int)]),
        (int, {}, None, Unset, [ErrorFactory.parse_error(LOC, None, int)]),
        # float
        # -----
        (float, {}, 3.14, 3.14, []),
        (float, {}, "3.14", 3.14, []),
        (float, {}, "invalid", Unset, [ErrorFactory.parse_error(LOC, "invalid", float)]),
        (float, {}, None, Unset, [ErrorFactory.parse_error(LOC, None, float)]),
        # str
        # ---
        (str, {}, "spam", "spam", []),
        (str, {}, None, Unset, [ErrorFactory.invalid_type(LOC, None, [str])]),
        # bytes
        # -----
        (bytes, {}, b"spam", b"spam", []),
        (bytes, {}, None, Unset, [ErrorFactory.invalid_type(LOC, None, [bytes])]),
        # ipaddress.IPv4Address
        # ---------------------
        (ipaddress.IPv4Address, {}, ipaddress.IPv4Address("192.168.1.2"), ipaddress.IPv4Address("192.168.1.2"), []),
        (ipaddress.IPv4Address, {}, "192.168.1.2", ipaddress.IPv4Address("192.168.1.2"), []),
        (
            ipaddress.IPv4Address,
            {},
            "invalid",
            Unset,
            [ErrorFactory.parse_error(LOC, "invalid", ipaddress.IPv4Address, msg="Not a valid IPv4 address")],
        ),
        # ipaddress.IPv6Address
        # ---------------------
        (ipaddress.IPv6Address, {}, ipaddress.IPv6Address("ffff::1"), ipaddress.IPv6Address("ffff::1"), []),
        (ipaddress.IPv6Address, {}, "ffff::1", ipaddress.IPv6Address("ffff::1"), []),
        (
            ipaddress.IPv6Address,
            {},
            "invalid",
            Unset,
            [ErrorFactory.parse_error(LOC, "invalid", ipaddress.IPv6Address, msg="Not a valid IPv6 address")],
        ),
        # pathlib.Path
        # ------------
        (pathlib.Path, {}, pathlib.Path("/tmp"), pathlib.Path("/tmp"), []),
        (pathlib.Path, {}, "/tmp", pathlib.Path("/tmp"), []),
        (pathlib.Path, {}, None, Unset, [ErrorFactory.invalid_type(LOC, None, [pathlib.Path], [str])]),
        # Unset
        # -----
        (UnsetType, {}, Unset, Unset, []),
        (UnsetType, {}, None, Unset, [ErrorFactory.invalid_value(LOC, None, [Unset])]),
        # Model
        # -----
        (User, {}, User(name="John Doe", age=25), User(name="John Doe", age=25), []),
        (User, {}, {"name": "John Doe", "age": 25}, User(name="John Doe", age=25), []),
        (User, {}, "invalid", Unset, [ErrorFactory.invalid_type(LOC, "invalid", [User], [Mapping])]),
        (
            User,
            {},
            {},
            Unset,
            [ErrorFactory.required_missing(LOC + Loc("name")), ErrorFactory.required_missing(LOC + Loc("age"))],
        ),
        # MutableMapping
        # --------------
        (dict, {}, {}, {}, []),
        (dict, {}, {"one": 1}, {"one": 1}, []),
        (dict, {}, "invalid", Unset, [ErrorFactory.invalid_type(LOC, "invalid", [dict], [Mapping])]),
        (dict[Any, Any], {}, {}, {}, []),
        (dict[Any, Any], {}, {"one": 1}, {"one": 1}, []),
        (
            dict[Any, Any],
            {},
            "invalid",
            Unset,
            [ErrorFactory.invalid_type(LOC, "invalid", [dict[Any, Any]], [Mapping])],
        ),
        (MutableMapping, {}, {}, {}, []),
        (MutableMapping, {}, {"one": 1}, {"one": 1}, []),
        (
            MutableMapping,
            {},
            "invalid",
            Unset,
            [ErrorFactory.invalid_type(LOC, "invalid", [MutableMapping], [Mapping])],
        ),
        (MutableMapping[Any, Any], {}, {}, {}, []),
        (MutableMapping[Any, Any], {}, {"one": 1}, {"one": 1}, []),
        (
            MutableMapping[Any, Any],
            {},
            "invalid",
            Unset,
            [ErrorFactory.invalid_type(LOC, "invalid", [MutableMapping[Any, Any]], [Mapping])],
        ),
        (dict[str, int], {}, {}, {}, []),
        (dict[str, int], {}, {"one": 1}, {"one": 1}, []),
        (dict[str, int], {}, {"one": "2"}, {"one": 2}, []),
        (dict[str, int], {}, {1: "one"}, Unset, [ErrorFactory.invalid_type(LOC + Loc.irrelevant(), 1, [str])]),
        (dict[str, int], {}, {"one": "spam"}, Unset, [ErrorFactory.parse_error(LOC + Loc("one"), "spam", int)]),
        (MutableMapping[str, int], {}, {}, {}, []),
        (MutableMapping[str, int], {}, {"one": 1}, {"one": 1}, []),
        (MutableMapping[str, int], {}, {"one": "2"}, {"one": 2}, []),
        (
            MutableMapping[str, int],
            {},
            {1: "one"},
            Unset,
            [ErrorFactory.invalid_type(LOC + Loc.irrelevant(), 1, [str])],
        ),
        (
            MutableMapping[str, int],
            {},
            {"one": "spam"},
            Unset,
            [ErrorFactory.parse_error(LOC + Loc("one"), "spam", int)],
        ),
        # MutableSequence
        # ---------------
        (list, {}, [], [], []),
        (list, {}, [1, 3.14, "spam"], [1, 3.14, "spam"], []),
        (list, {}, "invalid", Unset, [ErrorFactory.invalid_type(LOC, "invalid", [list], [Sequence], [str, bytes])]),
        (list[Any], {}, [], [], []),
        (list[Any], {}, [1, 3.14, "spam"], [1, 3.14, "spam"], []),
        (
            list[Any],
            {},
            "invalid",
            Unset,
            [ErrorFactory.invalid_type(LOC, "invalid", [list[Any]], [Sequence], [str, bytes])],
        ),
        (MutableSequence, {}, [], [], []),
        (MutableSequence, {}, [1, 3.14, "spam"], [1, 3.14, "spam"], []),
        (
            MutableSequence,
            {},
            "invalid",
            Unset,
            [ErrorFactory.invalid_type(LOC, "invalid", [MutableSequence], [Sequence], [str, bytes])],
        ),
        (MutableSequence[Any], {}, [], [], []),
        (MutableSequence[Any], {}, [1, 3.14, "spam"], [1, 3.14, "spam"], []),
        (
            MutableSequence[Any],
            {},
            "invalid",
            Unset,
            [ErrorFactory.invalid_type(LOC, "invalid", [MutableSequence[Any]], [Sequence], [str, bytes])],
        ),
        (list[int], {}, ["1", "2"], [1, 2], []),
        (list[int], {}, ["1", "2", "spam"], Unset, [ErrorFactory.parse_error(LOC + Loc(2), "spam", int)]),
        (MutableSequence[int], {}, ["1", "2"], [1, 2], []),
        (MutableSequence[int], {}, ["1", "2", "spam"], Unset, [ErrorFactory.parse_error(LOC + Loc(2), "spam", int)]),
        # Sequence
        # --------
        (tuple, {}, [1, 3.14, "spam"], (1, 3.14, "spam"), []),
        (tuple, {}, "invalid", Unset, [ErrorFactory.invalid_type(LOC, "invalid", [tuple], [Sequence], [str, bytes])]),
        (tuple[Any, ...], {}, [1, 3.14, "spam"], (1, 3.14, "spam"), []),
        (
            tuple[Any, ...],
            {},
            "invalid",
            Unset,
            [ErrorFactory.invalid_type(LOC, "invalid", [tuple[Any, ...]], [Sequence], [str, bytes])],
        ),
        (Sequence, {}, [1, 3.14, "spam"], (1, 3.14, "spam"), []),
        (
            Sequence,
            {},
            "invalid",
            Unset,
            [ErrorFactory.invalid_type(LOC, "invalid", [Sequence], [Sequence], [str, bytes])],
        ),
        (Sequence[Any], {}, [1, 3.14, "spam"], (1, 3.14, "spam"), []),
        (
            Sequence[Any],
            {},
            "invalid",
            Unset,
            [ErrorFactory.invalid_type(LOC, "invalid", [Sequence[Any]], [Sequence], [str, bytes])],
        ),
        (tuple[int, ...], {}, [1, "2", "3"], (1, 2, 3), []),
        (tuple[int, ...], {}, [1, "2", "3", "spam"], Unset, [ErrorFactory.parse_error(LOC + Loc(3), "spam", int)]),
        (Sequence[int], {}, [1, "2", "3"], (1, 2, 3), []),
        (Sequence[int], {}, [1, "2", "3", "spam"], Unset, [ErrorFactory.parse_error(LOC + Loc(3), "spam", int)]),
        (tuple[int], {}, ["1"], (1,), []),
        (tuple[int, float, str], {}, ["1", "3.14", "spam"], (1, 3.14, "spam"), []),
        (
            tuple[int, float, str],
            {},
            ["foo", "3.14", "spam"],
            Unset,
            [ErrorFactory.parse_error(LOC + Loc(0), "foo", int)],
        ),
        (
            tuple[int, float, str],
            {},
            ["1", "3.14", "spam", "more spam"],
            Unset,
            [ErrorFactory.invalid_tuple_length(LOC, ("1", "3.14", "spam", "more spam"), (int, float, str))],
        ),
        # MutableSet
        # ----------
        (set, {}, [1, 3.14, "spam"], {1, 3.14, "spam"}, []),
        (set, {}, "invalid", Unset, [ErrorFactory.invalid_type(LOC, "invalid", [set], [Set, Sequence], [str, bytes])]),
        (MutableSet, {}, [1, 3.14, "spam"], {1, 3.14, "spam"}, []),
        (
            MutableSet,
            {},
            "invalid",
            Unset,
            [ErrorFactory.invalid_type(LOC, "invalid", [MutableSet], [Set, Sequence], [str, bytes])],
        ),
        (set[int], {}, [1, "2", "3"], {1, 2, 3}, []),
        (
            set[int],
            {},
            "invalid",
            Unset,
            [ErrorFactory.invalid_type(LOC, "invalid", [set[int]], [Set, Sequence], [str, bytes])],
        ),
        (set[int], {}, ["spam"], Unset, [ErrorFactory.parse_error(LOC + Loc.irrelevant(), "spam", int)]),
        (MutableSet[int], {}, [1, "2", "3"], {1, 2, 3}, []),
        (
            MutableSet[int],
            {},
            "invalid",
            Unset,
            [ErrorFactory.invalid_type(LOC, "invalid", [MutableSet[int]], [Set, Sequence], [str, bytes])],
        ),
        (MutableSet[int], {}, ["spam"], Unset, [ErrorFactory.parse_error(LOC + Loc.irrelevant(), "spam", int)]),
        # Annotated[T, ...]
        # -----------------
        (Annotated[int, Ge(0)], {}, 0, 0, []),
        (Annotated[int, Ge(0)], {}, "1", 1, []),
        (Annotated[int, Ge(0)], {}, -1, Unset, [ErrorFactory.out_of_range(LOC, -1, min_inclusive=0)]),
        # Deferred[T]
        # -----------
        (Deferred[int], {}, 1, 1, []),
        (Deferred[int], {}, "2", 2, []),
        (Deferred[int], {}, Unset, Unset, []),
        (Deferred[int], {}, "invalid", Unset, [ErrorFactory.parse_error(LOC, "invalid", int)]),
        (Deferred[int | float], {}, "3.14", 3.14, []),
        (Deferred[int | float], {}, "invalid", Unset, [ErrorFactory.invalid_type(LOC, "invalid", [int, float])]),
        (Deferred[Annotated[int, Ge(0)]], {}, "0", 0, []),
        (Deferred[Annotated[int, Ge(0)]], {}, "-1", Unset, [ErrorFactory.out_of_range(LOC, -1, min_inclusive=0)]),
        # Optional[T]
        # -----------
        (Optional[int], {}, 1, 1, []),
        (Optional[int], {}, "2", 2, []),
        (Optional[int], {}, None, None, []),
        (Optional[int], {}, "invalid", Unset, [ErrorFactory.parse_error(LOC, "invalid", int)]),
        (Optional[int], {}, Unset, Unset, [ErrorFactory.unset_not_allowed(LOC, Optional[int])]),
        # LooseOptional[T]
        # ----------------
        (LooseOptional[int], {}, Unset, Unset, []),
        (LooseOptional[int], {}, None, None, []),
        (LooseOptional[int], {}, 1, 1, []),
        (LooseOptional[int], {}, "2", 2, []),
        (LooseOptional[int], {}, "invalid", Unset, [ErrorFactory.parse_error(LOC, "invalid", int)]),
        # StrictOptional[T]
        # -----------------
        (StrictOptional[int], {}, Unset, Unset, []),
        (StrictOptional[int], {}, 1, 1, []),
        (StrictOptional[int], {}, "2", 2, []),
        (StrictOptional[int], {}, None, Unset, [ErrorFactory.none_not_allowed(LOC, StrictOptional[int])]),
        # Union[T, U, ...]
        # ----------------
        (Union[int, float], {}, 1, 1, []),
        (Union[int, float], {}, 3.14, 3.14, []),
        (Union[int, float], {}, "3", 3, []),
        (Union[int, float], {}, "3.14", 3.14, []),
        (Union[int, float], {}, "invalid", Unset, [ErrorFactory.invalid_type(LOC, "invalid", [int, float])]),
    ],
)
def test_parse(typ, type_opts, input_value, expected_output_value, expected_errors):
    type_handler = create_type_handler(typ, **type_opts)
    errors = []
    assert type_handler.parse(errors, LOC, input_value) == expected_output_value
    assert errors == expected_errors


def test_creating_handler_fails_for_unknown_types():
    with pytest.raises(UnsupportedTypeError) as excinfo:
        create_type_handler(object)
    assert excinfo.value.typ is object
