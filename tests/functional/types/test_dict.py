from typing import Any, Mapping
import pytest

from mockify.api import Return, ordered

from modelity.error import ErrorFactory
from modelity.exc import ParsingError
from modelity.loc import Loc
from modelity.model import Model
from modelity.types import Deferred
from modelity.unset import Unset

from . import common


@pytest.mark.parametrize(
    "typ",
    [
        dict,
        dict[Any, Any],
    ],
)
class TestAnyDict:

    @pytest.fixture
    def SUT(self, typ):

        class SUT(Model):
            foo: Deferred[typ] = Unset

        return SUT

    @pytest.fixture(autouse=True)
    def setup(self, SUT):
        self.SUT = SUT

    @pytest.fixture(
        params=[
            ({}, {}, {}),
            ({"foo": 1, "bar": True}, {"foo": 1, "bar": True}, {"foo": 1, "bar": True}),
        ]
    )
    def data(self, request):
        return request.param

    @pytest.fixture(
        params=[
            (None, [ErrorFactory.invalid_type(common.loc, None, [dict], [Mapping])]),
        ]
    )
    def invalid_data(self, request):
        return request.param

    def test_construct_successfully(self, input, expected_output):
        common.test_construct_successfully(self, input, expected_output)

    def test_assign_successfully(self, input, expected_output):
        common.test_assign_successfully(self, input, expected_output)

    def test_validate_successfully(self, input, expected_output):
        common.test_validate_successfully(self, input, expected_output)

    def test_dump_successfully(self, input, expected_dump_output):
        common.test_dump_successfully(self, input, expected_dump_output)

    def test_constructing_fails_for_invalid_input(self, invalid_input, expected_errors):
        common.test_constructing_fails_for_invalid_input(self, invalid_input, expected_errors)

    def test_assignment_fails_for_invalid_input(self, invalid_input, expected_errors):
        common.test_assignment_fails_for_invalid_input(self, invalid_input, expected_errors)

    def test_accept_visitor(self, mock):
        sut = self.SUT(foo={"one": 1, "two": "spam"})
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_mapping_begin.expect_call(Loc("foo"), sut.foo)
        mock.visit_any.expect_call(Loc("foo", "one"), 1)
        mock.visit_any.expect_call(Loc("foo", "two"), "spam")
        mock.visit_mapping_end.expect_call(Loc("foo"), sut.foo)
        mock.visit_model_field_end.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_model_end.expect_call(Loc(), sut)
        with ordered(mock):
            sut.accept(mock, Loc())

    def test_when_visit_mapping_begin_returns_true_then_visiting_mapping_is_skipped(self, mock):
        sut = self.SUT(foo={"one": 1})
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_mapping_begin.expect_call(Loc("foo"), sut.foo).will_once(Return(True))
        mock.visit_model_field_end.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_model_end.expect_call(Loc(), sut)
        with ordered(mock):
            sut.accept(mock, Loc())


