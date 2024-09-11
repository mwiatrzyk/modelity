class UndefinedType:
    """Type for representing undefined values.

    This type is used by Modelity to distinguish between unset values and f.e.
    values set to ``None``.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "Undefined"

    def __bool__(self):
        return False


#: Singleton instance of the UndefinedType
Undefined = UndefinedType()
