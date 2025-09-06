import pytest


@pytest.fixture
def input(data: tuple):
    return data[0]


@pytest.fixture
def expected_output(data: tuple):
    return data[1]


@pytest.fixture
def expected_dump_output(data: tuple):
    return data[2]


@pytest.fixture
def invalid_input(invalid_data: tuple):
    return invalid_data[0]


@pytest.fixture
def expected_errors(invalid_data: tuple):
    return invalid_data[1]
