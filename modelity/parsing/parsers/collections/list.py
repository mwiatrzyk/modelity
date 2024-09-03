import collections
import collections.abc
import itertools
from typing import Any, Iterable, get_args
from modelity.error import Error, ErrorCode
from modelity.exc import ParsingError
from modelity.invalid import Invalid
from modelity.parsing.interface import IParser, IParserRegistry
from modelity.parsing.registry import TypeParserRegistry

registry = TypeParserRegistry()


class _TypedList(collections.abc.MutableSequence):

    def __init__(self, loc: tuple, elements: list, element_parser: IParser):
        self._loc = loc
        self._elements = elements
        self._element_parser = element_parser

    def __eq__(self, value: object) -> bool:
        return self._elements == value

    def __repr__(self):
        return repr(self._elements)

    def __delitem__(self, index: int):
        del self._elements[index]

    def __getitem__(self, index: int):
        return self._elements[index]

    def __setitem__(self, index: int, value: Any):
        value = self._element_parser(value, self._loc)
        if isinstance(value, Invalid):
            raise ParsingError(value.errors)
        self._elements[index] = value

    def __len__(self):
        return len(self._elements)

    def insert(self, index: int, value: Any) -> None:
        value = self._element_parser(value, self._loc)
        if isinstance(value, Invalid):
            raise ParsingError(value.errors)
        return self._elements.insert(index, value)


@registry.type_parser_factory(list)
def make_list_parser(registry: IParserRegistry, tp: type):

    def parse_any_list(value, loc):
        if not isinstance(value, Iterable):
            return Invalid(value, Error.create(loc, ErrorCode.ITERABLE_REQUIRED))
        return list(value)

    def parse_typed_list(value, loc):
        if not isinstance(value, Iterable):
            return Invalid(value, Error.create(loc, ErrorCode.ITERABLE_REQUIRED))
        result = list(element_parser(x, loc + (i,)) for i, x in enumerate(value))
        errors = tuple(itertools.chain(*(x.errors for x in result if isinstance(x, Invalid))))
        if len(errors) > 0:
            return Invalid(value, *errors)
        return _TypedList(loc, result, element_parser)

    args = get_args(tp)
    if len(args) == 0:
        return parse_any_list
    element_parser = registry.require_parser(args[0])
    return parse_typed_list
