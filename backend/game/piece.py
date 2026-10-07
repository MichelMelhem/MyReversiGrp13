"""A single Reversi disc. One side is black, the other white."""
from enum import Enum


class PieceColor(str, Enum):
    BLACK = 'black'
    WHITE = 'white'

    @property
    def opponent(self):
        return PieceColor.WHITE if self is PieceColor.BLACK else PieceColor.BLACK


class Piece:
    def __init__(self, color):
        self._color = PieceColor(color)

    def flip(self):
        self._color = self._color.opponent

    def get_color(self):
        return self._color

    def __repr__(self):
        return f'Piece({self._color.value})'
