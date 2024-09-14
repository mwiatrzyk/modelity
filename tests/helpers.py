from typing import Tuple, Type
from modelity.error import Error
from modelity.loc import Loc


class ErrorFactoryHelper:

    @staticmethod
    def integer_required(loc: Loc):
        return Error.create(loc, "modelity.IntegerRequired")

    @staticmethod
    def unsupported_type(loc: Loc, supported_types: Tuple[Type, ...]):
        return Error.create(loc, "modelity.UnsupportedType", supported_types=supported_types)

    @staticmethod
    def required_missing(loc: Loc):
        return Error.create(loc, "modelity.RequiredMissing")
