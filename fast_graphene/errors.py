class FastGrapheneException(Exception):
    pass


class CircularDependencyException(FastGrapheneException):
    pass


class InvalidCallableException(FastGrapheneException):
    """Raises at when using wrong arguments to define resolver."""

    pass
