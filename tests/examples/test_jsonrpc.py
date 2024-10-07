# Example models for the JSONRPC 2.0 protocol

from numbers import Number
from typing import Literal, Union

import pytest

from modelity.exc import ParsingError, ValidationError
from modelity.loc import Loc
from modelity.model import Model, field, model_validator
from modelity.unset import Unset

from tests.helpers import ErrorFactoryHelper

JSONRPC = Literal["2.0"]

PrimitiveType = Union[str, Number, bool, type(None)]

StructuredType = Union[list, dict]

AnyType = Union[PrimitiveType, StructuredType]

ID = Union[str, int]


class Notification(Model):
    jsonrpc: JSONRPC
    method: str
    params: StructuredType = field(optional=True)


class Request(Notification):
    id: ID


class Error(Model):
    code: int
    message: str
    data: AnyType = field(optional=True)


class Response(Model):
    jsonrpc: JSONRPC
    result: AnyType = field(optional=True)
    error: Error = field(optional=True)
    id: ID

    @model_validator
    def _validate_response(model: "Response"):
        if model.result is Unset and model.error is Unset:
            raise ValueError("neither 'error' nor 'result' field set")
        if model.result is not Unset and model.error is not Unset:
            raise ValueError("cannot set both 'error' and 'result' fields")


class TestNotification:

    @pytest.fixture
    def notif(self, data: dict):
        return Notification(**data)

    @pytest.mark.parametrize(
        "given_data, expected_dump",
        [
            ({"jsonrpc": "2.0", "method": "dummy"}, {"jsonrpc": "2.0", "method": "dummy", "params": Unset}),
            (
                {"jsonrpc": "2.0", "method": "dummy", "params": [1, 2, 3]},
                {"jsonrpc": "2.0", "method": "dummy", "params": [1, 2, 3]},
            ),
        ],
    )
    def test_load_and_dump(self, given_data: dict, expected_dump: dict):
        notif = Notification.load(given_data)
        notif.validate()
        assert notif.dump() == expected_dump
        assert Notification.load(notif.dump()) == notif

    class TestFields:

        @pytest.mark.parametrize(
            "data, expected_value",
            [
                ({}, Unset),
                ({"jsonrpc": "2.0"}, "2.0"),
            ],
        )
        def test_jsonrpc(self, notif: Notification, expected_value):
            assert notif.jsonrpc == expected_value

        @pytest.mark.parametrize(
            "value, expected_errors",
            [
                ("3.0", [ErrorFactoryHelper.invalid_literal(Loc("jsonrpc"), ("2.0",))]),
            ],
        )
        def test_jsonrpc_invalid(self, value, expected_errors):
            with pytest.raises(ParsingError) as excinfo:
                _ = Notification(jsonrpc=value)
            assert excinfo.value.errors == tuple(expected_errors)

        @pytest.mark.parametrize(
            "data, expected_value",
            [
                ({}, Unset),
                ({"method": "foo"}, "foo"),
            ],
        )
        def test_method(self, notif: Notification, expected_value):
            assert notif.method == expected_value

        @pytest.mark.parametrize(
            "data, expected_value",
            [
                ({}, Unset),
                ({"params": []}, []),
                ({"params": [1, 2, 3]}, [1, 2, 3]),
                ({"params": {}}, {}),
                ({"params": {"a": 1}}, {"a": 1}),
            ],
        )
        def test_params(self, notif: Notification, expected_value):
            assert notif.params == expected_value

        @pytest.mark.parametrize(
            "value, expected_errors",
            [
                (123, [ErrorFactoryHelper.unsupported_type(Loc("params"), (list, dict))]),
                (None, [ErrorFactoryHelper.unsupported_type(Loc("params"), (list, dict))]),
            ],
        )
        def test_params_invalid(self, value, expected_errors):
            with pytest.raises(ParsingError) as excinfo:
                _ = Notification(params=value)
            assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize(
        "data, expected_notif",
        [
            ({"jsonrpc": "2.0", "method": "spam"}, Notification(jsonrpc="2.0", method="spam")),
            (
                {"jsonrpc": "2.0", "method": "spam", "params": [1, 2]},
                Notification(jsonrpc="2.0", method="spam", params=[1, 2]),
            ),
        ],
    )
    def test_create_valid_request_object(self, notif: Notification, expected_notif):
        notif.validate()
        assert notif == expected_notif

    @pytest.mark.parametrize(
        "data, expected_errors",
        [
            (
                {},
                [
                    ErrorFactoryHelper.required_missing(Loc("jsonrpc")),
                    ErrorFactoryHelper.required_missing(Loc("method")),
                ],
            ),
        ],
    )
    def test_create_invalid_request_object(self, notif: Notification, expected_errors):
        with pytest.raises(ValidationError) as excinfo:
            notif.validate()
        assert excinfo.value.model is notif
        assert excinfo.value.errors == tuple(expected_errors)


