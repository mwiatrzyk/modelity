import pathlib

import pytest

from modelity.error import ErrorFactory
from modelity.loc import Loc
from modelity.model import Model, field_info

from . import common


class TestPathlibPath:

    @pytest.mark.parametrize(
        "data",
        [
            (pathlib.Path, None, "/tmp", pathlib.Path("/tmp"), "/tmp"),
            (pathlib.Path, None, b"/tmp", pathlib.Path("/tmp"), "/tmp"),
            (pathlib.Path, field_info(bytes_encoding="ascii"), b"/tmp", pathlib.Path("/tmp"), "/tmp"),
            (pathlib.Path, None, pathlib.Path("/home"), pathlib.Path("/home"), "/home"),
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
                pathlib.Path,
                None,
                None,
                [ErrorFactory.invalid_type(common.loc, None, [str, bytes, pathlib.Path])],
            ),
            (
                pathlib.Path,
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
        foo: pathlib.Path

    def test_accept_visitor(self, mock):
        sut = self.SUT(foo="/spam")
        mock.visit_model_begin.expect_call(Loc(), sut)
        mock.visit_model_field_begin.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_scalar.expect_call(Loc("foo"), pathlib.Path("/spam"))
        mock.visit_model_field_end.expect_call(Loc("foo"), sut.foo, self.SUT.__model_fields__["foo"])
        mock.visit_model_end.expect_call(Loc(), sut)
        sut.accept(mock, Loc())
