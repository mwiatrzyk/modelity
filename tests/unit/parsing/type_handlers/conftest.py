import pytest

from mockify.api import Mock, satisfied


@pytest.fixture
def visitor_mock():
    mock = Mock("visitor_mock")
    with satisfied(mock):
        yield mock


@pytest.fixture
def type_handler_factory_mock():
    mock = Mock("type_handler_factory_mock")
    with satisfied(mock):
        yield mock
