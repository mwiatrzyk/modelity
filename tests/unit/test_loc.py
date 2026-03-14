import pytest

from modelity.loc import Loc, Pattern


class TestLoc:

    @pytest.mark.parametrize(
        "uut, expected_repr",
        [
            (Loc(), "Loc()"),
            (Loc(1), "Loc(1)"),
            (Loc("foo"), "Loc('foo')"),
            (Loc("foo", "bar", 1), "Loc('foo', 'bar', 1)"),
        ],
    )
    def test_repr(self, uut, expected_repr):
        assert repr(uut) == expected_repr

    @pytest.mark.parametrize(
        "uut, expected_str",
        [
            (Loc(), "(empty)"),
            (Loc("foo"), "foo"),
            (Loc(1), "1"),
            (Loc("foo", "bar", 2), "foo.bar.2"),
        ],
    )
    def test_str(self, uut, expected_str):
        assert str(uut) == expected_str

    @pytest.mark.parametrize(
        "uut, index, expected",
        [
            (Loc(1), 0, 1),
            (Loc("spam"), 0, "spam"),
            (Loc("spam", "bar", 1, "baz"), 2, 1),
        ],
    )
    def test_getitem(self, uut, index, expected):
        assert uut[index] == expected

    @pytest.mark.parametrize(
        "uut, expected",
        [
            (Loc(), 0),
            (Loc("foo"), 1),
            (Loc("spam"), 1),
            (Loc("foo", "bar", 2), 3),
        ],
    )
    def test_len(self, uut, expected):
        assert len(uut) == expected

    @pytest.mark.parametrize(
        "left, right, is_equal",
        [
            (Loc(), Loc(), True),
            (Loc(1), Loc(), False),
            (Loc(), Loc(1), False),
            (Loc(1), Loc(1), True),
            (Loc("foo"), Loc("foo", 2), False),
        ],
    )
    def test_eq_and_ne_operators(self, left, right, is_equal):
        assert (left == right) == is_equal
        assert (left != right) == (not is_equal)

    @pytest.mark.parametrize(
        "left, right, expected_sum",
        [
            (Loc(), Loc(), Loc()),
            (Loc(1), Loc(2), Loc(1, 2)),
            (Loc("foo", "bar"), Loc("baz", "spam", 3), Loc("foo", "bar", "baz", "spam", 3)),
        ],
    )
    def test_concatenate_two_locs(self, left, right, expected_sum):
        assert left + right == expected_sum

    def test_slicing_returns_loc(self):
        uut = Loc("foo", "bar", 0, "baz")
        assert uut[1:] == Loc("bar", 0, "baz")
        assert uut[:2] == Loc("foo", "bar")

    def test_slicing_with_step_is_not_supported_for_loc(self):
        uut = Loc("foo", "bar", 0)
        with pytest.raises(TypeError):
            uut[::2]

    @pytest.mark.parametrize(
        "uut, pattern, status",
        [
            (Loc(), Loc("a"), False),
            (Loc("a"), Loc("a"), True),
            (Loc("a"), Loc("*"), True),
            (Loc(1), Loc(1), True),
            (Loc(1), Loc("*"), True),
            (Loc("a", "b"), Loc("b"), True),
            (Loc("a", "b"), Loc("a", "b"), True),
            (Loc("a", "b"), Loc("a", "*"), True),
            (Loc("a", "b"), Loc("a"), False),
        ],
    )
    def test_suffix_match(self, uut: Loc, pattern: Loc, status):
        assert uut.suffix_match(pattern) is status


