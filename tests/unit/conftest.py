import pytest

from mockify.api import Mock, satisfied


@pytest.fixture
def mock():
    mock = Mock("mock")
    with satisfied(mock):
        yield mock
