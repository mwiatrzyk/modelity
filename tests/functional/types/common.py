import pytest

from modelity.exc import ParsingError
from modelity.helpers import dump, validate
from modelity.loc import Loc

loc = Loc("foo")


def test_construct_successfully(self, input, expected_output):
    sut = self.SUT(foo=input)
    assert sut.foo == expected_output


def test_assign_successfully(self, input, expected_output):
    sut = self.SUT()
    sut.foo = input
    assert sut.foo == expected_output


def test_validate_successfully(self, input, expected_output):
    sut = self.SUT(foo=input)
    assert sut.foo == expected_output
    validate(sut)


def test_dump_successfully(self, input, expected_dump_output):
    sut = self.SUT(foo=input)
    if not callable(expected_dump_output):
        assert dump(sut) == {'foo': expected_dump_output}
    else:
        data = dump(sut)
        assert expected_dump_output(data['foo'])


def test_constructing_fails_for_invalid_input(self, invalid_input, expected_errors):
    with pytest.raises(ParsingError) as excinfo:
        self.SUT(foo=invalid_input)
    assert excinfo.value.errors == tuple(expected_errors)


def test_assignment_fails_for_invalid_input(self, invalid_input, expected_errors):
    sut = self.SUT()
    with pytest.raises(ParsingError) as excinfo:
        sut.foo = invalid_input
    assert excinfo.value.errors == tuple(expected_errors)
