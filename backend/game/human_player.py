"""A human taking part through the web client."""
from .player import Player


class HumanPlayer(Player):
    def __init__(self, name, color):
        super().__init__(name, color)
        self._pending_move = None

    def select_square(self, row, col):
        """Record the square the user clicked; consumed by make_move()."""
        self._pending_move = (row, col)

    def make_move(self, board):
        move, self._pending_move = self._pending_move, None
        return move
