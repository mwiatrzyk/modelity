import sys

import dataclasses

_version = (sys.version_info.major, sys.version_info.minor)

if _version == (3, 9):

    def dataclass(**kwargs):
        kwargs.pop("slots", None)
        return dataclasses.dataclass(**kwargs)

else:
    dataclass = dataclasses.dataclass
