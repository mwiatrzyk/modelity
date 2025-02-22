from typing import Annotated, Dict, List, Optional, Set, Type

import pytest

from mockify.api import Invoke, Raise, ordered, Return, _

from modelity.constraints import MaxLength
from modelity.error import Error, ErrorCode
from modelity.exc import ModelError, ParsingError, ValidationError
from modelity.invalid import Invalid
from modelity.loc import Loc
from modelity.model import (
    Config,
    field,
    field_validator,
    model_validator,
    BoundField,
    Model,
    postprocessor,
    preprocessor,
    _wrap_field_processor,
)
from modelity.unset import Unset

from tests.helpers import ErrorFactoryHelper


@pytest.fixture
def initial_params():
    return {}


@pytest.fixture
def model(model_type: Type[Model], initial_params: dict):
    return model_type(**initial_params)


@pytest.fixture
def config(model_type: Type[Model]):
    return model_type.__config__


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
    def expected_fields(self):
        return [
            ("a", BoundField(name="a", type=int)),
            ("b", BoundField(name="b", type=Optional[str])),
            ("c", BoundField(name="c", type=float, default=2.71)),
            ("d", BoundField(name="d", type=str, default="spam")),
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
            ({}, [("a", Unset), ("b", Unset), ("c", 2.71), ("d", "spam")]),
            ({"c": 3.14}, [("a", Unset), ("b", Unset), ("c", 3.14), ("d", "spam")]),
            (
                {"d": "more spam"},
                [("a", Unset), ("b", Unset), ("c", 2.71), ("d", "more spam")],
            ),
            ({"a": "123"}, [("a", 123), ("b", Unset), ("c", 2.71), ("d", "spam")]),
            ({"a": "123", "b": None}, [("a", 123), ("b", None), ("c", 2.71), ("d", "spam")]),
        ],
    )
    def test_create_model_object_successfully(self, model: Model, expected_values):
        for name, expected_value in expected_values:
            assert getattr(model, name) == expected_value

    @pytest.mark.parametrize(
        "initial_params, expected_errors",
        [
            ({"a": "spam"}, [ErrorFactoryHelper.integer_required(Loc("a"))]),
            (
                {"b": 123},
                [ErrorFactoryHelper.unsupported_type(Loc("b"), supported_types=(str, type(None)))],
            ),
            (
                {"a": "spam", "b": 123},
                [
                    ErrorFactoryHelper.integer_required(Loc("a")),
                    ErrorFactoryHelper.unsupported_type(Loc("b"), supported_types=(str, type(None))),
                ],
            ),
        ],
    )
    def test_creating_model_object_fails_if_one_or_more_params_have_incorrect_type(
        self, model_type: Type[Model], initial_params, expected_errors
    ):
        with pytest.raises(ParsingError) as excinfo:
            _ = model_type(**initial_params)
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize(
        "name, value, expected_errors",
        [
            ("a", "spam", [ErrorFactoryHelper.integer_required(Loc("a"))]),
            (
                "b",
                123,
                [ErrorFactoryHelper.unsupported_type(Loc("b"), supported_types=(str, type(None)))],
            ),
        ],
    )
    def test_setting_field_to_wrong_type_causes_parsing_error(self, model: Model, name, value, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            setattr(model, name, value)
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize(
        "name, value, expected_errors",
        [
            ("a", "spam", [ErrorFactoryHelper.integer_required(Loc("a"))]),
            (
                "b",
                123,
                [ErrorFactoryHelper.unsupported_type(Loc("b"), supported_types=(str, type(None)))],
            ),
        ],
    )
    def test_catch_parsing_errors_via_model_error_base_class(self, model: Model, name, value, expected_errors):
        with pytest.raises(ModelError) as excinfo:
            setattr(model, name, value)
        assert excinfo.value.errors == tuple(expected_errors)

    def test_setting_attribute_fails_if_it_is_not_a_field(self, model: Model):
        with pytest.raises(AttributeError) as excinfo:
            model.spam = 123
        assert str(excinfo.value) == "'Dummy' model has no field named 'spam'"

    def test_use_a_non_reserved_private_variable_as_field_name(self):

        class Dummy(Model):
            _foo: int

        uut = Dummy(_foo="123")
        assert list(uut) == ["_foo"]
        assert uut._foo == 123

    def test_validating_model_fails_if_required_fields_are_missing(self, model: Model):
        with pytest.raises(ValidationError) as excinfo:
            model.validate()
        assert excinfo.value.model is model
        assert excinfo.value.errors == tuple([ErrorFactoryHelper.required_missing(Loc("a"))])

    @pytest.mark.parametrize(
        "left, right, is_equal",
        [
            ({}, {}, True),
            ({"a": 1}, {"a": 1}, True),
            ({"a": 1}, {"a": 2}, False),
            ({"a": 1, "b": "spam"}, {"a": 1, "b": "spam"}, True),
            ({"a": 2, "b": "spam"}, {"a": 1, "b": "spam"}, False),
            ({"a": 2, "b": "spam"}, {"a": 2, "b": "more spam"}, False),
            ({"c": 2.71}, {}, True),
            ({"c": 2.71}, {"c": 3.14}, False),
            ({"d": "spam"}, {}, True),
            ({"d": "spam"}, {"d": "more spam"}, False),
        ],
    )
    def test_eq_and_ne_operators(self, model_type: Type[Model], left, right, is_equal):
        left = model_type(**left)
        right = model_type(**right)
        assert (left == right) == is_equal
        assert (left != right) == (not is_equal)

    def test_iterating_over_model_yields_fields_that_are_currently_set_in_field_declaration_order(
        self, model_type: Type[Model]
    ):
        model = model_type()
        assert list(model) == ["c", "d"]  # Defaults
        model.a = 1
        assert list(model) == ["a", "c", "d"]

    def test_when_field_is_set_to_unset_then_it_becomes_unset(self, model: Model):
        assert set(model) == {"c", "d"}
        model.c = Unset
        assert set(model) == {"d"}

    def test_when_field_is_deleted_then_it_becomes_unset(self, model: Model):
        assert set(model) == {"c", "d"}
        del model.c
        assert set(model) == {"d"}
        assert model.c == Unset

    def test_in_operator_can_be_used_to_check_if_the_field_is_set(self, model: Model):
        assert "c" in model
        assert "d" in model

    def test_two_different_models_inheriting_from_same_base_model_class_use_same_config_object(self):

        class Base(Model):
            __config__ = Config()

        class Nested(Base):
            foo: int

        class Owning(Base):
            nested: Nested

        assert Nested.__config__ is Owning.__config__
        assert Owning.__config__ is Base.__config__

    def test_change_config_after_inheriting_one_from_base(self):

        class Base(Model):
            __config__ = Config()

        class Nested(Base):
            __config__ = Config()
            foo: int

        class Owning(Base):
            nested: Nested

        assert Nested.__config__ is not Base.__config__
        assert Owning.__config__ is Base.__config__

    @pytest.mark.parametrize(
        "params, expected_errors",
        [
            ({"foo": "spam"}, [ErrorFactoryHelper.integer_required(Loc("foo"))]),
        ],
    )
    def test_load_valid_fails_on_parsing_error_if_wrong_value_is_given_for_field(self, params, expected_errors):

        class Dummy(Model):
            foo: int

        with pytest.raises(ParsingError) as excinfo:
            Dummy.load_valid(params)
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize(
        "params, expected_errors",
        [
            ({}, [ErrorFactoryHelper.required_missing(Loc("foo"))]),
        ],
    )
    def test_load_valid_fails_on_validation_error_if_validation_errors_are_found(self, params, expected_errors):

        class Dummy(Model):
            foo: int

        with pytest.raises(ValidationError) as excinfo:
            Dummy.load_valid(params)
        assert excinfo.value.errors == tuple(expected_errors)

    class TestModelTypeDeclaration:

        def test_model_type_cannot_be_declared_if_reserved_name_is_used_as_field_name(self):
            with pytest.raises(TypeError) as excinfo:

                class Dummy(Model):
                    validate: int

            assert str(excinfo.value) == "the name 'validate' is reserved by Modelity and cannot be used as field name"

    class TestDump:

        class Nested(Model):
            a: int

        @pytest.mark.parametrize(
            "tp, given, expected",
            [
                (int, {"foo": "1"}, {"foo": 1}),
                (int, {}, {"foo": Unset}),
                (float, {"foo": "1.41"}, {"foo": 1.41}),
                (str, {"foo": "dummy"}, {"foo": "dummy"}),
                (bool, {"foo": "on"}, {"foo": True}),
            ],
        )
        def test_dump_scalar_field(self, tp, given, expected):

            class Dummy(Model):
                foo: tp

            uut = Dummy(**given)
            assert uut.dump() == expected

        @pytest.mark.parametrize(
            "key_type, value_type, given, expected",
            [
                (str, int, {}, {"foo": Unset}),
                (str, int, {"foo": {"one": "1"}}, {"foo": {"one": 1}}),
                (int, Nested, {}, {"foo": Unset}),
                (int, Nested, {"foo": {}}, {"foo": {}}),
                (int, Nested, {"foo": {1: {"a": "1"}}}, {"foo": {1: {"a": 1}}}),
            ],
        )
        def test_dump_mapping_field(self, key_type, value_type, given, expected):

            class Dummy(Model):
                foo: Dict[key_type, value_type]

            uut = Dummy(**given)
            assert uut.dump() == expected

        @pytest.mark.parametrize(
            "value_type, given, expected",
            [
                (int, {}, {"foo": Unset}),
                (int, {"foo": []}, {"foo": []}),
                (int, {"foo": ["1", "2"]}, {"foo": [1, 2]}),
                (Dict[str, int], {}, {"foo": Unset}),
                (Dict[str, int], {"foo": []}, {"foo": []}),
                (Dict[str, int], {"foo": [{"one": "1"}, {"two": "2"}]}, {"foo": [{"one": 1}, {"two": 2}]}),
                (Nested, {}, {"foo": Unset}),
                (Nested, {"foo": []}, {"foo": []}),
                (Nested, {"foo": [{"a": "1"}]}, {"foo": [{"a": 1}]}),
            ],
        )
        def test_dump_sequence_field(self, value_type, given, expected):

            class Dummy(Model):
                foo: List[value_type]

            uut = Dummy(**given)
            assert uut.dump() == expected

        @pytest.mark.parametrize(
            "value_type, given, expected",
            [
                (int, {}, {"foo": Unset}),
                (int, {"foo": []}, {"foo": set()}),
                (int, {"foo": set()}, {"foo": set()}),
                (int, {"foo": ["1", "1", "2", "3"]}, {"foo": {1, 2, 3}}),
            ],
        )
        def test_dump_set_field(self, value_type, given, expected):

            class Dummy(Model):
                foo: Set[value_type]

            uut = Dummy(**given)
            assert uut.dump() == expected

        @pytest.mark.parametrize(
            "given, expected",
            [
                ({}, {"foo": Unset}),
                ({"foo": {}}, {"foo": {"a": Unset}}),
                ({"foo": {"a": "1"}}, {"foo": {"a": 1}}),
            ],
        )
        def test_dump_model_field(self, given, expected):
            Nested = self.Nested

            class Dummy(Model):
                foo: Nested

            uut = Dummy(**given)
            assert uut.dump() == expected

        class TestDumpModelWithCustomFilter:

            def test_skip_undefined_fields(self, mock):

                class Dummy(Model):
                    a: int

                uut = Dummy()
                mock.expect_call(Unset, Loc("a")).will_once(Return((Unset, True)))
                assert uut.dump(mock) == {}

            def test_return_another_value(self, mock):

                class Dummy(Model):
                    a: int

                uut = Dummy(a=1)
                mock.expect_call(1, Loc("a")).will_once(Return((11, False)))
                assert uut.dump(mock) == {"a": 11}

        class TestDumpMappingWithCustomFilter:

            def test_skip_fields(self, mock):

                class Dummy(Model):
                    foo: Dict[str, int]

                uut = Dummy(foo={"one": "1", "two": 2})
                mock.expect_call({"one": 1, "two": 2}, Loc("foo")).will_once(Invoke(lambda v, l: (v, False)))
                mock.expect_call(1, Loc("foo", "one")).will_once(Return((1, True)))
                mock.expect_call(2, Loc("foo", "two")).will_once(Return((2, False)))
                assert uut.dump(mock) == {"foo": {"two": 2}}

            def test_return_another_value(self, mock):

                class Dummy(Model):
                    a: int

                uut = Dummy(a=1)
                mock.expect_call(1, Loc("a")).will_once(Return((11, False)))
                assert uut.dump(mock) == {"a": 11}

        class TestDumpStrByteBytearraySubclasses:

            class Str(str):
                pass

            class Bytes(bytes):
                pass

            class Bytearray(bytearray):
                pass

            @pytest.mark.parametrize(
                "tp, value, expected_dump",
                [
                    (Str, Str("dummy"), {"foo": ["dummy"]}),
                    (Bytes, Bytes(b"dummy"), {"foo": [b"dummy"]}),
                ],
            )
            def test_dont_convert_str_byte_or_bytearray_subclasses_to_sequence(self, tp, value, expected_dump):

                class Dummy(Model):
                    foo: List[tp] = []

                dummy = Dummy()
                dummy.foo.append(value)
                assert dummy.dump() == expected_dump

        class TestDumpWithFunc:

            @pytest.fixture
            def func(self):
                return lambda v, l: (v, False)  # False - don't skip

            @pytest.mark.parametrize(
                "tp, given, expected",
                [
                    (int, "1", 1),
                    (float, "1.41", 1.41),
                    (str, "dummy", "dummy"),
                    (bool, "true", True),
                ],
            )
            def test_visit_scalar_field(self, mock, tp, given, expected, func):

                class Dummy(Model):
                    foo: tp

                uut = Dummy(foo=given)
                mock.expect_call(expected, Loc("foo")).will_once(Invoke(func))
                with ordered(mock):
                    assert uut.dump(mock)["foo"] == expected

            def test_visit_mapping_field(self, mock, func):

                class Dummy(Model):
                    foo: Dict[str, int]

                foo = {"a": 1, "b": 2}
                uut = Dummy(foo=foo)
                mock.expect_call(foo, Loc("foo")).will_once(Invoke(func))
                mock.expect_call(1, Loc("foo", "a")).will_once(Invoke(func))
                mock.expect_call(2, Loc("foo", "b")).will_once(Invoke(func))
                with ordered(mock):
                    assert uut.dump(mock) == {"foo": foo}

            def test_visit_mapping_field_with_values_being_another_mapping(self, mock, func):

                class Dummy(Model):
                    foo: Dict[str, Dict[str, int]]

                foo = {"a": {"b": 1}, "c": {"d": 2, "e": 3}}
                uut = Dummy(foo=foo)
                mock.expect_call(foo, Loc("foo")).will_once(Invoke(func))
                mock.expect_call({"b": 1}, Loc("foo", "a")).will_once(Invoke(func))
                mock.expect_call(1, Loc("foo", "a", "b")).will_once(Invoke(func))
                mock.expect_call({"d": 2, "e": 3}, Loc("foo", "c")).will_once(Invoke(func))
                mock.expect_call(2, Loc("foo", "c", "d")).will_once(Invoke(func))
                mock.expect_call(3, Loc("foo", "c", "e")).will_once(Invoke(func))
                with ordered(mock):
                    assert uut.dump(mock) == {"foo": foo}

            def test_visit_nested_model(self, mock, func):

                class Foo(Model):
                    a: int

                class Bar(Model):
                    foo: Foo

                foo = {"a": 1}
                uut = Bar(foo=foo)
                mock.expect_call(Foo(a=1), Loc("foo")).will_once(Invoke(func))
                mock.expect_call(1, Loc("foo", "a")).will_once(Invoke(func))
                with ordered(mock):
                    assert uut.dump(mock) == {"foo": foo}

            @pytest.mark.parametrize(
                "tp, given, expected",
                [
                    (int, ["1", "2"], [1, 2]),
                ],
            )
            def test_visit_sequence_field(self, mock, tp, given, expected, func):

                class Dummy(Model):
                    foo: List[tp]

                uut = Dummy(foo=given)
                mock.expect_call(expected, Loc("foo")).will_once(Invoke(func))
                for i, val in enumerate(expected):
                    mock.expect_call(val, Loc("foo", i)).will_once(Invoke(func))
                with ordered(mock):
                    assert uut.dump(mock) == {"foo": expected}

    class TestCustomConfig:

        @pytest.fixture
        def model_type(self, config):

            class Dummy(Model):
                __config__ = config

                a: int
                b: int

            return Dummy

        @pytest.mark.parametrize("config", [Config(None)])
        def test_if_custom_config_provided_then_it_overrides_default_one(self, model_type: Type[Model], config):
            assert model_type.__config__ is config

        @pytest.mark.parametrize("config", [Config(None)])
        def test_if_custom_config_provided_for_base_model_then_child_model_also_uses_that_config(
            self, model_type: Type[Model], config
        ):

            class Child(model_type):
                pass

            assert Child.__config__ is config

        @pytest.mark.parametrize("config", [Config(None)])
        def test_if_custom_config_provided_for_base_model_then_grandchild_model_also_uses_that_config(
            self, model_type: Type[Model], config
        ):

            class Child(model_type):
                pass

            class Grandchild(Child):
                pass

            assert Grandchild.__config__ is config

        def test_override_default_type_parser_provider(self, mock):

            class Dummy(Model):
                __config__ = Config(type_parser_provider=mock)

                a: int

            mock.provide_type_parser.expect_call(int, Dummy.__config__).will_once(Return(mock.parse_int))
            mock.parse_int.expect_call("123", Loc("a"), Dummy.__config__).will_once(Return(123))
            dummy = Dummy(a="123")
            assert dummy.a == 123

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
                ("a", BoundField(name="a", type=int)),
                ("b", BoundField(name="b", type=int)),
                ("c", BoundField(name="c", type=int)),
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
                ("a", BoundField(name="a", type=int)),
                ("b", BoundField(name="b", type=int)),
                ("c", BoundField(name="c", type=int)),
            ]

        def test_fields_declared_in_base_model_are_inherited_by_child_model(
            self, model_type: Type[Model], expected_field_names
        ):
            assert list(model_type.__fields__.keys()) == expected_field_names

    class TestValidation:

        def test_validate_simple_model(self):

            class Dummy(Model):
                a: int

            dummy = Dummy()
            with pytest.raises(ValidationError) as excinfo:
                dummy.validate()
            assert excinfo.value.errors == tuple([ErrorFactoryHelper.required_missing(Loc("a"))])

        def test_validation_errors_can_be_caught_using_model_error_type(self):

            class Dummy(Model):
                a: int

            dummy = Dummy()
            with pytest.raises(ModelError) as excinfo:
                dummy.validate()
            assert excinfo.value.errors == tuple([ErrorFactoryHelper.required_missing(Loc("a"))])

        def test_validate_nested_model(self):

            class Nested(Model):
                a: int

            class Dummy(Model):
                nested: Nested

            dummy = Dummy(nested=Nested())
            with pytest.raises(ValidationError) as excinfo:
                dummy.validate()
            assert excinfo.value.errors == tuple([ErrorFactoryHelper.required_missing(Loc("nested", "a"))])

        def test_validate_nested_model_wrapped_in_mapping(self):

            class Nested(Model):
                a: int

            class Dummy(Model):
                nested: Dict[str, Nested]

            dummy = Dummy(nested={"foo": Nested()})
            with pytest.raises(ValidationError) as excinfo:
                dummy.validate()
            assert excinfo.value.errors == tuple([ErrorFactoryHelper.required_missing(Loc("nested", "foo", "a"))])

        def test_validate_nested_model_wrapped_in_sequence(self):

            class Nested(Model):
                a: int

            class Dummy(Model):
                nested: List[Nested]

            dummy = Dummy(nested=[Nested()])
            with pytest.raises(ValidationError) as excinfo:
                dummy.validate()
            assert excinfo.value.errors == tuple([ErrorFactoryHelper.required_missing(Loc("nested", 0, "a"))])

        def test_validation_fails_if_constraints_fails_for_validated_field(self):

            class Dummy(Model):
                foo: Annotated[List[int], MaxLength(3)]

            dummy = Dummy(foo=["1", "2", "3"])
            assert dummy.foo == [1, 2, 3]
            dummy.foo.append("4")  # Not possible to check constraints from here
            assert dummy.foo == [1, 2, 3, 4]
            with pytest.raises(ValidationError) as excinfo:
                dummy.validate()
            assert excinfo.value.errors == tuple([ErrorFactoryHelper.value_too_long(Loc("foo"), 3)])

    class TestGetValue:

        @pytest.fixture
        def model_type(self):

            class Nested(Model):
                a: int

            class Dummy(Model):
                foo: int
                nested: Nested
                mapping: Dict[int, str]
                nested_mapping: Dict[int, Nested]
                list: List[int]
                nested_list: List[Nested]

            return Dummy

        @pytest.mark.parametrize(
            "initial_params, loc, expected_result",
            [
                ({}, Loc("a"), None),
                ({}, Loc("foo"), None),
                ({"foo": 1}, Loc("foo"), 1),
                ({"nested": {"a": 2}}, Loc("nested", "a"), 2),
                ({"mapping": {3: "three"}}, Loc("mapping", 3), "three"),
                ({"nested_mapping": {4: {"a": 444}}}, Loc("nested_mapping", 4, "a"), 444),
                ({"list": [111, 222, 333]}, Loc("list", 0), 111),
                ({"list": [111, 222, 333]}, Loc("list", 1), 222),
                ({"list": [111, 222, 333]}, Loc("list", 2), 333),
                ({"list": [111, 222, 333]}, Loc("list", 3), None),
                ({"list": [111, 222, 333]}, Loc("list", -1), 333),
                ({"list": [111, 222, 333]}, Loc("list", -2), 222),
                ({"list": [111, 222, 333]}, Loc("list", -3), 111),
                ({"list": [111, 222, 333]}, Loc("list", -4), None),
                ({"nested_list": [{"a": 5}]}, Loc("nested_list", 0, "a"), 5),
            ],
        )
        def test_get_value(self, model: Model, loc, expected_result):
            assert model.get_value(loc) == expected_result

        def test_when_memo_used_then_getting_same_loc_returns_memoized_value(self, model: Model, mock):
            model.foo = 123
            mock.get.expect_call(Loc("foo"), Unset).will_once(Return(Unset))
            mock.__setitem__.expect_call(Loc("foo"), 123)
            assert model.get_value(Loc("foo"), mock) == 123
            mock.get.expect_call(Loc("foo"), Unset).will_once(Return(123))
            assert model.get_value(Loc("foo"), mock) == 123


