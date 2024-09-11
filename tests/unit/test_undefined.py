import pytest

from modelity.undefined import Undefined, UndefinedType


def test_undefined_type_is_a_singleton():
    assert Undefined is UndefinedType()
    assert UndefinedType() is UndefinedType()


def test_repr_of_undefined():
    assert repr(Undefined) == "Undefined"


@pytest.mark.parametrize("left, right, is_equal", [
    (Undefined, Undefined, True),
    (Undefined, None, False),
    (Undefined, 0, False),
    (Undefined, "", False),
    (Undefined, False, False),
    (UndefinedType(), Undefined, True),
    (Undefined, UndefinedType(), True),
    (UndefinedType(), UndefinedType(), True),
])
def test_equality_checks(left, right, is_equal):
    computed_equality = left == right
    assert computed_equality == is_equal


def test_undefined_evaluates_to_false():
    assert (not Undefined) == True
    assert bool(Undefined) == False
