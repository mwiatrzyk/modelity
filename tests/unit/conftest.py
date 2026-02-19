import pytest

from mockify.api import Mock, satisfied


@pytest.fixture
def type_handler_mock():
    mock = Mock("type_handler_mock")
    with satisfied(mock):
        yield mock