class TestNestedModel:

    class Child(Model):
        foo: int

    @pytest.fixture
    def model_type(self):

        class Parent(Model):
            child: self.Child

        return Parent

    @pytest.mark.parametrize(
        "initial_params, expected_foo",
        [
            ({"child": {"foo": "123"}}, 123),
        ],
    )
    def test_create_valid_model(self, model: Model, expected_foo):
        model.validate()
        assert model.child.foo == expected_foo

    @pytest.mark.parametrize(
        "initial_params, expected_errors",
        [
            ({}, [ErrorFactoryHelper.required_missing(Loc("child"))]),
            ({"child": {}}, [ErrorFactoryHelper.required_missing(Loc("child", "foo"))]),
        ],
    )
    def test_create_invalid_model(self, model: Model, expected_errors):
        with pytest.raises(ValidationError) as excinfo:
            model.validate()
        assert excinfo.value.model is model
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize(
        "given_child, expected_foo",
        [
            ({"foo": "123"}, 123),
        ],
    )
    def test_set_child_attribute_to_valid_value(self, model: Model, given_child, expected_foo):
        model.child = given_child
        assert model.child.foo == expected_foo

    @pytest.mark.parametrize(
        "given_child, expected_errors",
        [
            (None, [ErrorFactoryHelper.invalid_model(Loc("child"), Child)]),
            ({"foo": "spam"}, [ErrorFactoryHelper.integer_required(Loc("child", "foo"))]),
        ],
    )
    def test_set_child_attribute_to_invalid_value(self, model: Model, given_child, expected_errors):
        with pytest.raises(ParsingError) as excinfo:
            model.child = given_child
        assert excinfo.value.errors == tuple(expected_errors)

    def test_set_child_foo_to_valid_value(self, model: Model):
        model.child = {}
        model.child.foo = "123"
        assert model.child.foo == 123

    def test_set_child_foo_to_invalid_value(self, model: Model):
        model.child = {}
        with pytest.raises(ParsingError) as excinfo:
            model.child.foo = "spam"
        assert excinfo.value.errors == tuple([ErrorFactoryHelper.integer_required(Loc("child", "foo"))])