class TestTypedDict:

    class SUT(Model):
        foo: Deferred[dict[str, int]] = Unset

    @pytest.fixture(
        params=[
            ({}, {}, {}),
            ({"one": 1}, {"one": 1}, {"one": 1}),
            ({"two": "2"}, {"two": 2}, {"two": 2}),
        ]
    )
    def data(self, request):
        return request.param

    @pytest.fixture(
        params=[
            (None, [ErrorFactory.invalid_type(common.loc, None, [dict], [Mapping])]),
            ({1: 1}, [ErrorFactory.invalid_type(common.loc + Loc.irrelevant(), 1, [str])]),
            ({"one": "spam"}, [ErrorFactory.parse_error(common.loc + Loc("one"), "spam", int)]),
        ]
    )
    def invalid_data(self, request):
        return request.param

    def test_construct_successfully(self, input, expected_output):
        common.test_construct_successfully(self, input, expected_output)

    def test_assign_successfully(self, input, expected_output):
        common.test_assign_successfully(self, input, expected_output)

    def test_validate_successfully(self, input, expected_output):
        common.test_validate_successfully(self, input, expected_output)

    def test_dump_successfully(self, input, expected_dump_output):
        common.test_dump_successfully(self, input, expected_dump_output)

    def test_constructing_fails_for_invalid_input(self, invalid_input, expected_errors):
        common.test_constructing_fails_for_invalid_input(self, invalid_input, expected_errors)

    def test_assignment_fails_for_invalid_input(self, invalid_input, expected_errors):
        common.test_assignment_fails_for_invalid_input(self, invalid_input, expected_errors)

    def test_accept_visitor(self, mock):
        sut = self.SUT(foo={"one": 1})
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_mapping_begin.expect_call(Loc("foo"), sut.foo)
        mock.visit_scalar.expect_call(Loc("foo", "one"), 1)
        mock.visit_mapping_end.expect_call(Loc("foo"), sut.foo)
        mock.visit_model_field_end.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_model_end.expect_call(Loc(), sut)
        with ordered(mock):
            sut.accept(mock, Loc())

    def test_when_visit_mapping_begin_returns_true_then_visiting_mapping_is_skipped(self, mock):
        sut = self.SUT(foo={"one": 1})
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_mapping_begin.expect_call(Loc("foo"), sut.foo).will_once(Return(True))
        mock.visit_model_field_end.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_model_end.expect_call(Loc(), sut)
        with ordered(mock):
            sut.accept(mock, Loc())

    class TestMethods:

        @pytest.fixture
        def SUT(self):

            class SUT(Model):
                foo: dict[str, list[int]] = {}

            return SUT

        class TestSetDefault:

            def test_setdefault_and_append(self, SUT):
                sut = SUT()
                sut.foo.setdefault("bar", []).append("123")  # type: ignore
                assert sut.foo == {"bar": [123]}

            def test_incorrect_default_value_causes_parsing_error(self, SUT):
                sut = SUT()
                with pytest.raises(ParsingError) as excinfo:
                    sut.foo.setdefault("bar", [1, 3.14, "spam"])
                assert excinfo.value.errors == (ErrorFactory.parse_error(Loc("bar", 2), "spam", int),)

            def test_does_not_change_value_if_already_exists(self, SUT):
                sut = SUT()
                sut.foo = {"bar": [1, 2, 3]}
                sut.foo.setdefault("bar", [4, 5, 6])
                assert sut.foo["bar"] == [1, 2, 3]

        class TestUpdate:

            @pytest.mark.parametrize(
                "args, kwargs, expected_output",
                [
                    (tuple(), dict(), {}),
                    (tuple(), dict(foo=[1], bar=["2"]), {"foo": [1], "bar": [2]}),
                    (tuple([[("foo", [1])]]), dict(), {"foo": [1]}),
                    (tuple([[("foo", [1])]]), dict(bar=[2]), {"foo": [1], "bar": [2]}),
                ],
            )
            def test_update_successfully(self, SUT, args, kwargs, expected_output):
                sut = SUT()
                sut.foo.update(*args, **kwargs)
                assert sut.foo == expected_output

            def test_update_overwrites_previous_values(self, SUT):
                sut = SUT(foo={"bar": [1]})
                assert sut.foo == {"bar": [1]}
                sut.foo.update(bar=[2])
                assert sut.foo["bar"] == [2]

            def test_update_fails_with_multiple_errors_if_multiple_items_are_invalid(self, SUT):
                sut = SUT()
                with pytest.raises(ParsingError) as excinfo:
                    sut.foo.update({"bar": ["spam"], "baz": [1, 2, "more spam"]})
                assert excinfo.value.errors == (
                    ErrorFactory.parse_error(Loc("bar", 0), "spam", int),
                    ErrorFactory.parse_error(Loc("baz", 2), "more spam", int),
                )

            def test_update_raises_type_error_if_called_with_incorrect_params(self, SUT):
                sut = SUT(foo={})
                with pytest.raises(TypeError) as excinfo:
                    sut.foo.update(1, 2, foo=[1])
                assert (
                    str(excinfo.value) == "update() called with unsupported arguments: args=(1, 2), kwargs={'foo': [1]}"
                )
