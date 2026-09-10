import sys

_version = sys.version_info.major, sys.version_info.minor

if _version >= (3, 14):
    from .py314 import __all__ as _all
    from .py314 import *
else:
    from .default import __all__ as _all
    from .default import *

__all__ = _all  # type: ignore
