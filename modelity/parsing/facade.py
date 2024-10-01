"""Facade for the :mod:`modelity.parsing` module."""

from modelity.parsing.providers import TypeParserProvider

from ._type_parsers.all import provider as _root_provider


def get_builtin_type_parser_provider() -> TypeParserProvider:
    """Obtain reference to the root type parser provider object containing
    parsers for all built-in types."""
    return _root_provider
