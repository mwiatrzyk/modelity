from typing import Any, Generic, Optional, Type, TypeVar, Protocol

T = TypeVar("T")


class IParser(Protocol, Generic[T]):
    """Protocol representing parser that parses value of any type to object of
    type T."""

    def __call__(self, value: Any) -> T:
        """Try to parse *value* to instance of type T.

        On success, object of type T is returned, on failure - :exc:`ParsingError` is raised.

        :param value:
            The value to be parsed.
        """


class IParserRegistry(Protocol):
    """Represents connected collection of type parsers."""

    def require_parser(self, tp: Type[T]) -> IParser[T]:
        """Require parser for given type.

        Returns parser callable or raises :exc:`UnsupportedType` if parser was
        not found.
        """
