"""Class skeleton - Board (package ``game``).

Phase 2 class design, MyReversi, Group 13.
Phase 1 change: ``rows``/``cols`` became one ``size`` (6, 8 or 10) for the
"custom boards" feature, and ``executeFlip`` was split into
``pieces_to_flip`` (check) and ``place_piece`` / ``flip_pieces`` (do).
"""
from typing import List, Optional, Tuple

from .cell import Cell
from .piece import PieceColor

Position = Tuple[int, int]          # (row, col)

DIRECTIONS: List[Position] = [      # the 8 outflanking directions
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]
SUPPORTED_SIZES = (6, 8, 10)


class InvalidMoveError(ValueError):
    """Raised when a move breaks the rules. The board is left unchanged."""


class Board:
    """The square grid and the placement rules (outflank and flip).

    Associations:
      * Game  "1" *-- "1" Board            (is played on)
      * Board "1" *-- "size x size" Cell   (is made of)
    """

    def __init__(self, size: int = 8) -> None:
        """Create an empty ``size`` x ``size`` grid.

        Raises ``ValueError`` if ``size`` is not in ``SUPPORTED_SIZES``.
        """
        self.size: int = size
        self.cells: List[List[Cell]] = []

    # --- set-up -----------------------------------------------------------
    def initialize(self) -> None:
        """Clear the grid and place the 4 starting pieces in the centre."""
        ...

    # --- queries ----------------------------------------------------------
    def in_bounds(self, row: int, col: int) -> bool:
        """True if (row, col) is on the board."""
        ...

    def get_cell(self, row: int, col: int) -> Cell:
        ...

    def pieces_to_flip(self, row: int, col: int, color: PieceColor) -> List[Cell]:
        """Cells that would flip if ``color`` played at (row, col).

        Empty list means the move is illegal (occupied, off board, or
        outflanks nothing). Walks all 8 ``DIRECTIONS``.
        """
        ...

    def is_valid_move(self, row: int, col: int, color: PieceColor) -> bool:
        ...

    def get_valid_moves(self, color: PieceColor) -> List[Position]:
        """Every legal square for ``color``; used to highlight moves (UC-02 step 1)."""
        ...

    def has_valid_move(self, color: PieceColor) -> bool:
        """Used by Game to decide skip (UC-03) or game over (UC-04)."""
        ...

    def count(self, color: PieceColor) -> int:
        """Number of pieces of ``color`` on the board (the score)."""
        ...

    def is_full(self) -> bool:
        ...

    # --- commands ---------------------------------------------------------
    def place_piece(self, row: int, col: int, color: PieceColor) -> List[Cell]:
        """Place a piece and flip every outflanked opponent piece.

        Returns the flipped cells. Raises ``InvalidMoveError`` if illegal.
        """
        ...

    def flip_pieces(self, cells: List[Cell]) -> None:
        ...

    # --- copying and storage ----------------------------------------------
    def copy(self) -> 'Board':
        """Independent copy, used by ComputerPlayer to try moves."""
        ...

    def to_list(self) -> List[List[Optional[str]]]:
        """Rows of 'black' / 'white' / None, stored in GameRecord.board_state."""
        ...

    @classmethod
    def from_list(cls, grid: List[List[Optional[str]]]) -> 'Board':
        """Rebuild a board from ``to_list()`` output."""
        ...
