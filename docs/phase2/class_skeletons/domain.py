"""MyReversi - class skeletons for the game rules (package: game).

Based on the refined domain class diagram (Fig. 1).
"""
from abc import ABC, abstractmethod
from enum import Enum


class PieceColor(Enum):
    BLACK = "black"
    WHITE = "white"

    def opponent(self):
        """Return the other colour."""
        pass


class GameStatus(Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class InvalidMoveError(Exception):
    """Raised when a move breaks the rules."""


class Piece:
    """A disc on the board."""

    def __init__(self, color):
        self.color = color          # PieceColor

    def flip(self):
        """Change to the opponent's colour."""
        pass


class Cell:
    """One square of the board. Holds 0 or 1 Piece."""

    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.piece = None           # Piece or None

    def is_empty(self):
        pass


class Board:
    """The grid of cells (6x6, 8x8 or 10x10) and the placement rules."""

    def __init__(self, size=8):
        self.size = size
        self.cells = []             # size x size Cells

    def initialize(self):
        """Place the 4 starting pieces in the centre."""
        pass

    def is_valid_move(self, row, col, color):
        """True if the move outflanks at least one opponent piece."""
        pass

    def get_valid_moves(self, color):
        """List of (row, col) the player can play (shown to the user)."""
        pass

    def place_piece(self, row, col, color):
        """Place a piece and flip the outflanked pieces.
        Raises InvalidMoveError if the move is not legal."""
        pass

    def count(self, color):
        """Number of pieces of this colour (the score)."""
        pass


class Player(ABC):
    """A player in the game (human or computer)."""

    def __init__(self, name, color):
        self.name = name
        self.color = color          # PieceColor
        self.score = 0

    @abstractmethod
    def make_move(self, board):
        """Return the (row, col) to play."""
        pass


class HumanPlayer(Player):
    """A person playing in the browser."""

    def make_move(self, board):
        pass


class ComputerPlayer(Player):
    """The computer opponent (UC-05)."""

    def __init__(self, color, difficulty="normal"):
        super().__init__("Computer", color)
        self.difficulty = difficulty  # "easy", "normal" or "hard"

    def make_move(self, board):
        """Choose a move depending on the difficulty."""
        pass


class Game:
    """Controls one game: turns, skipping and the end of the game."""

    def __init__(self, black, white, size=8):
        self.players = [black, white]   # 2 Players, Black first
        self.board = Board(size)
        self.current_player_index = 0   # 0 = Black, 1 = White
        self.status = GameStatus.WAITING

    def start(self):
        """Set up the board. Black plays first (UC-01)."""
        pass

    def play_turn(self, row, col):
        """Play a move for the current player (UC-02),
        then pass the turn, skip (UC-03) or end the game (UC-04)."""
        pass

    def check_game_over(self):
        """True when neither player can move."""
        pass

    def forfeit(self, color):
        """End the game; the other player wins."""
        pass

    def get_winner(self):
        """Return the winning Player, or None for a draw."""
        pass
