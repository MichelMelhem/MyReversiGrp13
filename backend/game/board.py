"""The Reversi grid and its placement rules (outflanking and flipping)."""
from .cell import Cell
from .piece import Piece, PieceColor

DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]

SUPPORTED_SIZES = (6, 8, 10)


class InvalidMoveError(ValueError):
    pass


class Board:
    def __init__(self, size=8):
        if size not in SUPPORTED_SIZES:
            raise ValueError(f'Board size must be one of {SUPPORTED_SIZES}')
        self.size = size
        self.cells = [[Cell(r, c) for c in range(size)] for r in range(size)]

    def initialize(self):
        """Clear the board and place the four starting pieces in the centre."""
        for row in self.cells:
            for cell in row:
                cell.set_piece(None)
        mid = self.size // 2
        self.cells[mid - 1][mid - 1].set_piece(Piece(PieceColor.WHITE))
        self.cells[mid][mid].set_piece(Piece(PieceColor.WHITE))
        self.cells[mid - 1][mid].set_piece(Piece(PieceColor.BLACK))
        self.cells[mid][mid - 1].set_piece(Piece(PieceColor.BLACK))

    def in_bounds(self, row, col):
        return 0 <= row < self.size and 0 <= col < self.size

    def get_cell(self, row, col):
        return self.cells[row][col]

    def pieces_to_flip(self, row, col, color):
        """Cells outflanked if ``color`` plays at (row, col); empty if illegal."""
        color = PieceColor(color)
        if not self.in_bounds(row, col) or not self.cells[row][col].is_empty():
            return []
        flips = []
        for dr, dc in DIRECTIONS:
            line = []
            r, c = row + dr, col + dc
            while self.in_bounds(r, c) and self.cells[r][c].get_color() == color.opponent:
                line.append(self.cells[r][c])
                r, c = r + dr, c + dc
            if line and self.in_bounds(r, c) and self.cells[r][c].get_color() == color:
                flips.extend(line)
        return flips

    def is_valid_move(self, row, col, color):
        return bool(self.pieces_to_flip(row, col, color))

    def get_valid_moves(self, color):
        return [
            (r, c)
            for r in range(self.size)
            for c in range(self.size)
            if self.is_valid_move(r, c, color)
        ]

    def has_valid_move(self, color):
        return any(
            self.is_valid_move(r, c, color)
            for r in range(self.size)
            for c in range(self.size)
        )

    def place_piece(self, row, col, color):
        """Place a piece and flip every outflanked opponent piece.

        Returns the list of flipped cells. Raises InvalidMoveError if illegal.
        """
        if not self.in_bounds(row, col):
            raise InvalidMoveError('That square is not on the board.')
        if not self.cells[row][col].is_empty():
            raise InvalidMoveError('That square is already occupied.')
        flips = self.pieces_to_flip(row, col, color)
        if not flips:
            raise InvalidMoveError('That square does not outflank any opponent piece.')
        self.cells[row][col].set_piece(Piece(color))
        self.flip_pieces(flips)
        return flips

    def flip_pieces(self, cells):
        for cell in cells:
            cell.get_piece().flip()

    def count(self, color):
        color = PieceColor(color)
        return sum(1 for row in self.cells for cell in row if cell.get_color() == color)

    @property
    def black_count(self):
        return self.count(PieceColor.BLACK)

    @property
    def white_count(self):
        return self.count(PieceColor.WHITE)

    def is_full(self):
        return all(not cell.is_empty() for row in self.cells for cell in row)

    def copy(self):
        return Board.from_list(self.to_list())

    def to_list(self):
        """Serialise as rows of 'black' / 'white' / None."""
        return [
            [None if cell.is_empty() else cell.get_color().value for cell in row]
            for row in self.cells
        ]

    @classmethod
    def from_list(cls, grid):
        board = cls(len(grid))
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value is not None:
                    board.cells[r][c].set_piece(Piece(value))
        return board
