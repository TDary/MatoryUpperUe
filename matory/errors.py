"""Matory exception hierarchy."""


class MatoryError(Exception):
    """Base exception for all Matory errors."""


class CommandError(MatoryError):
    """Server returned a non-zero response code.

    Attributes:
        code: The numeric error code from the server.
        msg:  The human-readable error message from the server.
    """

    def __init__(self, code: int, msg: str) -> None:
        self.code = code
        self.msg = msg
        super().__init__(f"CommandError(code={code}, msg={msg!r})")


class WidgetNotFoundError(MatoryError):
    """No widget matched the given locator.

    Attributes:
        method: The lookup method used ("id", "name", or "path").
        value:  The locator value that had no match.
    """

    def __init__(self, method: str, value: str) -> None:
        self.method = method
        self.value = value
        super().__init__(f"WidgetNotFoundError(method={method!r}, value={value!r})")


class ConnectionKeyError(MatoryError):
    """No connection found with the given key.

    Attributes:
        key: The connection key that was not found.
        available: List of existing connection keys.
    """

    def __init__(self, key: str, available: list[str]) -> None:
        self.key = key
        self.available = available
        super().__init__(
            f"ConnectionKeyError(key={key!r}, available={available!r})"
        )


class MatoryConnectionError(MatoryError):
    """TCP connection to the UE SDK server failed or was lost."""

    def __init__(self, message: str = "Connection error") -> None:
        super().__init__(message)
