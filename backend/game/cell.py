"""One square of the board. Holds at most one Piece."""


class Cell:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self._piece = None

    def set_piece(self, piece):
        self._piece = piece

    def get_piece(self):
        return self._piece

    def is_empty(self):
        return self._piece is None

    def get_color(self):
        """Colour of the piece on this cell, or None if the cell is empty."""
        return None if self._piece is None else self._piece.get_color()

    @property
    def label(self):
        """Human-readable coordinate, e.g. row 2 col 3 -> 'D3'."""
        return f'{chr(ord("A") + self.col)}{self.row + 1}'