class TestFieldValidator:

    @pytest.fixture
    def model_type(self, mock):

        class Dummy(Model):
            foo: Optional[int]
            bar: Optional[int]

            @field_validator()
            def _validate_foo(name, value):
                return mock(name, value)

        return Dummy

    def test_field_validator_is_not_called_if_fields_are_not_set(self, model: Model):
        model.validate()

    def test_when_only_foo_field_set_then_validator_is_called_for_foo_field_only(self, model: Model, mock):
        model.foo = 123
        mock.expect_call("foo", 123)
        model.validate()

    def test_when_all_fields_set_then_validator_is_called_for_all_fields(self, model: Model, mock):
        model.foo = 123
        model.bar = 456
        mock.expect_call("foo", 123)
        mock.expect_call("bar", 456)
        with ordered(mock):
            model.validate()

    @pytest.mark.parametrize(
        "name, value, converted_value, given_error, expected_error",
        [
            (
                "foo",
                "123",
                123,
                ErrorFactoryHelper.value_error(Loc("foo"), "an error"),
                ErrorFactoryHelper.value_error(Loc("foo"), "an error"),
            ),
            (
                "foo",
                "123",
                123,
                ErrorFactoryHelper.value_error(Loc("foo", 1), "an error"),
                ErrorFactoryHelper.value_error(Loc("foo", 1), "an error"),
            ),
        ],
    )
    def test_when_validator_returns_error_then_validation_fails_with_that_error(
        self, model: Model, mock, name, value, converted_value, given_error, expected_error
    ):
        setattr(model, name, value)
        mock.expect_call(name, converted_value).will_once(Return(given_error))
        with pytest.raises(ValidationError) as excinfo:
            model.validate()
        assert excinfo.value.model == model
        assert excinfo.value.errors == tuple([expected_error])

    @pytest.mark.parametrize(
        "name, value, converted_value, given_errors, expected_errors",
        [
            (
                "foo",
                "123",
                123,
                [ErrorFactoryHelper.value_error(Loc("foo"), "an error")],
                [ErrorFactoryHelper.value_error(Loc("foo"), "an error")],
            ),
            (
                "foo",
                "123",
                123,
                [ErrorFactoryHelper.value_error(Loc("foo", 1), "an error")],
                [ErrorFactoryHelper.value_error(Loc("foo", 1), "an error")],
            ),
        ],
    )
    def test_when_validator_returns_tuple_of_errors_then_validation_fails_with_that_errors(
        self, model: Model, mock, name, value, converted_value, given_errors, expected_errors
    ):
        setattr(model, name, value)
        mock.expect_call(name, converted_value).will_once(Return(tuple(given_errors)))
        with pytest.raises(ValidationError) as excinfo:
            model.validate()
        assert excinfo.value.model == model
        assert excinfo.value.errors == tuple(expected_errors)

    @pytest.mark.parametrize(
        "name, value, exception, expected_error",
        [
            ("foo", 123, ValueError("an error"), ErrorFactoryHelper.value_error(Loc("foo"), "an error")),
            ("foo", 123, TypeError("an error"), ErrorFactoryHelper.type_error(Loc("foo"), "an error")),
        ],
    )
    def test_when_validator_raises_value_or_type_error_then_it_is_converted_to_error(
        self, model: Model, mock, name, value, exception, expected_error
    ):
        setattr(model, name, value)
        mock.expect_call(name, value).will_once(Raise(exception))
        with pytest.raises(ValidationError) as excinfo:
            model.validate()
        assert excinfo.value.errors == tuple([expected_error])

    def test_when_validator_declared_with_wrong_signature_then_raise_type_error(self):
        with pytest.raises(TypeError) as excinfo:

            class Dummy(Model):
                @field_validator("foo")
                def _validate_foo(value, name):
                    pass

        assert (
            str(excinfo.value)
            == "incorrect field validator's signature; (value, name) is not a subsequence of (cls, self, root, loc, name, value)"
        )

    def test_declare_validator_without_args(self, mock):
        class Dummy(Model):
            foo: int

            @field_validator()
            def _validate_foo():
                return mock()

        dummy = Dummy(foo=123)
        mock.expect_call()
        dummy.validate()

    def test_declare_validator_with_cls_only(self, mock):
        class Dummy(Model):
            foo: int

            @field_validator()
            def _validate_foo(cls):
                return mock(cls)

        dummy = Dummy(foo=123)
        mock.expect_call(Dummy)
        dummy.validate()

    def test_declare_validator_with_self_only(self, mock):
        class Dummy(Model):
            foo: int

            @field_validator()
            def _validate_foo(self):
                return mock(self)

        dummy = Dummy(foo=123)
        mock.expect_call(dummy)
        dummy.validate()

    def test_declare_validator_with_root_only(self, mock):
        class Nested(Model):
            foo: int

            @field_validator()
            def _validate_foo(root):
                return mock(root)

        class Root(Model):
            nested: Nested

        root = Root(nested={"foo": 123})
        mock.expect_call(root)
        root.validate()

    def test_declare_validator_with_loc_only(self, mock):
        class Nested(Model):
            foo: int

            @field_validator()
            def _validate_all(loc):
                return mock(loc)

        class Dummy(Model):
            nested: Nested

        dummy = Dummy(nested={"foo": 123})
        mock.expect_call(Loc("nested", "foo"))
        with ordered(mock):
            dummy.validate()

    def test_declare_validator_with_name_only(self, mock):
        class Dummy(Model):
            foo: int
            bar: int

            @field_validator()
            def _validate_all(name):
                return mock(name)

        dummy = Dummy(foo=123, bar=456)
        mock.expect_call("foo")
        mock.expect_call("bar")
        with ordered(mock):
            dummy.validate()

    def test_declare_validator_with_value_only(self, mock):
        class Dummy(Model):
            foo: int

            @field_validator()
            def _validate_foo(value):
                return mock(value)

        dummy = Dummy(foo=123)
        mock.expect_call(123)
        dummy.validate()

    class TestValidateSelectedField:

        @pytest.fixture
        def model_type(self, mock):

            class Dummy(Model):
                foo: Optional[int]
                bar: Optional[int]

                @field_validator("foo")
                def _validate_foo(name: str, value: int):
                    return mock(name, value)

            return Dummy

        def test_validator_is_not_triggered_if_field_is_not_set(self, model: Model):
            model.bar = 123
            model.validate()

        def test_validator_is_triggered_if_field_is_set(self, model: Model, mock):
            model.foo = 123
            mock.expect_call("foo", 123)
            model.validate()

    class TestMultipleValidators:

        @pytest.fixture
        def model_type(self, mock):

            class Dummy(Model):
                foo: Optional[int]
                bar: Optional[int]

                @field_validator("foo")
                def _validate_foo(name: str, value: int):
                    return mock.foo(name, value)

                @field_validator("bar")
                def _validate_bar(name: str, value: int):
                    return mock.bar(name, value)

            return Dummy

        def test_when_foo_set_then_run_foo_validator_only(self, model: Model, mock):
            model.foo = 123
            mock.foo.expect_call("foo", 123)
            model.validate()

        def test_when_bar_set_then_run_bar_validator_only(self, model: Model, mock):
            model.bar = 123
            mock.bar.expect_call("bar", 123)
            model.validate()

        def test_when_both_fields_set_then_run_both_validators(self, model: Model, mock):
            model.foo = 1
            model.bar = 2
            mock.foo.expect_call("foo", 1)
            mock.bar.expect_call("bar", 2)
            with ordered(mock):
                model.validate()

    class TestMultipleValidatorsForSameField:

        @pytest.fixture
        def model_type(self, mock):

            class Dummy(Model):
                foo: Optional[int]

                @field_validator("foo")
                def _validate_foo_1(name: str, value: int):
                    return mock.foo1(name, value)

                @field_validator("foo")
                def _validate_foo_2(name: str, value: int):
                    return mock.foo2(name, value)

            return Dummy

        def test_when_field_set_then_both_validators_are_called(self, model: Model, mock):
            model.foo = 123
            mock.foo1.expect_call("foo", 123).will_once(Raise(ValueError("first error")))
            mock.foo2.expect_call("foo", 123).will_once(Raise(ValueError("second error")))
            with pytest.raises(ValidationError) as excinfo:
                with ordered(mock):
                    model.validate()
            assert excinfo.value.errors == tuple(
                [
                    ErrorFactoryHelper.value_error(Loc("foo"), "first error"),
                    ErrorFactoryHelper.value_error(Loc("foo"), "second error"),
                ]
            )

    class TestInheritedValidator:

        @pytest.fixture
        def model_type(self, mock):

            class Base(Model):
                foo: Optional[int]

                @field_validator("foo")
                def _validate_base(name, value):
                    return mock.base(name, value)

            class Child(Base):

                @field_validator("foo")
                def _validate_child(name, value):
                    return mock.child(name, value)

            return Child

        @pytest.mark.parametrize("initial_params", [{"foo": 123}])
        def test_when_child_is_validated_then_validator_inherited_from_base_is_also_called(self, model: Model, mock):
            mock.base.expect_call("foo", 123)
            mock.child.expect_call("foo", 123)
            with ordered(mock):
                model.validate()

    class TestMixedInValidator:

        @pytest.fixture
        def model_type(self, mock):

            class Foo:
                foo: int

                @field_validator("foo")
                def _validate_foo(name, value):
                    return mock.foo(name, value)

            class Bar:
                bar: int

                @field_validator("bar")
                def _validate_bar(name, value):
                    return mock.bar(name, value)

            class Dummy(Model, Foo, Bar):
                pass

            return Dummy

        @pytest.mark.parametrize(
            "initial_params",
            [
                {"foo": 1, "bar": 2},
            ],
        )
        def test_when_class_is_validated_then_mixed_in_validators_are_also_called(self, model: Model, mock):
            mock.foo.expect_call("foo", 1)
            mock.bar.expect_call("bar", 2)
            with ordered(mock):
                model.validate()