class TestPattern:

    @pytest.mark.parametrize("uut, expected_len", [
        (Pattern(), 0),
        (Pattern("a", "b", 0), 3),
    ])
    def test_len(self, uut: Pattern, expected_len: int):
        assert len(uut) == expected_len

    def test_slicing_is_not_supported_for_pattern_objects(self):
        uut = Pattern("a", "b", 0)
        with pytest.raises(TypeError) as excinfo:
            a = uut[0:1]
        assert str(excinfo.value) == "slicing is not supported for Pattern type"

    @pytest.mark.parametrize("uut, index, expected_value", [
        (Pattern("a", "b", 0), 0, "a"),
        (Pattern("a", "b", 0), 1, "b"),
        (Pattern("a", "b", 0), -1, 0),
        (Pattern("a", "b", 0), -3, "a"),
    ])
    def test_get_item(self, uut: Pattern, index: int, expected_value):
        assert uut[index] == expected_value

    def test_comparing_with_non_pattern_returns_false(self):
        assert Pattern(123) != 123

    @pytest.mark.parametrize("left, right, are_equal", [
        (Pattern(), Pattern(), True),
        (Pattern("a"), Pattern(), False),
        (Pattern("a"), Pattern("a"), True),
    ])
    def test_compare_two_patterns(self, left: Pattern, right: Pattern, are_equal: bool):
        assert (left == right) is are_equal

    @pytest.mark.parametrize("uut, expected_repr", [
        (Pattern(), "Pattern()"),
        (Pattern("a"), "Pattern('a')"),
        (Pattern("a", "b"), "Pattern('a', 'b')"),
        (Pattern("a", "b", "?", 0), "Pattern('a', 'b', '?', 0)"),
    ])
    def test_repr(self, uut: Pattern, expected_repr: str):
        assert repr(uut) == expected_repr

    def test_wildcard_one(self):
        assert Pattern.wildcard_one() == Pattern("?")

    def test_wildcard_one_or_more(self):
        assert Pattern.wildcard_one_or_more() == Pattern("*")

    @pytest.mark.parametrize("uut, loc, status", [
        (Pattern(), Loc(), True),
        (Pattern(), Loc("a"), False),
        (Pattern("a"), Loc("a"), True),
        (Pattern("a"), Loc("b"), False),
        (Pattern("?"), Loc("b"), True),
        (Pattern("?", "?"), Loc("b"), False),
        (Pattern("?", "?"), Loc("a", "b"), True),
        (Pattern("*"), Loc("b"), True),
        (Pattern("*"), Loc(), False),
        (Pattern("a"), Loc("a", "b"), False),
        (Pattern("?"), Loc("a", "b"), False),
        (Pattern("*"), Loc("a", "b"), True),
        (Pattern("a", "b"), Loc("a", "b"), True),
        (Pattern("a", "b"), Loc("a", "c"), False),
        (Pattern("a", "?"), Loc("a", "c"), True),
        (Pattern("a", "*"), Loc("a", "c"), True),
        (Pattern("a", "b", "c"), Loc("a", "b", "c"), True),
        (Pattern("a", "b", "c"), Loc("a", "b", "d"), False),
        (Pattern("a", "?", "c"), Loc("a", "b", "c"), True),
        (Pattern("a", "*", "c"), Loc("a", "b", "c"), True),
        (Pattern("a", "*", "c"), Loc("a", "b", "d"), False),
        (Pattern("a", "*", "c"), Loc("a", "b", "d", "c"), True),
        (Pattern("a", "*", "c", 0), Loc("a", "b", "d", "c"), False),
        (Pattern("a", "*", "c", 0), Loc("a", "b", "d", "c", 0), True),
        (Pattern("a", "*", "*", "c", 0), Loc("a", "b", "d", "c", 0), True),
        (Pattern("a", "*", "c", "*", 2, 3), Loc("a", "b", "d", "c", 0, 1, 2, 3), True),
        (Pattern("a", "*", "*", "c", "*", 2, 3), Loc("a", "b", "d", "c", 0, 1, 2, 3), True),
        (Pattern("a", "*", "c", "*", 2, 3), Loc("a", "b", "d", "c", 0, 1, 2, 4), False),
        (Pattern("a", "*"), Loc("a", "b", "d", "c", 0, 1, 2, 4), True),
        (Pattern("*"), Loc("a", "b", "d", "c", 0, 1, 2, 4), True),
        (Pattern("**"), Loc("a", "b", "d", "c", 0, 1, 2, 4), True),
        (Pattern("**"), Loc(), True),
        (Pattern("**"), Loc("a"), True),
        (Pattern("**", "b"), Loc("a"), False),
        (Pattern("**", "b"), Loc("b"), True),
        (Pattern("**", "b"), Loc("b", "c"), False),
        (Pattern("**", "c"), Loc("b", "c"), True),
    ])
    def test_match(self, uut: Pattern, loc: Loc, status):
        assert uut.match(loc) is status
