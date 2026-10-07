"""Base class for anyone taking part in a game."""
from abc import ABC, abstractmethod

from .piece import PieceColor


class Player(ABC):
    is_computer = False

    def __init__(self, name, color):
        self._name = name
        self._color = PieceColor(color)
        self.score = 0

    @abstractmethod
    def make_move(self, board):
        """Return the (row, col) this player wants to play, or None to pass."""

    def update_score(self, points):
        self.score = points

    def get_name(self):
        return self._name

    def get_color(self):
        return self._color
