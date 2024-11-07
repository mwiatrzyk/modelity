import abc
from typing import List, get_args, get_origin
import pytest

from mockify.api import Return

from modelity.exc import UnsupportedType
from modelity.interface import ITypeParserProvider
from modelity.loc import Loc
from modelity.model import ModelConfig
from modelity.providers import CachingTypeParserProviderProxy, TypeParserProvider


class TestTypeParserProvider:

    @pytest.fixture
    def uut(self):
        return TypeParserProvider()

    @pytest.fixture
    def model_config(self, uut: ITypeParserProvider):
        return ModelConfig(type_parser_provider=uut)

    def test_register_function_taking_no_args(self, uut: TypeParserProvider, mock):

        def func():
            return mock()

        factory = uut.register_type_parser_factory(int, func)
        mock.expect_call().will_once(Return(mock.parser))
        assert factory(uut, int) is mock.parser

    def test_register_function_taking_model_config_arg(self, uut: TypeParserProvider, mock, model_config):

        def func(model_config):
            return mock(model_config)

        factory = uut.register_type_parser_factory(int, func)
        mock.expect_call(model_config).will_once(Return(mock.parser))
        assert factory(int, model_config) is mock.parser

    def test_register_function_taking_tp_arg(self, uut: TypeParserProvider, mock, model_config):

        def func(tp):
            return mock(tp)

        factory = uut.register_type_parser_factory(int, func)
        mock.expect_call(int).will_once(Return(mock.parser))
        assert factory(int, model_config) is mock.parser

    def test_register_function_taking_both_provider_and_tp_args(self, uut: TypeParserProvider, mock, model_config):

        def func(tp, model_config):
            return mock(tp, model_config)

        factory = uut.register_type_parser_factory(int, func)
        mock.expect_call(int, model_config).will_once(Return(mock.parser))
        assert factory(int, model_config) is mock.parser

    def test_registering_fails_if_func_is_declared_with_wrong_arguments(self, uut: TypeParserProvider):

        def func(tp, provider):
            pass

        with pytest.raises(TypeError) as excinfo:
            uut.register_type_parser_factory(int, func)
        assert (
            str(excinfo.value)
            == "incorrect type parser factory signature: (tp, provider) is not a subsequence of (tp, model_config)"
        )

    def test_register_type_parser_factory_for_simple_type(self, uut: TypeParserProvider, mock, model_config):

        @uut.type_parser_factory(int)
        def make_int_parser(tp):
            return mock(tp)

        mock.expect_call(int).will_once(Return(mock.parse_int))
        parser = uut.provide_type_parser(int, model_config)
        mock.parse_int.expect_call("123", Loc()).will_once(Return(123))
        assert parser("123", Loc()) == 123

    def test_register_type_parser_factory_for_simple_type(self, uut: TypeParserProvider, mock, model_config):

        @uut.type_parser_factory(int)
        def make_parser(tp):
            return mock(tp)

        mock.expect_call(int).will_once(Return(mock.parse))
        parser = uut.provide_type_parser(int, model_config)
        mock.parse.expect_call("123", Loc()).will_once(Return(123))
        assert parser("123", Loc()) == 123

    def test_register_type_parser_factory_for_typing_type(self, uut: TypeParserProvider, mock, model_config):

        @uut.type_parser_factory(list)
        def make_parser(tp):
            return mock(get_origin(tp), get_args(tp))

        mock.expect_call(list, (int,)).will_once(Return(mock.parse))
        parser = uut.provide_type_parser(List[int], model_config)
        mock.parse.expect_call(["123"], Loc()).will_once(Return([123]))
        assert parser(["123"], Loc()) == [123]

    def test_register_type_for_base_class(self, uut: TypeParserProvider, mock, model_config):

        class Base:
            pass

        class Child(Base):
            pass

        @uut.type_parser_factory(Base)
        def make_parser(tp):
            return mock(tp)

        mock.expect_call(Child).will_once(Return(mock.parse))
        parser = uut.provide_type_parser(Child, model_config)
        child = Child()
        mock.parse.expect_call(child, Loc()).will_once(Return(child))
        assert parser(child, Loc()) == child

    def test_register_type_for_abc_virtual_base_class(self, uut: TypeParserProvider, mock, model_config):

        class Base(abc.ABC):
            pass

        class Child:
            pass

        Base.register(Child)

        @uut.type_parser_factory(Base)
        def make_parser(tp):
            return mock(tp)

        mock.expect_call(Child).will_once(Return(mock.parse))
        parser = uut.provide_type_parser(Child, model_config)
        child = Child()
        mock.parse.expect_call(child, Loc()).will_once(Return(child))
        assert parser(child, Loc()) == child

    def test_provide_type_parser_fails_if_no_type_parser_factory_was_found(self, uut: TypeParserProvider, model_config):
        with pytest.raises(UnsupportedType) as excinfo:
            uut.provide_type_parser(int, model_config)
        assert excinfo.value.tp == int

    # def test_when_no_root_given_then_uut_is_passed_as_provider(self, uut: TypeParserProvider, mock):

    #     def create_parser(provider):
    #         return mock.parse(provider)

    #     uut.register_type_parser_factory(int, create_parser)
    #     mock.parse.expect_call(uut)
    #     uut.provide_type_parser(int)

    # def test_when_root_given_then_given_root_is_passed_as_provider(self, uut: TypeParserProvider, mock):

    #     def create_parser(provider):
    #         return mock.parse(provider)

    #     uut.register_type_parser_factory(int, create_parser)
    #     mock.parse.expect_call(mock.root)
    #     uut.provide_type_parser(int, model_config=mock.root)


class TestCachingTypeParserProvider:
    UUT = CachingTypeParserProviderProxy

    @pytest.fixture
    def uut(self, mock):
        return CachingTypeParserProviderProxy(mock)

    @pytest.fixture
    def model_config(self, uut: ITypeParserProvider):
        return ModelConfig(type_parser_provider=uut)

    def test_when_parser_created_for_the_first_time_then_use_target_to_find_provider(self, uut: UUT, mock, model_config):
        mock.provide_type_parser.expect_call(int, model_config).will_once(Return(mock.parse_int))
        assert uut.provide_type_parser(int, model_config) is mock.parse_int

    def test_when_parser_created_for_the_second_time_then_reuse_parser_created_earlier(self, uut: UUT, mock, model_config):
        mock.provide_type_parser.expect_call(int, model_config).will_once(Return(mock.parse_int))
        assert uut.provide_type_parser(int, model_config) is mock.parse_int
        assert uut.provide_type_parser(int, model_config) is mock.parse_int
