from typing import List, Literal, Mapping, Set
import pytest

from modelity._utils import describe, is_subsequence


class Dummy:

    class Nested:
        pass


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


@pytest.mark.parametrize("obj, expected_result", [
    (str, "str"),
    (bytes, "bytes"),
    (int, "int"),
    (float, "float"),
    (Dummy, "Dummy"),
    (Dummy.Nested, "Dummy.Nested"),
    (Set, "set"),
    (Set[str], "set[str]"),
    (List, "list"),
    (List[int], "list[int]"),
    (Mapping, "Mapping"),
    (Mapping[str, int], "Mapping[str, int]"),
    (list[str], "list[str]"),
    (list[Dummy], "list[Dummy]"),
    (tuple[Dummy.Nested, ...], "tuple[Dummy.Nested, ...]"),
    (tuple[Dummy.Nested, ...], "tuple[Dummy.Nested, ...]"),
    (dict, "dict"),
    (dict[str, dict[str, float]], "dict[str, dict[str, float]]"),
    (Literal[1, 3.14, "spam"], "Literal[1, 3.14, 'spam']"),
    ("spam", "'spam'"),
    (b"spam", "b'spam'"),
    (123, "123"),
    (None, "None"),
    ([], "[]"),
    ([1, 3.14, "spam"], "[1, 3.14, 'spam']"),
    ([1, 3.14, "spam", Literal["on", "off"]], "[1, 3.14, 'spam', Literal['on', 'off']]"),
    ((1, 3.14, "spam", Literal["on", "off"]), "(1, 3.14, 'spam', Literal['on', 'off'])"),
    ({"types": [Literal[1, 2, 3]]}, "{'types': [Literal[1, 2, 3]]}")
])
def test_describe(obj, expected_result):
    assert describe(obj) == expected_result
