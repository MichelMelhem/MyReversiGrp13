"""Class skeleton - GameService and GameActionError (Django app ``api``).

Phase 2 class design, MyReversi, Group 13.
Replaces the Phase 1 ``Server`` class. In the code these are module-level
functions in ``backend/api/services.py``; they are grouped here as one
<<control>> class to match the class diagram. ``GameAPI`` (views.py) only
reads the HTTP request and calls these methods.

Each public method runs in one database transaction and locks the
GameRecord row, so two requests can never change the same game at once.
"""
from datetime import timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from database.models import GameRecord
from game import Game, TurnResult


class GameActionError(Exception):
    """A request that cannot be done now; turned into an HTTP error."""

    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


class GameService:
    """Coordinates games between clients (server side of section 3.2.1)."""

    RECONNECT_WINDOW = timedelta(seconds=30)   # then the absent player forfeits

    # --- starting games ---------------------------------------------------
    @staticmethod
    def create_computer_game(name: str, board_size: int = 8,
                             difficulty: str = 'normal') -> Tuple[GameRecord, str, str]:
        """UC-05: player is Black, computer is White. Returns (record, token, colour)."""
        ...

    @staticmethod
    def join_online_game(name: str, board_size: int = 8) -> Tuple[GameRecord, str, str]:
        """UC-01: pair with a waiting player of the same size, or wait.

        Colours are drawn at random once two players are paired. Stale
        waiting games (host gone longer than RECONNECT_WINDOW) are cancelled.
        """
        ...

    # --- in-game actions ----------------------------------------------------
    @staticmethod
    def make_move(game_id: UUID, token: str, row: int, col: int) -> GameRecord:
        """UC-02: check the token, rebuild the Game, play the move, save it.

        Raises GameActionError 403 for a wrong token, 400 for a bad move.
        """
        ...

    @staticmethod
    def play_computer_turn(game_id: UUID, token: str) -> GameRecord:
        """UC-05 step 3: let the ComputerPlayer move if it is its turn."""
        ...

    @staticmethod
    def leave_game(game_id: UUID, token: str) -> GameRecord:
        """Cancel a lobby wait, or forfeit a game in progress (UC-04 variation)."""
        ...

    @staticmethod
    def poll_game(game_id: UUID, token: str) -> Tuple[GameRecord, Optional[str]]:
        """Latest state; marks the caller present and forfeits an opponent
        who has been gone longer than RECONNECT_WINDOW."""
        ...

    # --- conversion -----------------------------------------------------------
    @staticmethod
    def build_game(record: GameRecord) -> Game:
        """GameRecord -> Game + Board + Players (rebuilt on each request)."""
        ...

    @staticmethod
    def serialize(record: GameRecord, viewer: Optional[str] = None) -> Dict:
        """JSON state sent to the client: board, valid moves, scores, turn."""
        ...

    @staticmethod
    def replay_frames(record: GameRecord) -> List[Dict]:
        """Board after every move, for the replay page."""
        ...

    @staticmethod
    def _record_turn(record: GameRecord, game: Game, result: TurnResult) -> None:
        """Save a MoveRecord and the message both players will see."""
        ...

    @staticmethod
    def _finish(record: GameRecord, game: Game, reason: str) -> None:
        """Store the result and update both PlayerProfiles' totals."""
        ...
