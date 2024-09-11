from typing import Optional, Type

import pytest

from modelity.error import Error
from modelity.exc import ValidationError
from modelity.invalid import Invalid
from modelity.loc import Loc
from modelity.model import field, FieldInfo, Model
from modelity.undefined import Undefined


class TestModelType:

    @pytest.fixture
    def model_type(self):

        class Dummy(Model):
            a: int
            b: Optional[str]
            c: float = 2.71
            d: str = field(default="spam")

        return Dummy

    @pytest.fixture
    def initial_params(self):
        return {}

    @pytest.fixture
    def model(self, model_type: Type[Model], initial_params: dict):
        return model_type(**initial_params)

    @pytest.fixture
    def expected_fields(self):
        return [
            ("a", FieldInfo(name="a", type=int)),
            ("b", FieldInfo(name="b", type=Optional[str])),
            ("c", FieldInfo(name="c", type=float, default=2.71)),
            ("d", FieldInfo(name="d", type=str, default="spam")),
        ]

    @pytest.fixture
    def expected_field_names(self, expected_fields):
        return list(map(lambda x: x[0], expected_fields))

    def test_model_class_has_fields_attribute_set(self, model_type: Type[Model], expected_fields):
        assert list(model_type.__fields__.items()) == expected_fields

    def test_model_class_has_slots_attribute_set(self, model_type: Type[Model], expected_field_names):
        assert set(expected_field_names).issubset(model_type.__slots__)

    @pytest.mark.parametrize(
        "initial_params, expected_values",
        [
            ({}, [("a", Undefined), ("b", Undefined), ("c", 2.71), ("d", "spam")]),
            ({"c": 3.14}, [("a", Undefined), ("b", Undefined), ("c", 3.14), ("d", "spam")]),
            ({"d": "more spam"}, [("a", Undefined), ("b", Undefined), ("c", 2.71), ("d", "more spam")]),
            ({"a": "123"}, [("a", 123), ("b", Undefined), ("c", 2.71), ("d", "spam")]),
            ({"a": "123", "b": None}, [("a", 123), ("b", None), ("c", 2.71), ("d", "spam")]),
        ],
    )
    def test_create_model_object(self, model: Model, expected_values):
        for name, expected_value in expected_values:
            assert getattr(model, name) == expected_value

    @pytest.mark.parametrize("name, value, expected_error_codes", [
        ("a", "spam", ["modelity.IntegerRequired"]),
        ("b", 123, ["modelity.UnsupportedType"]),
    ])
    def test_setting_field_to_invalid_value_causes_invalid_to_be_set(self, model: Model, name, value, expected_error_codes):
        setattr(model, name, value)
        result = getattr(model, name)
        assert isinstance(result, Invalid)
        assert result.value == value
        assert result.error_codes == tuple(expected_error_codes)

    def test_validating_model_fails_if_required_fields_are_missing(self, model: Model):
        with pytest.raises(ValidationError) as excinfo:
            model.validate()
        assert excinfo.value.model is model
        assert excinfo.value.errors == tuple([Error.create(("a",), "modelity.RequiredMissing")])

    @pytest.mark.parametrize("initial_params, expected_errors", [
        ({"a": "spam"}, [Error.create(Loc("a"), "modelity.IntegerRequired")])
    ])
    def test_validating_model_fails_if_field_is_set_to_invalid_value(self, model: Model, expected_errors):
        with pytest.raises(ValidationError) as excinfo:
            model.validate()
        assert excinfo.value.model is model
        assert excinfo.value.errors == tuple(expected_errors)

    class TestInheritance:

        @pytest.fixture
        def model_type(self):

            class Base(Model):
                a: int

            class Child(Base):
                b: int
                c: int

            return Child

        @pytest.fixture
        def expected_fields(self):
            return [
                ("a", FieldInfo(name="a", type=int)),
                ("b", FieldInfo(name="b", type=int)),
                ("c", FieldInfo(name="c", type=int)),
            ]

        def test_fields_declared_in_base_model_are_inherited_by_child_model(
            self, model_type: Type[Model], expected_field_names
        ):
            assert list(model_type.__fields__.keys()) == expected_field_names

    class TestMixinInheritance:

        @pytest.fixture
        def model_type(self):

            class Foo:
                a: int

            class Bar:
                b: int

            class Dummy(Model, Foo, Bar):
                c: int

            return Dummy

        @pytest.fixture
        def expected_fields(self):
            return [
                ("a", FieldInfo(name="a", type=int)),
                ("b", FieldInfo(name="b", type=int)),
                ("c", FieldInfo(name="c", type=int)),
            ]

        def test_fields_declared_in_base_model_are_inherited_by_child_model(
            self, model_type: Type[Model], expected_field_names
        ):
            assert list(model_type.__fields__.keys()) == expected_field_names


class TestModel:

    @pytest.fixture
    def model_type(self):

        class Dummy(Model):
            a: int
            b: Optional[str]

        return Dummy

    @pytest.fixture
    def initial_args(self):
        return {}

    @pytest.fixture
    def model(self, model_type: Type[Model], initial_args):
        return model_type(**initial_args)

    @pytest.mark.parametrize("initial_args, expected_values", [({}, [("a", Undefined), ("b", Undefined)])])
    def test_create_model_object(self, model: Model, expected_values):
        for name, expected_value in expected_values:
            assert getattr(model, name) == expected_value
