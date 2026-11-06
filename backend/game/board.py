"""Board: the grid of cells and the placement rules."""
from .cell import Cell
from .errors import InvalidMoveError
from .piece import Piece, PieceColor

# The 8 directions a line of pieces can run in: (row step, col step).
DIRECTIONS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

EMPTY = 0   # stored board: 0 = empty, 1 = black, 2 = white


class Board:
    """A square grid of 6x6, 8x8 or 10x10 cells (custom feature 5).

    A Position is a ``(row, col)`` tuple, both counted from 0.
    """

    SUPPORTED_SIZES = (6, 8, 10)

    def __init__(self, size=8):
        if size not in self.SUPPORTED_SIZES:
            raise ValueError(
                f"Board size must be one of {self.SUPPORTED_SIZES}, got {size!r}"
            )
        self.size = size
        self.cells = [[Cell(r, c) for c in range(size)] for r in range(size)]

    # --- set-up -----------------------------------------------------------

    def initialize(self):
        """Clear the board and place the 4 starting pieces in the centre.

        White on the top-left/bottom-right diagonal, Black on the other,
        so on 8x8 this is D4 = White, E4 = Black, D5 = Black, E5 = White.
        """
        for row in self.cells:
            for cell in row:
                cell.set_piece(None)
        m = self.size // 2
        self.cells[m - 1][m - 1].set_piece(Piece(PieceColor.WHITE))
        self.cells[m][m].set_piece(Piece(PieceColor.WHITE))
        self.cells[m - 1][m].set_piece(Piece(PieceColor.BLACK))
        self.cells[m][m - 1].set_piece(Piece(PieceColor.BLACK))

    # --- lookups ------------------------------------------------------------

    def in_bounds(self, row, col):
        return 0 <= row < self.size and 0 <= col < self.size

    def get_cell(self, row, col):
        if not self.in_bounds(row, col):
            raise InvalidMoveError(f"({row}, {col}) is off the board")
        return self.cells[row][col]

    def all_cells(self):
        """Every cell, row by row."""
        return [cell for row in self.cells for cell in row]

    # --- rules --------------------------------------------------------------

    def pieces_to_flip(self, row, col, color):
        """Cells that would be flipped if ``color`` played at (row, col).

        Returns an empty list if the square is off the board, occupied,
        or the move outflanks nothing.
        """
        if not self.in_bounds(row, col) or not self.cells[row][col].is_empty():
            return []
        opponent = color.opponent()
        to_flip = []
        for dr, dc in DIRECTIONS:
            line = []
            r, c = row + dr, col + dc
            # Walk over a run of opponent pieces...
            while self.in_bounds(r, c) and self.cells[r][c].get_color() is opponent:
                line.append(self.cells[r][c])
                r += dr
                c += dc
            # ...which only counts if it is closed off by one of our own.
            if line and self.in_bounds(r, c) and self.cells[r][c].get_color() is color:
                to_flip.extend(line)
        return to_flip

    def is_valid_move(self, row, col, color):
        """True if the move outflanks at least one opponent piece."""
        return bool(self.pieces_to_flip(row, col, color))

    def get_valid_moves(self, color):
        """All (row, col) positions ``color`` can play, in row order.
        Used to highlight possible moves (custom feature 4)."""
        return [
            (r, c)
            for r in range(self.size)
            for c in range(self.size)
            if self.is_valid_move(r, c, color)
        ]

    def has_valid_move(self, color):
        """True if ``color`` has at least one legal move (drives UC-03/UC-04).
        Stops at the first legal move it finds."""
        return any(
            self.is_valid_move(r, c, color)
            for r in range(self.size)
            for c in range(self.size)
        )

    def place_piece(self, row, col, color):
        """Play a move: place a piece and flip every outflanked piece.

        Returns the list of flipped cells. Raises InvalidMoveError and leaves
        the board unchanged if the move is not legal.
        """
        if not self.in_bounds(row, col):
            raise InvalidMoveError(f"({row}, {col}) is off the board")
        cell = self.cells[row][col]
        if not cell.is_empty():
            raise InvalidMoveError(f"{cell.get_label()} is already taken")
        to_flip = self.pieces_to_flip(row, col, color)
        if not to_flip:
            raise InvalidMoveError(
                f"{cell.get_label()} does not outflank any {color.opponent().value} pieces"
            )
        cell.set_piece(Piece(color))
        self.flip_pieces(to_flip)
        return to_flip

    def flip_pieces(self, cells):
        for cell in cells:
            cell.get_piece().flip()

    # --- state --------------------------------------------------------------

    def count(self, color):
        """Number of pieces of this colour (that player's score)."""
        return sum(1 for cell in self.all_cells() if cell.get_color() is color)

    def is_full(self):
        return all(not cell.is_empty() for cell in self.all_cells())

    def copy(self):
        """Independent deep copy, used by the computer's search."""
        return Board.from_list(self.to_list())

    def to_list(self):
        """The board as rows of ints: 0 empty, 1 black, 2 white.
        This is exactly what ``database.models.Game.board`` stores."""
        return [
            [EMPTY if cell.is_empty() else cell.get_color().code for cell in row]
            for row in self.cells
        ]

    @staticmethod
    def from_list(grid):
        """Rebuild a Board from ``to_list()`` output (or a saved Game.board).

        Raises ValueError if the grid is not square, has an unsupported
        size, or contains anything other than 0, 1 or 2.
        """
        size = len(grid)
        if any(len(row) != size for row in grid):
            raise ValueError("Board grid must be square")
        board = Board(size)
        for r, row in enumerate(grid):
            for c, code in enumerate(row):
                if code != EMPTY:
                    board.cells[r][c].set_piece(Piece(PieceColor.from_code(code)))
        return board

    def __str__(self):
        width = len(str(self.size))
        header = " " * (width + 1) + " ".join(chr(ord("A") + c) for c in range(self.size))
        chars = {EMPTY: ".", 1: "B", 2: "W"}
        rows = [
            f"{r + 1:>{width}} " + " ".join(chars[v] for v in row)
            for r, row in enumerate(self.to_list())
        ]
        return "\n".join([header, *rows])
