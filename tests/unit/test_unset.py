import pytest

from modelity.unset import Unset, UnsetType


def test_unset_type_is_a_singleton():
    assert Unset is UnsetType()
    assert UnsetType() is UnsetType()


def test_repr_of_unset():
    assert repr(Unset) == "Unset"


@pytest.mark.parametrize(
    "left, right, is_equal",
    [
        (Unset, Unset, True),
        (Unset, None, False),
        (Unset, 0, False),
        (Unset, "", False),
        (Unset, False, False),
        (UnsetType(), Unset, True),
        (Unset, UnsetType(), True),
        (UnsetType(), UnsetType(), True),
    ],
)
def test_equality_checks(left, right, is_equal):
    computed_equality = left == right
    assert computed_equality == is_equal


def test_undefined_evaluates_to_false():
    assert (not Unset) == True
    assert bool(Unset) == False
