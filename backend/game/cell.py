# Cell: one square of the board.
from .piece import Piece


class Cell:
    """One square of the board. Holds zero or one Piece."""

    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.piece = None           # Piece or None

    def set_piece(self, piece):
        # put a piece on the cell, or clear it with None.
        if piece is not None and not isinstance(piece, Piece):
            raise TypeError("piece must be a Piece or None")
        self.piece = piece

    def get_piece(self):
        return self.piece

    def is_empty(self):
        return self.piece is None

    def get_color(self):
        # colour of the piece on this cell, or None if empty.
        return None if self.piece is None else self.piece.color

    def get_position(self):
        # (row, col) tuple."
        return (self.row, self.col)

    def get_label(self):
        # square name shown to players
        return f"{chr(ord('A') + self.col)}{self.row + 1}"

    def __repr__(self):
        return f"Cell({self.get_label()}, {self.get_color()})"
