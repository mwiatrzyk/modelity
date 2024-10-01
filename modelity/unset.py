class UnsetType:
    """Type for representing unset values.

    Modelity keeps clean separation between values that are not set, and values
    that are f.e. set to ``None`` and this type is used to enforce that.
    """

    __slots__: tuple = tuple()

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "Unset"

    def __bool__(self):
        return False


#: Singleton instance of the UnsetType
Unset = UnsetType()
