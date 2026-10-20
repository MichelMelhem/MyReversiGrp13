"""Class skeleton - Game, GameStatus, TurnResult (package ``game``).

Phase 2 class design, MyReversi, Group 13.
Phase 1 change: ``currentTurn: Player`` became ``current_player_index`` and
``gameState: String`` became the ``GameStatus`` enumeration. ``Move`` was
replaced by ``TurnResult`` (what one turn did) and, on the server, by
``MoveRecord`` (the saved move).
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple

from .board import Board, InvalidMoveError
from .piece import PieceColor
from .player import Player

Position = Tuple[int, int]


class GameStatus(str, Enum):
    WAITING = 'waiting'
    IN_PROGRESS = 'in_progress'
    FINISHED = 'finished'


class NotYourTurnError(InvalidMoveError):
    """A player tried to move when it is the opponent's turn."""


class GameOverError(InvalidMoveError):
    """A move was sent after the game ended."""


@dataclass
class TurnResult:
    """What happened in one call to ``Game.play_turn`` (a value object)."""

    color: PieceColor                                   # who moved
    row: int
    col: int
    flipped: List[Position] = field(default_factory=list)
    skipped: Optional[PieceColor] = None                # UC-03: who had to pass
    game_over: bool = False                             # UC-04


class Game:
    """One game: turn order, skipping, end of game and the result.

    Associations:
      * Game "1" o-- "2 {ordered}" Player   (is played by)
      * Game "1" *-- "1" Board              (is played on)
      * Game ..> TurnResult                 (<<create>>)
    """

    def __init__(self, black: Player, white: Player,
                 board: Optional[Board] = None, size: int = 8) -> None:
        """Raises ``ValueError`` unless ``black`` is BLACK and ``white`` is WHITE."""
        self.players: List[Player] = [black, white]
        self.board: Board = board if board is not None else Board(size)
        self.current_player_index: int = 0
        self.status: GameStatus = GameStatus.WAITING
        self.forfeited_by: Optional[PieceColor] = None

    def start(self) -> None:
        """Set up the starting position; Black moves first (UC-01 step 5)."""
        ...

    def resume(self, current_color: PieceColor,
               status: GameStatus = GameStatus.IN_PROGRESS) -> None:
        """Continue a game loaded from a GameRecord instead of starting fresh."""
        ...

    @property
    def current_player(self) -> Player:
        ...

    def get_player(self, color: PieceColor) -> Player:
        ...

    def valid_moves(self) -> List[Position]:
        """Legal squares for the player to move; empty if not in progress."""
        ...

    def play_turn(self, row: int, col: int,
                  color: Optional[PieceColor] = None) -> TurnResult:
        """Play (row, col) for the current player (UC-02).

        Raises ``GameOverError`` if the game is not in progress,
        ``NotYourTurnError`` if ``color`` is given and is not the mover,
        ``InvalidMoveError`` if the square is illegal (board unchanged).
        """
        ...

    def _advance_turn(self, result: TurnResult) -> None:
        """Pass the turn, or skip the opponent (UC-03), or end the game (UC-04)."""
        ...

    def check_game_over(self) -> bool:
        ...

    def forfeit(self, color: PieceColor) -> None:
        """End now; the other player wins whatever the score (leave / disconnect)."""
        ...

    def get_winner(self) -> Optional[Player]:
        """Winner, or ``None`` for a draw or an unfinished game."""
        ...

    def _update_scores(self) -> None:
        ...
