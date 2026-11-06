"""PieceColor and Piece."""
from enum import Enum


class PieceColor(Enum):
    """The two sides of a disc. Black always moves first."""

    BLACK = "black"
    WHITE = "white"

    def opponent(self):
        """Return the other colour."""
        return PieceColor.WHITE if self is PieceColor.BLACK else PieceColor.BLACK

    @property
    def code(self):
        """Number used in the stored/JSON board: 1 = black, 2 = white
        (0 is an empty square). Same encoding as the API and frontend."""
        return 1 if self is PieceColor.BLACK else 2

    @classmethod
    def from_code(cls, code):
        """Inverse of ``code``. Raises ValueError for anything else."""
        for color in cls:
            if color.code == code:
                return color
        raise ValueError(f"Unknown piece code: {code!r}")

    @classmethod
    def from_name(cls, name):
        """"black" -> BLACK, "white" -> WHITE (the API's current_turn strings)."""
        try:
            return cls(name)
        except ValueError:
            raise ValueError(f"Unknown colour: {name!r}") from None


class Piece:
    """A disc on the board. It always sits on exactly one Cell."""

    def __init__(self, color):
        if not isinstance(color, PieceColor):
            raise TypeError("color must be a PieceColor")
        self.color = color

    def flip(self):
        """Turn the disc over to the opponent's colour."""
        self.color = self.color.opponent()

    def get_color(self):
        return self.color

    def __repr__(self):
        return f"Piece({self.color.name})"
