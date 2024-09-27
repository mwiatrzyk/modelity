import functools
import inspect
from typing import Callable, Type, get_origin

from modelity.exc import UnsupportedType

from modelity.interface import T, IParser, ITypeParserFactory, ITypeParserProvider


class TypeParserProvider(ITypeParserProvider):
    """Class for creating type parser providers.

    It is used internally by the library for managing built-in type parsers,
    but can also be used to extend existing types with custom ones.
    """

    def __init__(self):
        self._type_parser_factories = {}

    def attach(self, other: "TypeParserProvider"):
        """Attach other type parser provider object to this one.

        As a result, all type parsers registered using ``other`` will be used
        by this provider. Please be aware that any types that exist in both
        providers will be overwritten with parsers taken from ``other``.

        :param other:
            Reference to provider to attach parsers from.
        """
        self._type_parser_factories.update(other._type_parser_factories)

    def register_type_parser_factory(self, tp: Type, func: Callable) -> ITypeParserFactory:
        """Attach type parser factory function.

        Returns ``func`` wrapped with :class:`ITypeParserFactory` interface.

        :param tp:
            Type to register parser for.

        :param func:
            Type parser factory function.

            This function can be declared with a subsequence (including empty)
            of arguments declared for :meth:`ITypeParserFactory.__call__`.
        """

        @functools.wraps(func)
        def proxy(provider: ITypeParserProvider, tp: Type):
            kw = {}
            if "provider" in declared_params:
                kw["provider"] = provider
            if "tp" in declared_params:
                kw["tp"] = tp
            return func(**kw)

        sig = inspect.signature(func)
        declared_params = sig.parameters
        self._type_parser_factories[tp] = proxy
        return proxy

    def type_parser_factory(self, tp: Type):
        """Decorator version of the :meth:`register_type_parser_factory` function.

        :param tp:
            The type to declare parser factory for.
        """

        def decorator(func):
            return self.register_type_parser_factory(tp, func)

        return decorator

    def provide_type_parser(self, tp: Type[T]) -> IParser[T]:
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