class TestModelValidator:

    @pytest.fixture
    def model_type(self, mock):

        class Dummy(Model):
            foo: int

            @model_validator()
            def _validate_dummy():
                return mock()

        return Dummy

    @pytest.mark.parametrize("initial_params", [{"foo": 1}])
    def test_model_validator_is_called_when_validate_is_called(self, model: Model, mock):
        mock.expect_call()
        model.validate()

    @pytest.mark.parametrize(
        "validator_action, expected_errors",
        [
            (
                Return(ErrorFactoryHelper.value_error(Loc(), "an error")),
                [ErrorFactoryHelper.value_error(Loc(), "an error")],
            ),
            (
                Return(tuple([ErrorFactoryHelper.value_error(Loc(), "an error")])),
                [ErrorFactoryHelper.value_error(Loc(), "an error")],
            ),
            (
                Raise(ValueError("foo")),
                [ErrorFactoryHelper.value_error(Loc(), "foo")],
            ),
            (
                Raise(TypeError("bar")),
                [ErrorFactoryHelper.type_error(Loc(), "bar")],
            ),
            (Return(None), []),
        ],
    )
    def test_model_validator_is_called_after_built_in_validators(
        self, model: Model, mock, validator_action, expected_errors
    ):
        mock.expect_call().will_once(validator_action)
        with pytest.raises(ValidationError) as excinfo:
            model.validate()
        assert excinfo.value.errors == (ErrorFactoryHelper.required_missing(Loc("foo")),) + tuple(expected_errors)

    def test_when_declared_with_wrong_signature_then_type_error_is_raised(self):
        with pytest.raises(TypeError) as excinfo:

            class Dummy(Model):
                @model_validator()
                def _invalid_validator(cls, foo, model):
                    pass

        assert (
            str(excinfo.value)
            == "model validator '_invalid_validator' has incorrect signature: (cls, foo, model) is not a subsequence of (cls, self, root, loc, errors, config)"
        )

    def test_declare_with_cls_only(self, mock):

        class Dummy(Model):
            @model_validator()
            def _validator(cls):
                return mock(cls)

        dummy = Dummy()
        mock.expect_call(Dummy)
        dummy.validate()

    def test_declare_with_self_only(self, mock):

        class Dummy(Model):
            @model_validator()
            def _validator(self):
                return mock(self)

        dummy = Dummy()
        mock.expect_call(dummy)
        dummy.validate()

    def test_declare_with_root_only(self, mock):

        class Dummy(Model):
            @model_validator()
            def _validator(root):
                return mock(root)

        dummy = Dummy()
        mock.expect_call(dummy)
        dummy.validate()

    def test_declare_with_loc_only(self, mock):

        class Nested(Model):
            foo: int

            @model_validator()
            def _validator(loc):
                return mock(loc)

        class Dummy(Model):
            nested: Nested

        dummy = Dummy(nested={"foo": 123})
        mock.expect_call(Loc("nested"))
        dummy.validate()

    def test_declare_with_errors_only(self, mock):

        class Dummy(Model):
            foo: int

            @model_validator()
            def _validator(errors):
                return mock(errors)

        dummy = Dummy()
        mock.expect_call([ErrorFactoryHelper.required_missing(Loc("foo"))])
        with pytest.raises(ValidationError):
            dummy.validate()

    def test_declare_with_config_only(self, mock, config):

        class Dummy(Model):
            foo: int

            @model_validator()
            def _validator(config):
                return mock(config)

        dummy = Dummy()
        mock.expect_call(config)
        with pytest.raises(ValidationError):
            dummy.validate()

    class TestMultipleValidators:

        @pytest.fixture
        def model_type(self, mock):

            class Dummy(Model):
                foo: int

                @model_validator()
                def _first():
                    return mock.first()

                @model_validator()
                def _second():
                    return mock.second()

            return Dummy

        @pytest.mark.parametrize("initial_params", [{"foo": 123}])
        def test_validators_are_called_in_their_declaration_order(self, model: Model, mock):
            mock.first.expect_call()
            mock.second.expect_call()
            with ordered(mock):
                model.validate()

    class TestInheritedValidators:

        @pytest.fixture
        def model_type(self, mock):

            class Base(Model):

                @model_validator()
                def _validate_child():
                    return mock.base()

            class Child(Base):
                foo: int

                @model_validator()
                def _validate_child():
                    return mock.child()

            return Child

        @pytest.mark.parametrize("initial_params", [{"foo": 123}])
        def test_when_base_class_contains_validator_then_it_is_also_called_for_child_class(self, model: Model, mock):
            mock.base.expect_call()
            mock.child.expect_call()
            with ordered(mock):
                model.validate()

    class TestMixedInValidators:

        @pytest.fixture
        def model_type(self, mock):

            class Foo:

                @model_validator()
                def _validate_foo():
                    return mock.foo()

            class Bar:

                @model_validator()
                def _validate_bar():
                    return mock.bar()

            class Dummy(Model, Foo, Bar):
                pass

            return Dummy

        def test_validators_provided_by_mixins_are_also_called_when_validate_is_called(self, model: Model, mock):
            mock.foo.expect_call()
            mock.bar.expect_call()
            with ordered(mock):
                model.validate()

    class TestNestedModelValidation:

        @pytest.fixture
        def model_type(self, mock):

            class Child(Model):
                bar: Optional[int]

                @model_validator()
                def _validate_child(self, root: "Parent"):
                    return mock.child(self, root)

            class Parent(Model):
                foo: Optional[int]
                child: Optional[Child]

            return Parent

        @pytest.mark.parametrize("initial_params", [{"foo": 1, "child": {"bar": 2}}])
        def test_when_parent_is_validated_then_child_validator_receives_parent_model_as_root_argument(
            self, model: Model, mock
        ):
            mock.child.expect_call(model.child, model)
            model.validate()

        @pytest.mark.parametrize("initial_params", [{"foo": 1, "child": {"bar": 2}}])
        def test_when_child_validator_fails_then_it_contains_proper_error_location(self, model: Model, mock):
            mock.child.expect_call(model.child, model).will_once(Raise(ValueError("an error")))
            with pytest.raises(ValidationError) as excinfo:
                model.validate()
            assert excinfo.value.errors == tuple([ErrorFactoryHelper.value_error(Loc("child"), "an error")])

        @pytest.mark.parametrize("initial_params", [{"foo": 1, "child": {"bar": 2}}])
        def test_when_child_validator_fails_with_tuple_of_errors_then_reported_errors_contain_proper_error_location(
            self, model: Model, mock
        ):
            mock.child.expect_call(model.child, model).will_once(
                Return(
                    [
                        ErrorFactoryHelper.value_error(Loc("child", 1), "foo"),
                        ErrorFactoryHelper.value_error(Loc("child", 1), "bar"),
                    ]
                )
            )
            with pytest.raises(ValidationError) as excinfo:
                model.validate()
            assert excinfo.value.errors == tuple(
                [
                    ErrorFactoryHelper.value_error(Loc("child", 1), "foo"),
                    ErrorFactoryHelper.value_error(Loc("child", 1), "bar"),
                ]
            )

    class TestWithErrorsArg:

        def test_validation_fails_if_error_is_added_to_errors_list(self):

            class Dummy(Model):
                foo: int

                @model_validator()
                def _validate_model(errors: List[Error]):
                    errors.append(Error(Loc("foo"), "CUSTOM_ERROR", "custom error message"))

            dummy = Dummy(foo=123)
            with pytest.raises(ValidationError) as excinfo:
                dummy.validate()
            assert excinfo.value.errors == tuple(
                [
                    Error(Loc("foo"), "CUSTOM_ERROR", "custom error message"),
                ]
            )

        def test_model_validator_can_clear_errors_list(self):

            class Dummy(Model):
                foo: int

                @model_validator()
                def _validate_model(errors: List[Error]):
                    errors.clear()

            dummy = Dummy()
            dummy.validate()

    class TestWithPreOptionEnabled:

        @pytest.fixture
        def model_type(self):

            class Dummy(Model):
                foo: int

                @model_validator(pre=True)
                def _validate_model():
                    return ErrorFactoryHelper.value_error(Loc("dummy"), "an error")

            return Dummy

        def test_model_validator_with_pre_option_enabled_is_executed_before_any_other_validators(self, model: Model):
            with pytest.raises(ValidationError) as excinfo:
                model.validate()
            assert excinfo.value.errors == (
                ErrorFactoryHelper.value_error(Loc("dummy"), "an error"),
                ErrorFactoryHelper.required_missing(Loc("foo")),
            )


