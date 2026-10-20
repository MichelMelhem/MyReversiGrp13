"""Class skeletons - Player, HumanPlayer, ComputerPlayer (package ``game``).

Phase 2 class design, MyReversi, Group 13.
In the code these live in player.py, human_player.py and computer_player.py.
"""
import random
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from .board import Board
from .piece import PieceColor

Position = Tuple[int, int]


class Player(ABC):
    """Anyone taking part in a game (abstract).

    Associations:
      * Game "1" o-- "2 {ordered}" Player   (is played by; index 0 = Black)
      * Player --> "1" PieceColor           (plays as)
    """

    is_computer: bool = False

    def __init__(self, name: str, color: PieceColor) -> None:
        self._name: str = name
        self._color: PieceColor = PieceColor(color)
        self.score: int = 0                 # pieces on the board, set by Game

    @abstractmethod
    def make_move(self, board: Board) -> Optional[Position]:
        """Return the (row, col) to play, or ``None`` if there is no move."""

    def update_score(self, points: int) -> None:
        ...

    def get_name(self) -> str:
        ...

    def get_color(self) -> PieceColor:
        ...


class HumanPlayer(Player):
    """A person playing through the web client (UC-02).

    Phase 1 ``selectGridPosition()`` became ``select_square()``.
    """

    def __init__(self, name: str, color: PieceColor) -> None:
        super().__init__(name, color)
        self._pending_move: Optional[Position] = None

    def select_square(self, row: int, col: int) -> None:
        """Remember the square the user clicked."""
        ...

    def make_move(self, board: Board) -> Optional[Position]:
        """Return and clear the square chosen with ``select_square``."""
        ...


DIFFICULTIES = ('easy', 'normal', 'hard')


class ComputerPlayer(Player):
    """The computer opponent (UC-05).

    * easy   - random legal move
    * normal - greedy, uses a corner/edge weight table
    * hard   - alpha-beta minimax, depth 3 (depth 2 on 10x10 so it
               still answers within the 2 second target of UC-05)
    """

    is_computer = True

    def __init__(self, color: PieceColor, difficulty: str = 'normal',
                 name: str = 'Computer', rng: Optional[random.Random] = None) -> None:
        """Raises ``ValueError`` if ``difficulty`` is not in ``DIFFICULTIES``."""
        super().__init__(name, color)
        self.difficulty_level: str = difficulty
        self._rng: random.Random = rng or random.Random()

    def make_move(self, board: Board) -> Optional[Position]:
        """Pick a move for the current difficulty; ``None`` if it must pass."""
        ...

    def _best_greedy_move(self, board: Board, moves: List[Position]) -> Position:
        ...

    def _calculate_best_move(self, board: Board, moves: List[Position]) -> Position:
        """Search each move with ``_minimax`` on a copy of the board."""
        ...

    def _minimax(self, board: Board, depth: int, alpha: float, beta: float,
                 to_move: PieceColor, weights: List[List[int]]) -> float:
        ...

    def _evaluate(self, board: Board, weights: List[List[int]]) -> float:
        """Position weights + 5 x mobility; +/-10000 for a won/lost end."""
        ...
