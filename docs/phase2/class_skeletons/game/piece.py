"""Class skeleton - Piece and PieceColor (package ``game``).

Phase 2 class design, MyReversi, Group 13.
Bodies are left as ``...``; the full code is in ``backend/game/piece.py``.
"""
from enum import Enum


class PieceColor(str, Enum):
    """The two sides of a disc. Black always moves first."""

    BLACK = 'black'
    WHITE = 'white'

    @property
    def opponent(self) -> 'PieceColor':
        """The other colour (BLACK <-> WHITE)."""
        ...


class Piece:
    """A single disc on the board.

    Association: owned by exactly one ``Cell`` (composition, 0..1 per cell).
    A piece never moves; it only changes colour when it is outflanked.
    """

    def __init__(self, color: PieceColor) -> None:
        self._color: PieceColor = PieceColor(color)

    def flip(self) -> None:
        """Turn the disc over so it shows the opponent's colour (UC-02 step 3)."""
        ...

    def get_color(self) -> PieceColor:
        """Colour currently shown."""
        ...
