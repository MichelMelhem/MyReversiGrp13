"""Turn sequencing, skipping, game over and result for one Reversi game."""
from dataclasses import dataclass, field
from enum import Enum

from .board import Board, InvalidMoveError
from .piece import PieceColor


class GameStatus(str, Enum):
    WAITING = 'waiting'
    IN_PROGRESS = 'in_progress'
    FINISHED = 'finished'


class NotYourTurnError(InvalidMoveError):
    pass


class GameOverError(InvalidMoveError):
    pass


@dataclass
class TurnResult:
    """What happened as a result of one call to Game.play_turn()."""
    color: PieceColor
    row: int
    col: int
    flipped: list = field(default_factory=list)   # [(row, col), ...]
    skipped: PieceColor = None                    # colour whose turn was skipped
    game_over: bool = False


class Game:
    def __init__(self, black, white, board=None, size=8):
        if black.get_color() != PieceColor.BLACK or white.get_color() != PieceColor.WHITE:
            raise ValueError('First player must be black and second player white.')
        self.players = [black, white]
        self.board = board if board is not None else Board(size)
        self.current_player_index = 0
        self.status = GameStatus.WAITING
        self.forfeited_by = None

    def start(self):
        """Set up the starting position; Black moves first."""
        self.board.initialize()
        self.current_player_index = 0
        self.status = GameStatus.IN_PROGRESS
        self._update_scores()

    def resume(self, current_color, status=GameStatus.IN_PROGRESS):
        """Continue a game loaded from storage instead of starting a new one."""
        self.current_player_index = 0 if PieceColor(current_color) == PieceColor.BLACK else 1
        self.status = GameStatus(status)
        self._update_scores()

    @property
    def current_player(self):
        return self.players[self.current_player_index]

    def get_player(self, color):
        return self.players[0 if PieceColor(color) == PieceColor.BLACK else 1]

    def valid_moves(self):
        if self.status != GameStatus.IN_PROGRESS:
            return []
        return self.board.get_valid_moves(self.current_player.get_color())

    def play_turn(self, row, col, color=None):
        """Play (row, col) for the current player.

        ``color`` lets callers assert who is moving; a mismatch raises
        NotYourTurnError. Illegal squares raise InvalidMoveError and leave
        the board unchanged.
        """
        if self.status != GameStatus.IN_PROGRESS:
            raise GameOverError('The game is not in progress.')
        mover = self.current_player.get_color()
        if color is not None and PieceColor(color) != mover:
            raise NotYourTurnError('It is not your turn.')

        flipped = self.board.place_piece(row, col, mover)
        result = TurnResult(mover, row, col, [(c.row, c.col) for c in flipped])
        self._update_scores()
        self._advance_turn(result)
        return result

    def _advance_turn(self, result):
        mover = self.current_player.get_color()
        if self.board.has_valid_move(mover.opponent):
            self.current_player_index = 1 - self.current_player_index
        elif self.board.has_valid_move(mover):
            result.skipped = mover.opponent   # opponent passes, mover plays again
        else:
            self.status = GameStatus.FINISHED
            result.game_over = True

    def check_game_over(self):
        if self.status == GameStatus.IN_PROGRESS and \
                not self.board.has_valid_move(PieceColor.BLACK) and \
                not self.board.has_valid_move(PieceColor.WHITE):
            self.status = GameStatus.FINISHED
        return self.status == GameStatus.FINISHED

    def forfeit(self, color):
        """End the game immediately; the other player wins regardless of score."""
        self.forfeited_by = PieceColor(color)
        self.status = GameStatus.FINISHED

    def get_winner(self):
        """Winning Player, or None for a draw / unfinished game."""
        if self.status != GameStatus.FINISHED:
            return None
        if self.forfeited_by is not None:
            return self.get_player(self.forfeited_by.opponent)
        black, white = self.board.black_count, self.board.white_count
        if black == white:
            return None
        return self.players[0] if black > white else self.players[1]

    def _update_scores(self):
        self.players[0].update_score(self.board.black_count)
        self.players[1].update_score(self.board.white_count)
