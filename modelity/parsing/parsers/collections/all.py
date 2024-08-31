from modelity.parsing.registry import TypeParserRegistry

from . import tuple

registry = TypeParserRegistry()
registry.attach(tuple.registry)
