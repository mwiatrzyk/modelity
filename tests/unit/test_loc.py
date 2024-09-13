import pytest
from modelity.loc import Loc


class TestLoc:

    @pytest.mark.parametrize("uut, expected_repr", [
        (Loc(), "Loc()"),
        (Loc(1), "Loc(1)"),
        (Loc("foo"), "Loc('foo')"),
        (Loc("foo", "bar", 1), "Loc('foo', 'bar', 1)"),
    ])
    def test_repr(self, uut, expected_repr):
        assert repr(uut) == expected_repr

    @pytest.mark.parametrize("uut, expected_str", [
        (Loc(), ""),
        (Loc("foo"), "foo"),
        (Loc(1), "1"),
        (Loc("foo", "bar", 2), "foo.bar.2"),
    ])
    def test_str(self, uut, expected_str):
        assert str(uut) == expected_str

    # @pytest.mark.parametrize("uut, index, expected", [
    #     (Loc(1), 0, 1),
    #     (Loc("spam"), 0, "spam"),
    #     (Loc("spam", "bar", 1, "baz"), 2, 1),
    # ])
    # def test_getitem(self, uut, index, expected):
    #     assert uut[index] == expected

    # @pytest.mark.parametrize("uut, expected", [
    #     (Loc(), 0),
    #     (Loc("foo"), 1),
    #     (Loc("spam"), 1),
    #     (Loc("foo", "bar", 2), 3),
    # ])
    # def test_len(self, uut, expected):
    #     assert len(uut) == expected

    @pytest.mark.parametrize("left, right, is_equal", [
        (Loc(), Loc(), True),
        (Loc(1), Loc(), False),
        (Loc(), Loc(1), False),
        (Loc(1), Loc(1), True),
        (Loc("foo"), Loc("foo", 2), False),
    ])
    def test_eq_and_ne_operators(self, left, right, is_equal):
        assert (left == right) == is_equal
        assert (left != right) == (not is_equal)

    @pytest.mark.parametrize("left, right, expected_sum", [
        (Loc(), Loc(), Loc()),
        (Loc(1), Loc(2), Loc(1, 2)),
        (Loc("foo", "bar"), Loc("baz", "spam", 3), Loc("foo", "bar", "baz", "spam", 3)),
    ])
    def test_concatenate_two_locs(self, left, right, expected_sum):
        assert left + right == expected_sum
