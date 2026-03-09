from typing import Optional, Union

import pytest

from modelity.typing import LooseOptional, StrictOptional, is_loose_optional, is_optional, is_strict_optional
from modelity.unset import UnsetType


@pytest.mark.parametrize(
    "tp, expected_result",
    [
        (int, False),
        (Union[int, float], False),
        (Union[int, float, None], False),
        (Union[int, None], True),
        (Optional[int], True),
    ],
)
def test_is_optional(tp, expected_result):
    assert is_optional(tp) == expected_result


@pytest.mark.parametrize(
    "tp, expected_result",
    [
        (int, False),
        (Union[int, None], False),
        (Union[int, float, None], False),
        (StrictOptional[int], True),
        (StrictOptional[int | float], False),
        (Union[int, float, None, UnsetType], False),
    ],
)
def test_is_strict_optional(tp, expected_result):
    assert is_strict_optional(tp) == expected_result


@pytest.mark.parametrize(
    "tp, expected_result",
    [
        (int, False),
        (Union[int, None], False),
        (Union[int, float, None], False),
        (Union[int, None, UnsetType], True),
        (Union[int, float, None, UnsetType], False),
        (LooseOptional[int], True),
        (LooseOptional[int | float], False),
    ],
)
def test_is_loose_optional(tp, expected_result):
    assert is_loose_optional(tp) == expected_result
