import ipaddress

from typing import Any

from modelity.interface import IDumpFilter
from modelity.loc import Loc
from modelity.unset import Unset
from modelity.error import Error, ErrorFactory


def make_ipv4_address_type_descriptor():

    class IPv4TypeDescriptor:
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if isinstance(value, ipaddress.IPv4Address):
                return value
            try:
                return ipaddress.IPv4Address(value)
            except ipaddress.AddressValueError:
                errors.append(ErrorFactory.parsing_error(loc, value, "not a valid IPv4 address", ipaddress.IPv4Address))
                return Unset

        def dump(self, loc: Loc, value: Any, filter: IDumpFilter):
            return str(value)

        def validate(self, root, ctx, errors, loc, value):
            return

    return IPv4TypeDescriptor()
