import pytest

from mockify.api import Mock, satisfied

pytest.register_assert_rewrite('tests.functional.types.common')


@pytest.fixture
def mock():
    mock = Mock("mock")
    with satisfied(mock):
        yield mock
