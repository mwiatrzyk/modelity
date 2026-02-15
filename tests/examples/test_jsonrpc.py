# Example models for the JSONRPC 2.0 protocol

from typing import Literal, Union

import pytest

from modelity.api import (
    ParsingError,
    ValidationError,
    Loc,
    Model,
    model_postvalidator,
    dump,
    validate,
    StrictOptional,
    Unset,
    UnsetType,
    ErrorFactory,
)
from modelity.types import Deferred

JSONRPC = Literal["2.0"]

PrimitiveType = Union[str, int, float, bool, type(None)]

StructuredType = Union[list, dict]

AnyType = Union[PrimitiveType, StructuredType]

ID = Union[str, int]


class Notification(Model):
    jsonrpc: Deferred[JSONRPC] = Unset
    method: Deferred[str] = Unset
    params: StrictOptional[StructuredType] = Unset


class Request(Notification):
    id: Deferred[ID] = Unset


class Error(Model):
    code: Deferred[int] = Unset
    message: Deferred[str] = Unset
    data: StrictOptional[AnyType] = Unset


class Response(Model):
    jsonrpc: Deferred[JSONRPC] = Unset
    result: StrictOptional[AnyType] = Unset
    error: StrictOptional[Error] = Unset
    id: Deferred[ID] = Unset

    @model_postvalidator()
    def _validate_response(self):
        if self.result is Unset and self.error is Unset:
            raise ValueError("neither 'error' nor 'result' Field set")
        if self.result is not Unset and self.error is not Unset:
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
        notif = Notification(**given_data)
        validate(notif)
        assert dump(notif) == expected_dump
        assert Notification(**dump(notif)) == notif

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
                ("3.0", [ErrorFactory.invalid_value(Loc("jsonrpc"), "3.0", ["2.0"])]),
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
                (
                    123,
                    [
                        ErrorFactory.invalid_type(Loc("params"), 123, [list, dict, UnsetType]),
                    ],
                ),
                (
                    None,
                    [
                        ErrorFactory.invalid_type(Loc("params"), None, [list, dict, UnsetType]),
                    ],
                ),
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
        validate(notif)
        assert notif == expected_notif

    @pytest.mark.parametrize(
        "data, expected_errors",
        [
            (
                {},
                [
                    ErrorFactory.required_missing(Loc("jsonrpc")),
                    ErrorFactory.required_missing(Loc("method")),
                ],
            ),
        ],
    )
    def test_create_invalid_request_object(self, notif: Notification, expected_errors):
        with pytest.raises(ValidationError) as excinfo:
            validate(notif)
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
        request = Request(**given_data)
        validate(request)
        assert dump(request) == expected_dump
        assert Request(**dump(request)) == request

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
        validate(req)
        assert req == expected_req

    @pytest.mark.parametrize(
        "data, expected_errors",
        [
            (
                {},
                [
                    ErrorFactory.required_missing(Loc("jsonrpc")),
                    ErrorFactory.required_missing(Loc("method")),
                    ErrorFactory.required_missing(Loc("id")),
                ],
            ),
        ],
    )
    def test_create_invalid_request_object(self, req: Request, expected_errors):
        with pytest.raises(ValidationError) as excinfo:
            validate(req)
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
        validate(obj)
        assert obj == expected_obj

    @pytest.mark.parametrize(
        "data, expected_errors",
        [
            (
                {},
                [
                    ErrorFactory.required_missing(Loc("code")),
                    ErrorFactory.required_missing(Loc("message")),
                ],
            ),
        ],
    )
    def test_create_invalid_object(self, obj: Error, expected_errors):
        with pytest.raises(ValidationError) as excinfo:
            validate(obj)
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
        validate(obj)
        assert obj == expected_obj

    @pytest.mark.parametrize(
        "data, expected_errors",
        [
            (
                {},
                [
                    ErrorFactory.required_missing(Loc("jsonrpc")),
                    ErrorFactory.required_missing(Loc("id")),
                    ErrorFactory.exception(Loc(), Unset, ValueError("neither 'error' nor 'result' Field set")),
                ],
            ),
            (
                {"jsonrpc": "2.0", "id": 1},
                [ErrorFactory.exception(Loc(), Unset, ValueError("neither 'error' nor 'result' Field set"))],
            ),
            (
                {"jsonrpc": "2.0", "id": 1, "error": {}},
                [
                    ErrorFactory.required_missing(Loc("error", "code")),
                    ErrorFactory.required_missing(Loc("error", "message")),
                ],
            ),
            (
                {"jsonrpc": "2.0", "id": 1, "error": {"code": 1, "message": "a message"}, "result": None},
                [
                    ErrorFactory.exception(Loc(), Unset, ValueError("cannot set both 'error' and 'result' fields")),
                ],
            ),
        ],
    )
    def test_create_invalid_object(self, obj: Response, expected_errors):
        with pytest.raises(ValidationError) as excinfo:
            validate(obj)
        assert excinfo.value.model is obj
        assert excinfo.value.errors == tuple(expected_errors)
