import ipaddress

from typing import Any

from modelity.loc import Loc
from modelity.unset import Unset
from modelity.error import Error, ErrorFactory
from modelity.mixins import StrDumpMixin, EmptyValidateMixin


def make_ipv4_address_type_descriptor():

    class IPv4TypeDescriptor(StrDumpMixin, EmptyValidateMixin):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if isinstance(value, ipaddress.IPv4Address):
                return value
            try:
                return ipaddress.IPv4Address(value)
            except ipaddress.AddressValueError:
                errors.append(ErrorFactory.parsing_error(loc, value, "not a valid IPv4 address", ipaddress.IPv4Address))
                return Unset

    return IPv4TypeDescriptor()


def make_ipv6_address_type_descriptor():

    class IPv6TypeDescriptor(StrDumpMixin, EmptyValidateMixin):
        def parse(self, errors: list[Error], loc: Loc, value: Any):
            if isinstance(value, ipaddress.IPv6Address):
                return value
            try:
                return ipaddress.IPv6Address(value)
            except ipaddress.AddressValueError:
                errors.append(ErrorFactory.parsing_error(loc, value, "not a valid IPv6 address", ipaddress.IPv6Address))
                return Unset

    return IPv6TypeDescriptor()