class TestWrapFieldProcessor:

    @pytest.fixture
    def model_type(self):

        class Dummy(Model):
            pass

        return Dummy

    def test_wrap_function_without_args(self, model: Model, mock, config):

        def func():
            return mock()

        wrapped = _wrap_field_processor(func)
        mock.expect_call().will_once(Return(123))
        result = wrapped(type(model), model, "foo", "spam", config)
        assert result == 123

    def test_wrap_function_with_cls_arg_only(self, model: Model, mock, config):

        def func(cls):
            return mock(cls)

        wrapped = _wrap_field_processor(func)
        mock.expect_call(type(model)).will_once(Return(123))
        result = wrapped(type(model), model, "foo", "spam", config)
        assert result == 123

    def test_wrap_function_with_loc_arg_only(self, model: Model, mock, config):

        def func(loc):
            return mock(loc)

        wrapped = _wrap_field_processor(func)
        mock.expect_call(Loc("foo")).will_once(Return(123))
        result = wrapped(type(model), Loc("foo"), "foo", "spam", config)
        assert result == 123

    def test_wrap_function_with_name_arg_only(self, model: Model, mock, config):

        def func(name):
            return mock(name)

        wrapped = _wrap_field_processor(func)
        mock.expect_call("foo").will_once(Return(123))
        result = wrapped(type(model), model, "foo", "spam", config)
        assert result == 123

    def test_wrap_function_with_value_arg_only(self, model: Model, mock, config):

        def func(value):
            return mock(value)

        wrapped = _wrap_field_processor(func)
        mock.expect_call("spam").will_once(Return(123))
        result = wrapped(type(model), model, "foo", "spam", config)
        assert result == 123

    def test_wrap_function_with_config_arg_only(self, model: Model, mock, config):

        def func(config):
            return mock(config)

        wrapped = _wrap_field_processor(func)
        mock.expect_call(config).will_once(Return(123))
        result = wrapped(type(model), model, "foo", "spam", config)
        assert result == 123

    def test_if_wrong_signature_of_wrapped_function_then_raise_type_error(self, model: Model):

        def func(cls, value, name):
            pass

        with pytest.raises(TypeError) as excinfo:
            _wrap_field_processor(func)
        assert (
            str(excinfo.value)
            == "field processor 'func' has incorrect signature: (cls, value, name) is not a subsequence of (cls, loc, name, value, config)"
        )

    @pytest.mark.parametrize(
        "given_exc, model_loc, field_name, field_value, expected_error",
        [
            (ValueError("an error"), Loc(), "foo", 123, ErrorFactoryHelper.value_error(Loc("foo"), "an error")),
            (
                ValueError("an error"),
                Loc("nested"),
                "foo",
                123,
                ErrorFactoryHelper.value_error(Loc("nested", "foo"), "an error"),
            ),
            (TypeError("an error"), Loc(), "foo", 123, ErrorFactoryHelper.type_error(Loc("foo"), "an error")),
            (
                TypeError("an error"),
                Loc("nested"),
                "foo",
                123,
                ErrorFactoryHelper.type_error(Loc("nested", "foo"), "an error"),
            ),
        ],
    )
    def test_if_wrapped_func_raises_type_or_value_error_then_exception_is_converted_to_invalid_object(
        self, model: Model, mock, given_exc, model_loc, field_name, field_value, expected_error, config
    ):

        def func():
            return mock()

        wrapped = _wrap_field_processor(func)
        mock.expect_call().will_once(Raise(given_exc))
        result = wrapped(type(model), model_loc + Loc(field_name), field_name, field_value, config)
        assert isinstance(result, Invalid)
        assert result.value == field_value
        assert result.errors == (expected_error,)

    @pytest.mark.parametrize(
        "field_name, field_value, model_loc, given_loc, expected_loc",
        [
            ("foo", 123, Loc(), Loc(), Loc("foo")),
            ("foo", 123, Loc(), Loc(1), Loc("foo", 1)),
            ("foo", 123, Loc("nested"), Loc(1), Loc("nested", "foo", 1)),
        ],
    )
    def test_if_wrapped_func_returns_invalid_object_then_new_invalid_object_with_updated_loc_is_returned(
        self, model: Model, mock, field_name, field_value, model_loc, given_loc, expected_loc, config
    ):

        def func():
            return mock()

        wrapped = _wrap_field_processor(func)
        mock.expect_call().will_once(
            Return(Invalid(field_value, ErrorFactoryHelper.value_error(given_loc, "an error")))
        )
        model.set_loc(model_loc)
        result = wrapped(type(model), model.get_loc() + Loc(field_name), field_name, field_value, config)
        assert isinstance(result, Invalid)
        assert result.value == field_value
        assert result.errors == (ErrorFactoryHelper.value_error(expected_loc, "an error"),)


