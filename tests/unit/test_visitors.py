import datetime
import enum
import ipaddress
from typing import Any, Optional, cast
import pytest

from modelity.interface import IModel, IModelVisitor
from modelity.loc import Loc
from modelity.model import Model
from modelity.types import Deferred
from modelity.unset import Unset
from modelity.visitors import DumpVisitor, JsonDumpVisitorProxy


class EOption(enum.Enum):
    ONE = 1
    TWO = 2


class Nested(Model):
    bar: Deferred[int] = Unset


class NestedWithOptional(Model):
    bar: Optional[int]


@pytest.fixture
def model_class(typ):

    class Dummy(Model):
        foo: Deferred[typ] = Unset  # type: ignore

    return Dummy


@pytest.fixture
def model(model_class, input_value):
    return model_class(foo=input_value)


class TestDumpVisitor:

    @pytest.mark.parametrize(
        "typ, input_value, expected_dump_output",
        [
            (dict, {}, {}),
            (dict, {"a": 1}, {"a": 1}),
            (dict, {"a": 1}, {"a": 1}),
            (dict[str, int], {"one": 1, "two": 2}, {"one": 1, "two": 2}),
            (dict[str, Any], {"one": 1, "two": 3.14, "three": "spam"}, {"one": 1, "two": 3.14, "three": "spam"}),
            (list, [1, "2", 3.14, True, None], [1, "2", 3.14, True, None]),
            (list, [1, "2", 3.14, True, None, {"a": 123}], [1, "2", 3.14, True, None, {"a": 123}]),
            (list[Any], [1, "2", 3.14, True, None, {"a": 123}], [1, "2", 3.14, True, None, {"a": 123}]),
            (list[int], [1, "2"], [1, 2]),
            (list[list[int]], [[1], ["2"]], [[1], [2]]),
            (set, [], set()),
            (set, [1, "2", 3.14], {1, "2", 3.14}),
            (set[int], [1, "2", 3.14], {1, 2, 3}),
            (tuple, [], tuple()),
            (tuple[int, ...], [1, "2", 3.14], tuple([1, 2, 3])),
            (tuple[int, str, float], [1, "2", 3.14], tuple([1, "2", 3.14])),
            (int, "2", 2),
            (int, Unset, Unset),
            (Optional[int], 123, 123),
            (Optional[int], None, None),
            (Nested, {"bar": "123"}, {"bar": 123}),
        ],
    )
    def test_accept_visitor(self, model: IModel, expected_dump_output):
        out = {}
        visitor = cast(IModelVisitor, DumpVisitor(out))
        model.accept(visitor, Loc())
        assert out == {"foo": expected_dump_output}


class TestJsonDumpVisitorProxy:

    @pytest.mark.parametrize(
        "typ, opts, input_value, expected_dump_output",
        [
            (dict, {}, {}, {}),
            (dict, {}, {"a": 1, "b": "2"}, {"a": 1, "b": "2"}),
            (dict[str, Any], {}, {"a": 1, "b": "2"}, {"a": 1, "b": "2"}),
            (dict, {}, {"a": set([3.14])}, {"a": [3.14]}),
            (dict, {}, {"a": tuple([1, "2", 3.14])}, {"a": [1, "2", 3.14]}),
            (dict, {}, {"a": {"b": (1, "2", 3.14)}}, {"a": {"b": [1, "2", 3.14]}}),
            (list, {}, [{"b": (1, "2", 3.14)}], [{"b": [1, "2", 3.14]}]),
            (list, {}, [ipaddress.IPv4Address("192.168.1.1")], ["192.168.1.1"]),
            (set, {}, ["2"], ["2"]),
            (tuple, {}, [1, "2", 3.14], [1, "2", 3.14]),
            (datetime.datetime, {}, datetime.datetime(2000, 1, 2, 3, 4, 5, 6), "2000-01-02T03:04:05.000006"),
            (
                datetime.datetime,
                {},
                datetime.datetime(2000, 1, 2, 3, 4, 5, 6, datetime.timezone.utc),
                "2000-01-02T03:04:05.000006+0000",
            ),
            (
                datetime.datetime,
                {"datetime_format": "YYYY-MM-DD hh:mm:ss"},
                datetime.datetime(2000, 1, 2, 3, 4, 5, 6),
                "2000-01-02 03:04:05",
            ),
            (datetime.date, {}, datetime.date(2000, 1, 2), "2000-01-02"),
            (datetime.date, {"date_format": "DD-MM-YYYY"}, datetime.date(2000, 1, 2), "02-01-2000"),
            (dict, {}, {"a": datetime.date(2000, 1, 2)}, {"a": "2000-01-02"}),
            (Nested, {}, {"bar": 123}, {"bar": 123}),
            (bytes, {}, b"spam", "spam"),
            (bytes, {"bytes_format": "ascii"}, b"spam", "spam"),
            (bytes, {"bytes_format": "base64"}, b"\x00\x01", "AAE="),
            (ipaddress.IPv4Address, {}, "192.168.1.1", "192.168.1.1"),
            (ipaddress.IPv4Address, {"default_encoder": lambda l, v: int(v)}, "0.0.0.255", 255),
            (ipaddress.IPv6Address, {}, "ffff::1", "ffff::1"),
            (str, {}, "spam", "spam"),
            (int, {}, 123, 123),
            (float, {}, 3.14, 3.14),
            (bool, {}, True, True),
            (bool, {}, False, False),
            (Optional[int], {}, None, None),
            (int, {}, Unset, Unset),
            (Nested, {"exclude_unset": True}, {"bar": Unset}, {}),
            (NestedWithOptional, {"exclude_none": True}, {"bar": None}, {}),
            (EOption, {}, EOption.ONE, 1),
        ],
    )
    def test_accept_visitor(self, model: IModel, opts, expected_dump_output):
        out = {}
        visitor = cast(IModelVisitor, DumpVisitor(out))
        visitor = cast(IModelVisitor, JsonDumpVisitorProxy(visitor, **opts))
        model.accept(visitor, Loc())
        assert out == {"foo": expected_dump_output}

    @pytest.mark.parametrize(
        "typ, encoder_typ, encoder, input_value, expected_dump_output",
        [
            (Nested, Nested, lambda l, v: repr(v), {"bar": 1}, "Nested(bar=1)"),
            (list[Nested], Nested, lambda l, v: repr(v), [{"bar": 1}, {"bar": 2}], ["Nested(bar=1)", "Nested(bar=2)"]),
            (int, int, lambda l, v: str(v), 2, "2"),
            (list[int], int, lambda l, v: str(v), [1, 2], ["1", "2"]),
        ],
    )
    def test_dump_with_custom_type_encoder(self, model: IModel, encoder_typ, encoder, expected_dump_output):
        out = {}
        visitor = DumpVisitor(out)
        visitor = JsonDumpVisitorProxy(visitor)
        visitor.register_type_encoder(encoder_typ, encoder)
        model.accept(visitor, Loc())
        assert out == {"foo": expected_dump_output}
