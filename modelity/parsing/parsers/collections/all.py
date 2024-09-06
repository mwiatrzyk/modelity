from modelity.parsing.registry import TypeParserRegistry

from . import dict, list, tuple

registry = TypeParserRegistry()
registry.attach(dict.registry)
registry.attach(list.registry)
registry.attach(tuple.registry)
