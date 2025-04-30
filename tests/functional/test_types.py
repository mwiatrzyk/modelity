# TODO: This is new way of writing e2e tests for supported types, so if it
# meets all expectations the other tests will be moved here.

from ipaddress import IPv4Address

import pytest

from modelity.error import ErrorFactory
from modelity.exc import ParsingError
from modelity.interface import DISCARD
from modelity.loc import Loc
from modelity.model import Model, dump, validate


@pytest.fixture
def model_type(typ):

    class SUT(Model):
        foo: typ

    return SUT


@pytest.fixture
def model(model_type, input_value):
    return model_type(foo=input_value)


@pytest.mark.parametrize("typ", [IPv4Address])
class TestIPv4:

    @pytest.mark.parametrize(
        "input_value, output_value",
        [
            (IPv4Address("192.168.0.1"), IPv4Address("192.168.0.1")),
            ("192.168.0.1", IPv4Address("192.168.0.1")),
        ],
    )
    def test_parse_successfully(self, model, output_value):
        assert model.foo == output_value

    @pytest.mark.parametrize(
        "input_value, expected_errors",
        [
            (
                None,
                [
                    ErrorFactory.parsing_error(
                        Loc("foo"),
                        None,
                        "not a valid IPv4 address",
                        IPv4Address,
                    )
                ],
            ),
        ],
    )
    def test_parse_with_error(self, model_type, input_value, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            model_type(foo=input_value)
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize(
        "input_value, dump_filter, output_value",
        [
            ("1.1.1.1", lambda l, v: v, {"foo": "1.1.1.1"}),
            ("1.1.1.1", lambda l, v: DISCARD if l == Loc("foo") else v, {}),
            ("1.1.1.1", lambda l, v: DISCARD if v == IPv4Address("1.1.1.1") else v, {}),
        ],
    )
    def test_dump(self, model, dump_filter, output_value):
        assert model.dump(dump_filter) == output_value

    @pytest.mark.parametrize("input_value", [
        "1.1.1.2"
    ])
    def test_validate(self, model):
        validate(model)
