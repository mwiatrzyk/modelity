from typing import Any, Generic, Tuple, Type, TypeVar, Protocol, Union

from modelity.invalid import Invalid
from modelity.loc import Loc

T = TypeVar("T")


class IParser(Protocol, Generic[T]):
    """Protocol representing parser that parses value of any type to object of
    type T."""

    def __call__(self, value: Any, loc: Loc) -> Union[T, Invalid]:
        """Try to parse *value* to instance of type T.

        On success, object of type T is returned. On failure, :class:`Invalid`
        object is returned.

        :param value:
            The value to be parsed.

        :param loc:
            Optional location of the value.

            This is useful more a precise error reporting, for example when
            parsed value is part of some container.
        """


class IParserRegistry(Protocol):
    """Represents connected collection of type parsers."""

    def require_parser(self, tp: Type[T]) -> IParser[T]:
        """Require parser for given type.

        Returns parser callable or raises :exc:`UnsupportedType` if parser was
        not found.
        """
