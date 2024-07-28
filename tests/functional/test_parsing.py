from types import NoneType
from typing import Any, Optional, Type, Union
import pytest

from modelity.exc import ParsingError
from modelity.parsing.factory import create_default_parser_registry
from modelity.parsing.interface import IParser, IParserRegistry


@pytest.fixture
def registry():
    return create_default_parser_registry()


@pytest.fixture
def parser(registry: IParserRegistry, tp: Type):
    return registry.require_parser(tp)


class TestSuccessfulParsing:

    @pytest.fixture(params=[
        (int, 1, 1),
        (int, 3.14, 3),
        (int, "4", 4),
        (str, "foo", "foo"),
        (str, "4", "4"),
        (type(None), None, None),
        (Optional[int], None, None),
        (Optional[int], 1, 1),
        (Optional[int], "2", 2),
        (Optional[str], None, None),
        (Optional[str], "foo", "foo"),
        (Union[int, str, NoneType], 0, 0),
        (Union[int, str, NoneType], "123", 123),
        (Union[int, str, NoneType], "foo", "foo"),
        (Union[int, str, NoneType], None, None),
    ])
    def data(self, request: pytest.FixtureRequest):
        return request.param

    @pytest.fixture
    def tp(self, data: tuple):
        return data[0]

    @pytest.fixture
    def given(self, data: tuple):
        return data[1]

    @pytest.fixture
    def expected(self, data: tuple):
        return data[2]

    def test_parse_value_successfully_and_return_expected_result(self, parser: IParser, given: Any, expected: Any):
        assert parser(given) == expected


class TestParsingErrors:

    @pytest.fixture(params=[
        (int, None, "Not a valid integer number"),
        (int, "foo", "Not a valid integer number"),
        (str, 123, "String value required"),
        (type(None), 123, "None value required"),
        (Optional[str], 123, "Unsupported type of input value; supported ones are: <class 'str'>, <class 'NoneType'>"),
        (Optional[int], "foo", "Unsupported type of input value; supported ones are: <class 'int'>, <class 'NoneType'>"),
    ])
    def data(self, request: pytest.FixtureRequest):
        return request.param

    @pytest.fixture
    def tp(self, data: tuple):
        return data[0]

    @pytest.fixture
    def given(self, data: tuple):
        return data[1]

    @pytest.fixture
    def expected_error(self, data: tuple):
        return data[2]

    def test_parsing_fails_if_input_value_cannot_be_parsed(self, parser: IParser, given: Any, expected_error: str):
        with pytest.raises(ParsingError) as excinfo:
            parser(given)
        assert str(excinfo.value) == expected_error
