# Example models for the JSONRPC 2.0 protocol

from types import NoneType
from typing import Literal, Optional, Union

import pytest

from modelity.model import Model
from modelity.undefined import Undefined

JSONRPC = Literal["2.0"]

StructuredType = Union[list, dict]

IdType = Union[str, int]


class Request(Model):
    jsonrpc: JSONRPC
    method: str
    params: Optional[StructuredType]
    id: IdType


class TestRequest:

    @pytest.fixture
    def req(self, data: dict):
        return Request(**data)

    class TestFields:

        @pytest.mark.parametrize("data, expected_value", [
            ({}, Undefined),
            ({"jsonrpc": "2.0"}, "2.0"),
        ])
        def test_jsonrpc(self, req: Request, expected_value):
            assert req.jsonrpc == expected_value

        @pytest.mark.parametrize("data, expected_value", [
            ({}, Undefined),
            ({"method": "foo"}, "foo"),
        ])
        def test_method(self, req: Request, expected_value):
            assert req.method == expected_value

        @pytest.mark.parametrize("data, expected_value", [
            ({}, Undefined),
            ({"params": []}, []),
            ({"params": [1, 2, 3]}, [1, 2, 3]),
            ({"params": {}}, {}),
            ({"params": {"a": 1}}, {"a": 1}),
        ])
        def test_params(self, req: Request, expected_value):
            assert req.params == expected_value

        @pytest.mark.parametrize("data, expected_value", [
            ({}, Undefined),
            ({"id": 1}, 1),
            ({"id": "2"}, "2"),
            ({"id": "foo"}, "foo"),
        ])
        def test_id(self, req: Request, expected_value):
            assert req.id == expected_value

    @pytest.mark.parametrize("data, expected_req", [
        ({"jsonrpc": "2.0", "method": "spam", "id": 1}, Request(jsonrpc="2.0", method="spam", id=1)),
        ({"jsonrpc": "2.0", "method": "spam", "params": [1, 2], "id": 1}, Request(jsonrpc="2.0", method="spam", params=[1, 2], id=1)),
    ])
    def test_create_valid_request_object(self, req: Request, expected_req):
        req.validate()
        assert req == expected_req