class TestPreprocessor:

    @pytest.fixture
    def model_type(self, mock):

        class Dummy(Model):
            foo: int
            bar: int

            @preprocessor()
            def _preprocess_all(name, value):
                return mock(name, value)

        return Dummy

    def test_when_nothing_set_then_preprocessor_is_not_called(self, model_type: Type[Model]):
        model = model_type()
        assert model.foo == Unset
        assert model.bar == Unset

    def test_when_foo_set_then_preprocessor_is_only_called_for_foo(self, model_type: Type[Model], mock):
        mock.expect_call("foo", "spam").will_once(Return("123"))
        model = model_type(foo="spam")
        assert model.foo == 123
        assert model.bar == Unset

    def test_when_foo_and_bar_set_then_preprocessor_is_only_called_for_both(self, model_type: Type[Model], mock):
        mock.expect_call("foo", "spam").will_once(Return("123"))
        mock.expect_call("bar", "more spam").will_once(Return("456"))
        model = model_type(foo="spam", bar="more spam")
        assert model.foo == 123
        assert model.bar == 456

    def test_when_invalid_is_return_then_parsing_error_is_raised(self, model_type: Type[Model], mock):
        mock.expect_call("foo", "spam").will_once(
            Return(Invalid("spam", Error(Loc(), ErrorCode.VALUE_ERROR, msg="an error")))
        )
        with pytest.raises(ParsingError) as excinfo:
            model_type(foo="spam")
        assert excinfo.value.errors == tuple([ErrorFactoryHelper.value_error(Loc("foo"), "an error")])

    class TestPreprocessorForOneFieldOnly:

        @pytest.fixture
        def model_type(self, mock):

            class Dummy(Model):
                foo: int
                bar: int
                baz: int

                @preprocessor("bar")
                def _preprocess_bar(name, value):
                    return mock(name, value)

            return Dummy

        def test_set_one_field_having_no_preprocessor(self, model_type: Type[Model]):
            model = model_type(foo=123)
            assert model.foo == 123

        def test_set_one_field_having_preprocessor(self, model_type: Type[Model], mock):
            mock.expect_call("bar", 2).will_once(Return(22))
            model = model_type(foo=1, bar=2)
            assert model.foo == 1
            assert model.bar == 22

        def test_set_all_fields_expecting_preprocessor_to_be_called(self, model_type: Type[Model], mock):
            mock.expect_call("bar", 2).will_once(Return(22))
            model = model_type(foo=1, bar=2, baz=3)
            assert model.foo == 1
            assert model.bar == 22
            assert model.baz == 3

    class TestTwoPreprocessorsForFooField:

        @pytest.fixture
        def model_type(self, mock):

            class Dummy(Model):
                foo: int

                @preprocessor("foo")
                def _first(name, value):
                    return mock.first(name, value)

                @preprocessor("foo")
                def _second(name, value):
                    return mock.second(name, value)

            return Dummy

        def test_result_of_first_preprocessor_is_used_as_value_for_second_preprocessor(
            self, model_type: Type[Model], mock
        ):
            mock.first.expect_call("foo", 1).will_once(Return(2))
            mock.second.expect_call("foo", 2).will_once(Return(3))
            with ordered(mock):
                model = model_type(foo=1)
            assert model.foo == 3

        def test_if_first_preprocessor_fails_then_second_is_not_called(self, model_type, mock):
            mock.first.expect_call("foo", 1).will_once(Raise(ValueError("an error")))
            with pytest.raises(ParsingError) as excinfo:
                _ = model_type(foo=1)
            assert excinfo.value.errors == tuple([ErrorFactoryHelper.value_error(Loc("foo"), "an error")])

    class TestInheritedPreprocessors:

        @pytest.fixture
        def model_type(self, mock):

            class Base(Model):

                @preprocessor()
                def _preprocess_all(name, value):
                    return mock.base(name, value)

            class Child(Base):
                foo: int
                bar: int

                @preprocessor("foo")
                def _preprocess_bar(name, value):
                    return mock.child(name, value)

            return Child

        def test_preprocessors_from_base_class_are_also_executed_from_child_class(self, model_type, mock):
            mock.base.expect_call("foo", 1).will_once(Return(11))
            mock.child.expect_call("foo", 11).will_once(Return(111))
            mock.base.expect_call("bar", 2).will_once(Return(22))
            with ordered(mock):
                model = model_type(foo=1, bar=2)
            assert model.foo == 111
            assert model.bar == 22

    class TestMixedInPreprocessors:

        @pytest.fixture
        def model_type(self, mock):

            class Foo:

                @preprocessor()
                def _preprocess_foo(name, value):
                    return mock.foo(name, value)

            class Bar:

                @preprocessor()
                def _preprocess_bar(name, value):
                    return mock.bar(name, value)

            class Dummy(Model, Foo, Bar):
                foo: int

            return Dummy

        def test_mixed_in_preprocessors_are_also_executed(self, model_type, mock):
            mock.foo.expect_call("foo", 1).will_once(Return(11))
            mock.bar.expect_call("foo", 11).will_once(Return(111))
            with ordered(mock):
                model = model_type(foo=1)
            assert model.foo == 111

    class TestNestedModelPreprocessor:

        @pytest.fixture
        def model_type(self, mock):

            class Nested(Model):
                foo: int

                @preprocessor("foo")
                def _preprocess_foo(name, value):
                    return mock(name, value)

            class Parent(Model):
                nested: Nested

            return Parent

        def test_preprocessor_is_called_when_nested_field_is_initialized(self, model_type, mock):
            mock.expect_call("foo", 1).will_once(Return(11))
            model = model_type(**{"nested": {"foo": 1}})
            assert model.nested.foo == 11

        def test_preprocessor_is_called_when_nested_field_is_set(self, model_type, mock):
            model = model_type(**{"nested": {}})
            assert model.nested.foo == Unset
            mock.expect_call("foo", 1).will_once(Return(11))
            model.nested.foo = 1
            assert model.nested.foo == 11

        def test_when_preprocessor_fails_then_parse_error_is_raised(self, model_type, mock):
            mock.expect_call("foo", 1).will_once(Raise(ValueError("an error")))
            with pytest.raises(ParsingError) as excinfo:
                _ = model_type(nested={"foo": 1})
            assert excinfo.value.errors == tuple([ErrorFactoryHelper.value_error(Loc("nested", "foo"), "an error")])


