"""Class skeleton - Cell (package ``game``).

Phase 2 class design, MyReversi, Group 13.
Phase 1 change: ``isObstacle`` was removed because obstacle tiles were
dropped from scope; custom boards are done with board size instead.
"""
from typing import Optional

from .piece import Piece, PieceColor


class Cell:
    """One square of the board, at (row, col). Holds at most one Piece.

    Associations:
      * Board "1" *-- "size x size" Cell   (is made of)
      * Cell  "1" *-- "0..1" Piece         (holds)
    """

    def __init__(self, row: int, col: int) -> None:
        self.row: int = row                 # 0 .. size-1, shown as 1..size
        self.col: int = col                 # 0 .. size-1, shown as A..
        self._piece: Optional[Piece] = None

    def set_piece(self, piece: Optional[Piece]) -> None:
        """Put a piece on the cell, or clear it with ``None``."""
        ...

    def get_piece(self) -> Optional[Piece]:
        """The piece on this cell, or ``None`` if empty."""
        ...

    def is_empty(self) -> bool:
        """True when no piece is on the cell."""
        ...

    def get_color(self) -> Optional[PieceColor]:
        """Colour of the piece on this cell, or ``None`` if empty."""
        ...

    @property
    def label(self) -> str:
        """Board coordinate shown to players, e.g. row 2, col 3 -> 'D3'."""
        ...
