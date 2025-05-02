from typing import Optional
import pytest

from modelity.error import ErrorFactory
from modelity.exc import ParsingError
from modelity.loc import Loc
from modelity.model import BoundField, FieldInfo, Model, has_fields_set, make_type_descriptor
from modelity.unset import Unset


class TestBoundField:

    @pytest.fixture
    def name(self):
        return "foo"

    @pytest.fixture
    def type(self):
        return int

    @pytest.fixture
    def default(self):
        return Unset

    @pytest.fixture
    def field_info(self, default):
        return FieldInfo(default)

    @pytest.fixture
    def uut(self, name, type, field_info):
        return BoundField(name, type, make_type_descriptor(type), field_info)

    class TestOptional:

        @pytest.mark.parametrize(
            "type, expected_status",
            [
                (int, False),
                (Optional[int], True),
            ],
        )
        def test_check_if_field_is_optional(self, uut: BoundField, expected_status):
            assert uut.optional == expected_status

        @pytest.mark.parametrize(
            "field_info, expected_status",
            [
                (FieldInfo(optional=False), False),
                (FieldInfo(optional=True), True),
            ],
        )
        def test_check_if_field_is_optional_after_setting_field_info_optional_flag(
            self, uut: BoundField, expected_status
        ):
            assert uut.optional == expected_status

    class TestComputeDefault:

        @pytest.mark.parametrize(
            "field_info, expected_default",
            [
                (None, Unset),
                (FieldInfo(), Unset),
                (FieldInfo(None), None),
                (FieldInfo(123), 123),
                (FieldInfo(default_factory=lambda: 123), 123),
                (FieldInfo(123, lambda: 456), 123),
            ],
        )
        def test_compute_default(self, uut: BoundField, expected_default):
            assert uut.compute_default() == expected_default

        @pytest.mark.parametrize(
            "default",
            [
                [],
                set(),
                {},
                bytearray(),
            ],
        )
        def test_mutable_defaults_are_deep_copied(self, uut: BoundField, default):
            assert uut.compute_default() is not default


class TestModel:

    @pytest.fixture
    def args(self):
        return {}

    @pytest.fixture
    def uut(self, UUT, args):
        return UUT(**args)

    def test_comparing_model_to_non_model_returns_false(self):

        class UUT(Model):
            pass

        uut = UUT()
        assert uut != 123
        assert 123 != uut

    def test_instances_of_two_different_model_types_are_not_equal_even_if_fields_are_the_same(self):

        class A(Model):
            foo: int

        class B(Model):
            foo: int

        a = A(foo=1)
        b = B(foo=1)
        assert a != b

    class TestModelWithFooIntField:

        @pytest.fixture
        def field_info(self):
            return None

        @pytest.fixture
        def UUT(self, field_info):
            if field_info is None:

                class UUT(Model):
                    foo: int

                return UUT

            class UUT(Model):
                foo: int = field_info

            return UUT

        @pytest.mark.parametrize(
            "field_info, args, expected_value",
            [
                (None, {}, Unset),
                (None, {"foo": "0"}, 0),
                (FieldInfo(default="1"), {}, 1),
                (FieldInfo(default="2"), {"foo": "22"}, 22),
                (FieldInfo(default_factory=lambda: "3"), {}, 3),
                (FieldInfo(default_factory=lambda: "4"), {"foo": "44"}, 44),
            ],
        )
        def test_construct_new_model(self, UUT, args, expected_value):
            uut = UUT(**args)
            assert uut.foo == expected_value

        @pytest.mark.parametrize(
            "args, expected_errors",
            [
                ({"foo": "spam"}, [ErrorFactory.invalid_integer(Loc("foo"), "spam")]),
            ],
        )
        def test_construction_fails_if_argument_could_not_be_parsed_successfully(self, UUT, args, expected_errors):
            with pytest.raises(ParsingError) as excinfo:
                UUT(**args)
            assert excinfo.value.typ is UUT
            assert excinfo.value.errors == tuple(expected_errors)

        @pytest.mark.parametrize(
            "args, expected_repr",
            [
                ({}, "TestModel.TestModelWithFooIntField.UUT.<locals>.UUT(foo=Unset)"),
                ({"foo": "1"}, "TestModel.TestModelWithFooIntField.UUT.<locals>.UUT(foo=1)"),
            ],
        )
        def test_model_repr(self, uut, expected_repr):
            assert repr(uut) == expected_repr

        @pytest.mark.parametrize(
            "left, right, are_equal",
            [
                ({}, {}, True),
                ({"foo": 1}, {}, False),
                ({"foo": 1}, {"foo": 1}, True),
                ({"foo": 1}, {"foo": 2}, False),
                ({}, {"foo": 3}, False),
            ],
        )
        def test_equality_check(self, UUT, left, right, are_equal):
            assert (UUT(**left) == UUT(**right)) is are_equal
            assert (UUT(**right) == UUT(**left)) is are_equal

        @pytest.mark.parametrize(
            "given, expected",
            [
                (1, 1),
                ("2", 2),
                (3.14, 3),
            ],
        )
        def test_setting_field_invokes_value_parsing(self, uut, given, expected):
            uut.foo = given
            assert uut.foo == expected

        @pytest.mark.parametrize(
            "given, expected_errors",
            [
                ("spam", [ErrorFactory.invalid_integer(Loc("foo"), "spam")]),
            ],
        )
        def test_when_setting_field_to_invalid_value_then_parsing_error_is_raised(self, uut, given, expected_errors):
            with pytest.raises(ParsingError) as excinfo:
                uut.foo = given
            assert excinfo.value.typ is type(uut)
            assert excinfo.value.errors == tuple(expected_errors)

        def test_field_setting_fails_if_field_does_not_exist(self, uut):
            with pytest.raises(AttributeError) as excinfo:
                uut.non_existing_field = 123
            assert str(excinfo.value) == "'UUT' object has no attribute 'non_existing_field'"

        def test_deleting_attribute_sets_it_to_unset(self, uut):
            uut.foo = 123
            assert uut.foo == 123
            del uut.foo
            assert uut.foo is Unset

        def test_deleting_fails_if_field_does_not_exist(self, uut):
            with pytest.raises(AttributeError) as excinfo:
                del uut.non_existing_field
            assert str(excinfo.value) == "'UUT' object has no attribute 'non_existing_field'"

        def test_check_if_field_is_set_using_in_operator(self, uut):
            assert "foo" not in uut
            uut.foo = "123"
            assert "foo" in uut
            assert uut.foo == 123

        def test_iterating_over_model_generates_names_of_fields_set(self, uut):
            assert list(uut) == []
            uut.foo = 123
            assert list(uut) == ["foo"]
            del uut.foo
            assert list(uut) == []

        def test_check_if_model_has_at_least_one_field_set(self, uut):
            assert not has_fields_set(uut)
            uut.foo = 123
            assert has_fields_set(uut)

        def test_setting_field_to_unset_clears_it(self, uut):
            uut.foo = 123
            assert uut.foo == 123
            uut.foo = Unset
            assert uut.foo is Unset
