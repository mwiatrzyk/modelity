import pytest

from modelity.constraints import MaxLength, MaxValue, MinLength, MinValue
from modelity.invalid import Invalid
from modelity.loc import Loc

from tests.helpers import ErrorFactoryHelper


class TestMinValue:

    @pytest.mark.parametrize(
        "min_inclusive, min_exclusive, expected_error",
        [
            (None, None, "__init__() requires either 'min_inclusive' or 'min_exclusive' argument to be provided"),
            (0, 0, "__init__() cannot be called with both 'min_inclusive' and 'min_exclusive' arguments"),
        ],
    )
    def test_init_fails_if_called_with_invalid_combination_of_params(
        self, min_inclusive, min_exclusive, expected_error
    ):
        with pytest.raises(TypeError) as excinfo:
            MinValue(min_inclusive=min_inclusive, min_exclusive=min_exclusive)
        assert str(excinfo.value) == expected_error

    @pytest.mark.parametrize(
        "uut, value, loc",
        [
            (MinValue(min_inclusive=0), 0, Loc()),
            (MinValue(min_exclusive=0), 1, Loc()),
        ],
    )
    def test_constraint_checking_passed(self, uut, value, loc):
        result = uut(value, loc)
        assert result == value

    @pytest.mark.parametrize(
        "uut, value, loc, expected_error",
        [
            (MinValue(min_inclusive=0), -1, Loc(), ErrorFactoryHelper.value_too_low(Loc(), min_inclusive=0)),
            (MinValue(min_exclusive=0), -1, Loc(), ErrorFactoryHelper.value_too_low(Loc(), min_exclusive=0)),
            (MinValue(min_exclusive=0), 0, Loc(), ErrorFactoryHelper.value_too_low(Loc(), min_exclusive=0)),
        ],
    )
    def test_constraint_checking_failed(self, uut, value, loc, expected_error):
        result = uut(value, loc)
        assert isinstance(result, Invalid)
        assert result.value == value
        assert result.errors == (expected_error,)


class TestMaxValue:

    @pytest.mark.parametrize(
        "max_inclusive, max_exclusive, expected_error",
        [
            (None, None, "__init__() requires either 'max_inclusive' or 'max_exclusive' argument to be provided"),
            (0, 0, "__init__() cannot be called with both 'max_inclusive' and 'max_exclusive' arguments"),
        ],
    )
    def test_init_fails_if_called_with_invalid_combination_of_params(
        self, max_inclusive, max_exclusive, expected_error
    ):
        with pytest.raises(TypeError) as excinfo:
            MaxValue(max_inclusive=max_inclusive, max_exclusive=max_exclusive)
        assert str(excinfo.value) == expected_error

    @pytest.mark.parametrize(
        "uut, value, loc",
        [
            (MaxValue(max_inclusive=0), 0, Loc()),
            (MaxValue(max_exclusive=0), -1, Loc()),
        ],
    )
    def test_constraint_checking_passed(self, uut, value, loc):
        result = uut(value, loc)
        assert result == value

    @pytest.mark.parametrize(
        "uut, value, loc, expected_error",
        [
            (MaxValue(max_inclusive=0), 1, Loc(), ErrorFactoryHelper.value_too_high(Loc(), max_inclusive=0)),
            (MaxValue(max_exclusive=0), 1, Loc(), ErrorFactoryHelper.value_too_high(Loc(), max_exclusive=0)),
            (MaxValue(max_exclusive=0), 0, Loc(), ErrorFactoryHelper.value_too_high(Loc(), max_exclusive=0)),
        ],
    )
    def test_constraint_checking_failed(self, uut, value, loc, expected_error):
        result = uut(value, loc)
        assert isinstance(result, Invalid)
        assert result.value == value
        assert result.errors == (expected_error,)


class TestMinLength:

    @pytest.mark.parametrize(
        "uut, value, loc",
        [
            (MinLength(3), "foo", Loc()),
        ],
    )
    def test_constraint_checking_passed(self, uut, value, loc):
        result = uut(value, loc)
        assert result == value

    @pytest.mark.parametrize(
        "uut, value, loc, expected_error",
        [
            (MinLength(1), "", Loc(), ErrorFactoryHelper.value_too_short(Loc(), 1)),
        ],
    )
    def test_constraint_checking_failed(self, uut, value, loc, expected_error):
        result = uut(value, loc)
        assert isinstance(result, Invalid)
        assert result.value == value
        assert result.errors == (expected_error,)


class TestMaxLength:

    @pytest.mark.parametrize(
        "uut, value, loc",
        [
            (MaxLength(3), "foo", Loc()),
        ],
    )
    def test_constraint_checking_passed(self, uut, value, loc):
        result = uut(value, loc)
        assert result == value

    @pytest.mark.parametrize(
        "uut, value, loc, expected_error",
        [
            (MaxLength(1), "foo", Loc(), ErrorFactoryHelper.value_too_long(Loc(), 1)),
        ],
    )
    def test_constraint_checking_failed(self, uut, value, loc, expected_error):
        result = uut(value, loc)
        assert isinstance(result, Invalid)
        assert result.value == value
        assert result.errors == (expected_error,)
