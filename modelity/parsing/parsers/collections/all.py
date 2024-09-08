from modelity.parsing.registry import TypeParserRegistry

from . import dict, list, set, tuple

registry = TypeParserRegistry()
registry.attach(dict.registry)
registry.attach(list.registry)
registry.attach(set.registry)
registry.attach(tuple.registry)
