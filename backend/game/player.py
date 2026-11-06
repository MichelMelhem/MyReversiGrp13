"""Player: abstract participant in a game."""
from abc import ABC, abstractmethod

from .piece import PieceColor


class Player(ABC):
    """A player in the game (human or computer)."""

    is_computer = False

    def __init__(self, name, color):
        if not isinstance(color, PieceColor):
            raise TypeError("color must be a PieceColor")
        self.name = name
        self.color = color
        self.score = 0

    @abstractmethod
    def make_move(self, board):
        """Return the (row, col) to play, or None if there is no move."""

    def update_score(self, points):
        """Set the score (the number of pieces this player has on the board)."""
        self.score = points

    def get_name(self):
        return self.name

    def get_color(self):
        return self.color

    def __repr__(self):
        return f"{type(self).__name__}({self.name!r}, {self.color.name}, score={self.score})"
