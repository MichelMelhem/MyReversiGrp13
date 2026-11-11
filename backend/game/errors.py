# Errors raised by the game rules.


class InvalidMoveError(ValueError):
    pass
    # the move breaks the Reversi rules (occupied square, nothing flipped, off the board).


class NotYourTurnError(InvalidMoveError):
    pass
    # a player tried to move when it is the other player's turn.


class GameOverError(InvalidMoveError):
    pass
    # a player tried to move (or forfeit) after the game has finished.


class GameActionError(ValueError):
    pass
    # an action that is not a move is not allowed right now
    # e.g.) starting a game twice, playing before the game has started.
