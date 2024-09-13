# Example models for the JSONRPC 2.0 protocol

from typing import Literal, Optional

import pytest

from modelity.model import Model
from modelity.undefined import Undefined

JSONRPC = Literal["2.0"]

Structured = list | dict


class Request(Model):
    jsonrpc: JSONRPC = "2.0"
    method: str
    params: Optional[Structured]


class TestRequest:

    @pytest.fixture
    def req(self, data):
        return Request(**data)

    @pytest.mark.parametrize("data, jsonrpc, method, params", [
        ({}, "2.0", Undefined, Undefined),
    ])
    def test_create_request_model(self, req: Request, jsonrpc, method, params):
        assert req.jsonrpc == jsonrpc
        assert req.method == method
        assert req.params == params
