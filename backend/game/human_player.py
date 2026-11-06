"""HumanPlayer: a person playing in the browser."""
from .player import Player


class HumanPlayer(Player):
    """A person playing in the browser.

    The square they clicked is stored with ``select_square`` and handed
    back once by ``make_move``.
    """

    def __init__(self, name, color):
        super().__init__(name, color)
        self.pending_move = None    # (row, col) or None

    def select_square(self, row, col):
        self.pending_move = (row, col)

    def make_move(self, board):
        """Return the selected square and clear it. Returns None if nothing
        has been selected. Legality is checked by the Board, not here."""
        move = self.pending_move
        self.pending_move = None
        return move