class TestPostprocessor:

    @pytest.fixture
    def model_type(self, mock):

        class Dummy(Model):
            foo: int
            bar: int

            @postprocessor()
            def _postprocess_all(name, value):
                return mock(name, value)

        return Dummy

    def test_when_nothing_set_then_postprocessor_is_not_called(self, model_type: Type[Model]):
        model = model_type()
        assert model.foo == Unset
        assert model.bar == Unset

    def test_when_foo_set_then_postprocessor_is_only_called_for_foo(self, model_type: Type[Model], mock):
        mock.expect_call("foo", 1).will_once(Return(11))
        model = model_type(foo="1")
        assert model.foo == 11
        assert model.bar == Unset

    def test_when_foo_and_bar_set_then_preprocessor_is_called_for_both(self, model_type: Type[Model], mock):
        mock.expect_call("foo", 1).will_once(Return(11))
        mock.expect_call("bar", 2).will_once(Return(22))
        model = model_type(foo="1", bar="2")
        assert model.foo == 11
        assert model.bar == 22

    def test_when_invalid_is_return_then_parsing_error_is_raised(self, model_type: Type[Model], mock):
        mock.expect_call("foo", 1).will_once(Return(Invalid(1, Error(Loc(), ErrorCode.VALUE_ERROR, msg="an error"))))
        with pytest.raises(ParsingError) as excinfo:
            model_type(foo="1")
        assert excinfo.value.errors == tuple([ErrorFactoryHelper.value_error(Loc("foo"), "an error")])

    def test_postprocessor_is_not_called_when_value_is_invalid(self, model_type: Type[Model]):
        with pytest.raises(ParsingError) as excinfo:
            model_type(bar="spam")
        assert excinfo.value.errors == tuple([ErrorFactoryHelper.integer_required(Loc("bar"))])

    class TestPostprocessorForOneFieldOnly:

        @pytest.fixture
        def model_type(self, mock):

            class Dummy(Model):
                foo: int
                bar: int
                baz: int

                @postprocessor("bar")
                def _preprocess_bar(name, value):
                    return mock(name, value)

            return Dummy

        def test_set_one_field_having_no_postprocessor(self, model_type: Type[Model]):
            model = model_type(foo=123)
            assert model.foo == 123

        def test_set_one_field_having_postprocessor(self, model_type: Type[Model], mock):
            mock.expect_call("bar", 2).will_once(Return(22))
            model = model_type(foo=1, bar="2")
            assert model.foo == 1
            assert model.bar == 22

        def test_set_all_fields_expecting_postprocessor_to_be_called(self, model_type: Type[Model], mock):
            mock.expect_call("bar", 2).will_once(Return(22))
            model = model_type(foo=1, bar="2", baz=3)
            assert model.foo == 1
            assert model.bar == 22
            assert model.baz == 3

    class TestTwoPostprocessorsForFooField:

        @pytest.fixture
        def model_type(self, mock):

            class Dummy(Model):
                foo: int

                @postprocessor("foo")
                def _first(name, value):
                    return mock.first(name, value)

                @postprocessor("foo")
                def _second(name, value):
                    return mock.second(name, value)

            return Dummy

        def test_result_of_first_postprocessor_is_used_as_value_for_second_postprocessor(
            self, model_type: Type[Model], mock
        ):
            mock.first.expect_call("foo", 1).will_once(Return("2"))
            mock.second.expect_call("foo", "2").will_once(Return(3))
            with ordered(mock):
                model = model_type(foo="1")
            assert model.foo == 3

        def test_if_first_postprocessor_fails_then_second_is_not_called(self, model_type, mock):
            mock.first.expect_call("foo", 1).will_once(Raise(ValueError("an error")))
            with pytest.raises(ParsingError) as excinfo:
                _ = model_type(foo="1")
            assert excinfo.value.errors == tuple([ErrorFactoryHelper.value_error(Loc("foo"), "an error")])

    class TestInheritedPostprocessors:

        @pytest.fixture
        def model_type(self, mock):

            class Base(Model):

                @postprocessor()
                def _base(name, value):
                    return mock.base(name, value)

            class Child(Base):
                foo: int
                bar: int

                @postprocessor("foo")
                def _child(name, value):
                    return mock.child(name, value)

            return Child

        def test_postprocessors_from_base_class_are_also_executed_from_child_class(self, model_type, mock):
            mock.base.expect_call("foo", 1).will_once(Return("11"))
            mock.child.expect_call("foo", "11").will_once(Return(111))
            mock.base.expect_call("bar", 2).will_once(Return(22))
            with ordered(mock):
                model = model_type(foo="1", bar="2")
            assert model.foo == 111
            assert model.bar == 22

    class TestMixedInPostprocessors:

        @pytest.fixture
        def model_type(self, mock):

            class Foo:

                @postprocessor()
                def _foo(name, value):
                    return mock.foo(name, value)

            class Bar:

                @postprocessor()
                def _bar(name, value):
                    return mock.bar(name, value)

            class Dummy(Model, Foo, Bar):
                foo: int

            return Dummy

        def test_mixed_in_postprocessors_are_also_executed(self, model_type, mock):
            mock.foo.expect_call("foo", 1).will_once(Return("11"))
            mock.bar.expect_call("foo", "11").will_once(Return(111))
            with ordered(mock):
                model = model_type(foo="1")
            assert model.foo == 111

    class TestNestedModelPostprocessor:

        @pytest.fixture
        def model_type(self, mock):

            class Nested(Model):
                foo: int

                @postprocessor("foo")
                def _foo(name, value):
                    return mock(name, value)

            class Parent(Model):
                nested: Nested

            return Parent

        def test_postprocessor_is_called_when_nested_field_is_initialized(self, model_type, mock):
            mock.expect_call("foo", 1).will_once(Return(11))
            model = model_type(**{"nested": {"foo": "1"}})
            assert model.nested.foo == 11

        def test_postprocessor_is_called_when_nested_field_is_set(self, model_type, mock):
            model = model_type(**{"nested": {}})
            assert model.nested.foo == Unset
            mock.expect_call("foo", 1).will_once(Return(11))
            model.nested.foo = "1"
            assert model.nested.foo == 11

        def test_when_postprocessor_fails_then_parse_error_is_raised(self, model_type, mock):
            mock.expect_call("foo", 1).will_once(Raise(ValueError("an error")))
            with pytest.raises(ParsingError) as excinfo:
                _ = model_type(nested={"foo": "1"})
            assert excinfo.value.errors == tuple([ErrorFactoryHelper.value_error(Loc("nested", "foo"), "an error")])
