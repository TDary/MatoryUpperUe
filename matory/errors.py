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
