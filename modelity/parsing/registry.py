import inspect
import abc
from typing import Callable, Optional, Type, get_origin

from modelity.exc import UnsupportedType

from .interface import T, IParser, IParserProvider


class TypeParserRegistry(IParserProvider):

    def __init__(self):
        self._type_parser_factories = {}

    def attach(self, other: "TypeParserRegistry"):
        self._type_parser_factories.update(other._type_parser_factories)

    def register_type_parser_factory(self, tp: Type, func: Callable):

        def proxy(root_registry: IParserProvider, tp: Type):
            kw = {}
            if "registry" in declared_params:
                kw["registry"] = root_registry
            if "tp" in declared_params:
                kw["tp"] = tp
            return func(**kw)

        sig = inspect.signature(func)
        declared_params = sig.parameters
        self._type_parser_factories[tp] = proxy

    def type_parser_factory(self, tp: Type) -> Callable:

        def decorator(func):
            self.register_type_parser_factory(tp, func)
            return func

        return decorator

    def provide_parser(self, tp: Type[T]) -> IParser[T]:
        make_parser = self._type_parser_factories.get(tp)
        if make_parser is not None:
            return make_parser(self, tp)
        origin = get_origin(tp)
        make_parser = self._type_parser_factories.get(origin)
        if make_parser is not None:
            return make_parser(self, tp)
        for base in inspect.getmro(tp):
            make_parser = self._type_parser_factories.get(base)
            if make_parser is not None:
                return make_parser(self, tp)
        for maybe_base, make_parser in self._type_parser_factories.items():
            if isinstance(maybe_base, type) and issubclass(tp, maybe_base):
                return make_parser(self, tp)
        raise UnsupportedType(tp)
