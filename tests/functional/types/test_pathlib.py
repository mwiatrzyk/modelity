import pathlib

import pytest

from modelity.error import ErrorFactory
from modelity.loc import Loc
from modelity.model import Model, field_info
from modelity.types import Deferred
from modelity.unset import Unset

from . import common


class TestPathlibPath:

    @pytest.mark.parametrize(
        "data",
        [
            (Deferred[pathlib.Path], None, "/tmp", pathlib.Path("/tmp"), "/tmp"),
            (Deferred[pathlib.Path], None, b"/tmp", pathlib.Path("/tmp"), "/tmp"),
            (Deferred[pathlib.Path], field_info(bytes_encoding="ascii"), b"/tmp", pathlib.Path("/tmp"), "/tmp"),
            (Deferred[pathlib.Path], None, pathlib.Path("/home"), pathlib.Path("/home"), "/home"),
        ],
    )
    class TestParseSuccessfully:

        @pytest.fixture(autouse=True)
        def setup(self, SUT):
            self.SUT = SUT

        def test_construct_successfully(self, input, expected_output):
            common.test_construct_successfully(self, input, expected_output)

        def test_assign_successfully(self, input, expected_output):
            common.test_assign_successfully(self, input, expected_output)

        def test_validate_successfully(self, input, expected_output):
            common.test_validate_successfully(self, input, expected_output)

        def test_dump_successfully(self, input, expected_dump_output):
            common.test_dump_successfully(self, input, expected_dump_output)

    @pytest.mark.parametrize(
        "invalid_data",
        [
            (
                Deferred[pathlib.Path],
                None,
                None,
                [ErrorFactory.invalid_type(common.loc, None, [str, bytes, pathlib.Path])],
            ),
            (
                Deferred[pathlib.Path],
                field_info(bytes_encoding="ascii"),
                b"\xff",
                [
                    ErrorFactory.decode_error(
                        common.loc,
                        b"\xff",
                        ["ascii"],
                    )
                ],
            ),
        ],
    )
    class TestParsingErrors:

        @pytest.fixture(autouse=True)
        def setup(self, SUT):
            self.SUT = SUT

        def test_constructing_fails_for_invalid_input(self, invalid_input, expected_errors):
            common.test_constructing_fails_for_invalid_input(self, invalid_input, expected_errors)

        def test_assignment_fails_for_invalid_input(self, invalid_input, expected_errors):
            common.test_assignment_fails_for_invalid_input(self, invalid_input, expected_errors)

    class SUT(Model):
        foo: Deferred[pathlib.Path] = Unset

    def test_accept_visitor(self, mock):
        sut = self.SUT(foo="/spam")  # type: ignore
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_scalar.expect_call(Loc("foo"), pathlib.Path("/spam"))
        mock.visit_model_field_end.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_model_end.expect_call(Loc(), sut)
        sut.accept(mock, Loc())
