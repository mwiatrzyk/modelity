class Loc(tuple):
    """Object used to keep error location."""

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return ".".join(str(x) for x in self)
