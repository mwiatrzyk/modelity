import functools
import inspect
from typing import Any, Callable, Dict, Iterator, Optional, Type, get_origin

from modelity import _utils
from modelity.exc import UnsupportedType
from modelity.interface import T, IConfig, IParser, ITypeParserFactory, ITypeParserProvider


class TypeParserProvider:
    """Class for creating type parser providers.

    It is used internally by the library for managing built-in type parsers,
    but can also be used to extend existing types with custom ones.
    """

    def __init__(self) -> None:
        self._type_parser_factories: Dict[Any, ITypeParserFactory] = {}

    def attach(self, other: ITypeParserProvider):
        """Attach other type parser provider object to this one.

        As a result, all type parsers registered for *other* will be used
        by this provider. Please be aware that any types that existed in both
        providers will be replaced with ones taken from *other* after this
        method is called.

        :param other:
            Reference to provider to attach parsers from.
        """
        for tp in other.iter_types():
            parser_factory = other.get_type_parser_factory(tp)
            if parser_factory is not None:
                self._type_parser_factories[tp] = parser_factory

    def iter_types(self) -> Iterator[Type]:
        return iter(self._type_parser_factories)

    def has_type(self, tp: Type) -> bool:
        return tp in self._type_parser_factories

    def get_type_parser_factory(self, tp: Type[T]) -> Optional[ITypeParserFactory[T]]:
        return self._type_parser_factories.get(tp)

    def register_type_parser_factory(self, tp: Any, func: Callable) -> ITypeParserFactory[T]:
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
        def proxy(tp: Type[T], model_config: IConfig) -> IParser[T]:
            kw: Dict[str, Any] = {}
            if "tp" in declared_params:
                kw["tp"] = tp
            if "model_config" in declared_params:
                kw["model_config"] = model_config
            return func(**kw)

        sig = inspect.signature(func)
        declared_params = sig.parameters
        allowed_params = ("tp", "model_config")
        if not _utils.is_subsequence(declared_params, allowed_params):
            raise TypeError(
                f"incorrect type parser factory signature: {_utils.format_signature(declared_params)} is not a subsequence of {_utils.format_signature(allowed_params)}"
            )
        self._type_parser_factories[tp] = proxy
        return proxy

    def type_parser_factory(self, tp: Any):
        """Decorator version of the :meth:`register_type_parser_factory` function.

        :param tp:
            The type to declare parser factory for.
        """

        def decorator(func):
            return self.register_type_parser_factory(tp, func)

        return decorator

    def provide_type_parser(self, tp: Type[T], model_config: IConfig) -> IParser[T]:
        make_parser = self._type_parser_factories.get(tp)
        if make_parser is not None:
            return make_parser(tp, model_config)
        origin = get_origin(tp)
        make_parser = self._type_parser_factories.get(origin)
        if make_parser is not None:
            return make_parser(tp, model_config)
        for base in inspect.getmro(tp):
            make_parser = self._type_parser_factories.get(base)
            if make_parser is not None:
                return make_parser(tp, model_config)
        for maybe_base, make_parser in self._type_parser_factories.items():
            if isinstance(maybe_base, type) and issubclass(tp, maybe_base):
                return make_parser(tp, model_config)
        raise UnsupportedType(tp)


class CachingTypeParserProviderProxy:
    """Proxy type parser provider with cache support.

    :param target:
        The target provider.
    """
    __slots__ = ("_target", "_cache")

    def __init__(self, target: ITypeParserProvider):
        self._target = target
        self._cache: Dict[Type, IParser] = {}

    def iter_types(self) -> Iterator[Type]:
        return self._target.iter_types()

    def has_type(self, tp: Type) -> bool:
        return self._target.has_type(tp)

    def get_type_parser_factory(self, tp: Type[T]) -> Optional[ITypeParserFactory[T]]:
        return self._target.get_type_parser_factory(tp)

    def provide_type_parser(self, tp: Type[T], model_config: IConfig) -> IParser[T]:
        if tp not in self._cache:
            self._cache[tp] = self._target.provide_type_parser(tp, model_config)
        return self._cache[tp]
