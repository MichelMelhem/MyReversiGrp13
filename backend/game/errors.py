"""Errors raised by the game rules.

``InvalidMoveError`` is the parent of every "move not allowed" error, so the
API layer can catch them all as one type (UC-02 extension 2a).

Both base classes extend ValueError, so the existing API views already turn
them into HTTP 400 responses without any extra ``except`` clauses.
"""


class InvalidMoveError(ValueError):
    """The move breaks the Reversi rules (occupied square, nothing flipped,
    off the board)."""


class NotYourTurnError(InvalidMoveError):
    """A player tried to move when it is the other player's turn."""


class GameOverError(InvalidMoveError):
    """A player tried to move (or forfeit) after the game has finished."""


class GameActionError(ValueError):
    """An action that is not a move is not allowed right now
    (e.g. starting a game twice, playing before the game has started)."""
