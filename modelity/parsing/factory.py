from modelity.parsing.interface import IParserRegistry
from modelity.parsing.registry import ParserRegistry

from .types import simple, union


def create_default_parser_registry() -> IParserRegistry:
    registry = ParserRegistry()
    registry.attach(simple.registry)
    registry.attach(union.registry)
    return registry
