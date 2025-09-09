# TODO: Some workarounds need to be fixed once all tests in this module will be
# adjusted according to test_pathlib.py, which is the most recent one.

import pytest

from modelity.model import Model


def _validate_data_format(data: tuple):
    if len(data) != 5:
        raise TypeError(
            f"unsupported 'data' format; expected (field_type, field_info, input, expected_output, expected_dump_output), got {data!r}"
        )


def _validate_invalid_data_format(invalid_data: tuple):
    if len(invalid_data) != 4:
        raise TypeError(
            f"unsupported 'invalid_data' format; expected (field_type, field_info, input, expected_errors), got {invalid_data!r}"
        )


@pytest.fixture
def data():
    return tuple()


@pytest.fixture
def invalid_data():
    return tuple()


@pytest.fixture
def field_type(data: tuple, invalid_data: tuple):
    if data:
        _validate_data_format(data)
        return data[0]
    _validate_invalid_data_format(invalid_data)
    return invalid_data[0]


@pytest.fixture
def field_info(data: tuple, invalid_data: tuple):
    if data:
        _validate_data_format(data)
        return data[1]
    _validate_invalid_data_format(invalid_data)
    return invalid_data[1]


@pytest.fixture
def input(data: tuple):
    return data[0] if len(data) != 5 else data[2]


@pytest.fixture
def expected_output(data: tuple):
    return data[1] if len(data) != 5 else data[3]


@pytest.fixture
def expected_dump_output(data: tuple):
    return data[2] if len(data) != 5 else data[4]


@pytest.fixture
def invalid_input(invalid_data: tuple):
    return invalid_data[0] if len(invalid_data) != 4 else invalid_data[2]


@pytest.fixture
def expected_errors(invalid_data: tuple):
    return invalid_data[1] if len(invalid_data) != 4 else invalid_data[3]


@pytest.fixture
def SUT(field_type, field_info):
    if field_info is None:

        class SUT(Model):
            foo: field_type

        return SUT

    class SUT(Model):
        foo: field_type = field_info

    return SUT


@pytest.fixture
def sut(SUT):
    return SUT()
