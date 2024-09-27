import pytest

from mockify.api import Return

from modelity.parsing.providers import TypeParserProvider


class TestTypeParserProvider:

    @pytest.fixture
    def uut(self):
        return TypeParserProvider()

    def test_register_function_taking_no_args(self, uut: TypeParserProvider, mock):

        def func():
            return mock()

        factory = uut.register_type_parser_factory(int, func)
        mock.expect_call()
        factory(uut, int)