class TestRequest:

    @pytest.fixture
    def req(self, data: dict):
        return Request(**data)

    @pytest.mark.parametrize(
        "given_data, expected_dump",
        [
            (
                {"jsonrpc": "2.0", "method": "dummy", "id": 1},
                {"jsonrpc": "2.0", "method": "dummy", "id": 1, "params": Unset},
            ),
            (
                {"jsonrpc": "2.0", "method": "dummy", "id": 1, "params": [1, 2, 3]},
                {"jsonrpc": "2.0", "method": "dummy", "id": 1, "params": [1, 2, 3]},
            ),
        ],
    )
    def test_load_and_dump(self, given_data: dict, expected_dump: dict):
        request = Request.load(given_data)
        request.validate()
        assert request.dump() == expected_dump
        assert Request.load(request.dump()) == request

    class TestFields:

        @pytest.mark.parametrize(
            "data, expected_value",
            [
                ({}, Unset),
                ({"id": 1}, 1),
                ({"id": "2"}, "2"),
                ({"id": "foo"}, "foo"),
            ],
        )
        def test_id(self, req: Request, expected_value):
            assert req.id == expected_value

    @pytest.mark.parametrize(
        "data, expected_req",
        [
            ({"jsonrpc": "2.0", "method": "spam", "id": 1}, Request(jsonrpc="2.0", method="spam", id=1)),
            (
                {"jsonrpc": "2.0", "method": "spam", "params": [1, 2], "id": 1},
                Request(jsonrpc="2.0", method="spam", params=[1, 2], id=1),
            ),
        ],
    )
    def test_create_valid_request_object(self, req: Request, expected_req):
        req.validate()
        assert req == expected_req

    @pytest.mark.parametrize(
        "data, expected_errors",
        [
            (
                {},
                [
                    ErrorFactoryHelper.required_missing(Loc("jsonrpc")),
                    ErrorFactoryHelper.required_missing(Loc("method")),
                    ErrorFactoryHelper.required_missing(Loc("id")),
                ],
            ),
        ],
    )
    def test_create_invalid_request_object(self, req: Request, expected_errors):
        with pytest.raises(ValidationError) as excinfo:
            req.validate()
        assert excinfo.value.model is req
        assert excinfo.value.errors == tuple(expected_errors)


class TestError:

    @pytest.fixture
    def obj(self, data: dict):
        return Error(**data)

    @pytest.mark.parametrize(
        "data, expected_obj",
        [
            ({"code": -32601, "message": "Method not found"}, Error(code=-32601, message="Method not found")),
            (
                {"code": -32601, "message": "Method not found", "data": "foo"},
                Error(code=-32601, message="Method not found", data="foo"),
            ),
            (
                {"code": -32601, "message": "Method not found", "data": "on"},
                Error(code=-32601, message="Method not found", data="on"),
            ),
            (
                {"code": -32601, "message": "Method not found", "data": 123},
                Error(code=-32601, message="Method not found", data=123),
            ),
            (
                {"code": -32601, "message": "Method not found", "data": 2.71},
                Error(code=-32601, message="Method not found", data=2.71),
            ),
            (
                {"code": -32601, "message": "Method not found", "data": True},
                Error(code=-32601, message="Method not found", data=True),
            ),
        ],
    )
    def test_create_valid_object(self, obj: Error, expected_obj):
        obj.validate()
        assert obj == expected_obj

    @pytest.mark.parametrize(
        "data, expected_errors",
        [
            (
                {},
                [
                    ErrorFactoryHelper.required_missing(Loc("code")),
                    ErrorFactoryHelper.required_missing(Loc("message")),
                ],
            ),
        ],
    )
    def test_create_invalid_object(self, obj: Error, expected_errors):
        with pytest.raises(ValidationError) as excinfo:
            obj.validate()
        assert excinfo.value.model is obj
        assert excinfo.value.errors == tuple(expected_errors)


class TestResponse:

    @pytest.fixture
    def obj(self, data: dict):
        return Response(**data)

    @pytest.mark.parametrize(
        "data, expected_obj",
        [
            ({"jsonrpc": "2.0", "result": 123, "id": 1}, Response(jsonrpc="2.0", result=123, id=1)),
            (
                {"jsonrpc": "2.0", "error": {"code": 404, "message": "Not found"}, "id": 1},
                Response(jsonrpc="2.0", error=Error(code=404, message="Not found"), id=1),
            ),
        ],
    )
    def test_create_valid_object(self, obj: Response, expected_obj):
        obj.validate()
        assert obj == expected_obj

    @pytest.mark.parametrize(
        "data, expected_errors",
        [
            (
                {},
                [
                    ErrorFactoryHelper.required_missing(Loc("jsonrpc")),
                    ErrorFactoryHelper.required_missing(Loc("id")),
                    ErrorFactoryHelper.value_error(Loc(), "neither 'error' nor 'result' field set"),
                ],
            ),
            (
                {"jsonrpc": "2.0", "id": 1},
                [ErrorFactoryHelper.value_error(Loc(), "neither 'error' nor 'result' field set")],
            ),
            (
                {"jsonrpc": "2.0", "id": 1, "error": {}},
                [
                    ErrorFactoryHelper.required_missing(Loc("error", "code")),
                    ErrorFactoryHelper.required_missing(Loc("error", "message")),
                ],
            ),
            (
                {"jsonrpc": "2.0", "id": 1, "error": {"code": 1, "message": "a message"}, "result": None},
                [
                    ErrorFactoryHelper.value_error(Loc(), "cannot set both 'error' and 'result' fields"),
                ],
            ),
        ],
    )
    def test_create_invalid_object(self, obj: Response, expected_errors):
        with pytest.raises(ValidationError) as excinfo:
            obj.validate()
        assert excinfo.value.model is obj
        assert excinfo.value.errors == tuple(expected_errors)
