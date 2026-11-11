#PieceColor and Piece.
from enum import Enum


class PieceColor(Enum):
    # the two sides of a disc. Black always moves first.

    BLACK = "black"
    WHITE = "white"

    def opponent(self):
        # return the other colour.
        return PieceColor.WHITE if self is PieceColor.BLACK else PieceColor.BLACK

    @property
    def code(self):
        # number used in the stored/JSON board: 1 = black, 2 = white, 0 = empty
        return 1 if self is PieceColor.BLACK else 2

    @classmethod
    def from_code(cls, code):
        # raises ValueError for anything else.
        for color in cls:
            if color.code == code:
                return color
        raise ValueError(f"Unknown piece code: {code!r}")

    @classmethod
    def from_name(cls, name):
        # "black" -> BLACK, "white" -> WHITE
        try:
            return cls(name)
        except ValueError:
            raise ValueError(f"Unknown colour: {name!r}") from None


class Piece:
    # a disc on the board. Sits on exactly one Cell.

    def __init__(self, color):
        if not isinstance(color, PieceColor):
            raise TypeError("color must be a PieceColor")
        self.color = color

    def flip(self):
        self.color = self.color.opponent()

    def get_color(self):
        return self.color

    def __repr__(self):
        return f"Piece({self.color.name})"
