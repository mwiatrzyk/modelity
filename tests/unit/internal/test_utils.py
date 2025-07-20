import pytest

from modelity._internal.utils import is_subsequence


@pytest.mark.parametrize(
    "candidate, sequence, expected_result",
    [
        ([1], [1], True),
        ([1], [2], False),
        ([1, 2], [2], False),
        ([1, 3], [0, 1, 2, 3], True),
        ([1, 3, 4], [1], False),
        ([1, 3], [0, 3, 2, 1], False),
    ],
)
def test_is_subsequence(candidate, sequence, expected_result):
    assert is_subsequence(candidate, sequence) == expected_result
