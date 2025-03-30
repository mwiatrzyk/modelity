class UnsetType:
    """Singleton type for representing unset or undefined values.

    It has only one global instance to allow fast is-a tests in the code and
    always evaluates to ``False``.
    """

    __slots__: list = []

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "Unset"

    def __bool__(self):
        return False


#: Singleton instance of the UnsetType.
Unset = UnsetType()
