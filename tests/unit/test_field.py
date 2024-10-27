import pytest

from modelity.unset import Unset
from modelity.field import Field


class TestField:

    @pytest.mark.parametrize(
        "uut, expected_result",
        [
            (Field(), Unset),
            (Field(default=None), None),
            (Field(default=1), 1),
            (Field(default_factory=lambda: 2), 2),
            (Field(default=3, default_factory=lambda: 4), 3),
        ],
    )
    def test_compute_default(self, uut: Field, expected_result):
        assert uut.compute_default() == expected_result
