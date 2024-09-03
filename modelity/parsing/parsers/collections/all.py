from modelity.parsing.registry import TypeParserRegistry

from . import list, tuple

registry = TypeParserRegistry()
registry.attach(list.registry)
registry.attach(tuple.registry)
