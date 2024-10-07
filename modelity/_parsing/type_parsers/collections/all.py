from modelity.providers import TypeParserProvider

from . import dict, list, set, tuple

provider = TypeParserProvider()
provider.attach(dict.provider)
provider.attach(list.provider)
provider.attach(set.provider)
provider.attach(tuple.provider)
