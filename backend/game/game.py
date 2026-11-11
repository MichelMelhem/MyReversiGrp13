# Game: turns, skipping and the end of the game.
from dataclasses import dataclass, field
from enum import Enum

from .board import Board
from .errors import GameActionError, GameOverError, NotYourTurnError
from .piece import PieceColor


class GameStatus(Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


@dataclass
class TurnResult:
    """What happened when a move was played, returned by Game.play_turn.
    skipped is the colour that had to pass because it had no legal move. 
    game_over is True if this move ended the game.
    """

    color: PieceColor
    row: int
    col: int
    flipped: list = field(default_factory=list)   # [(row, col), ...]
    skipped: PieceColor = None
    game_over: bool = False


class Game:
    """Controls one game of Reversi.
    players[0] is black and players[1] is white.
    """

    def __init__(self, black, white, board=None, size=8):
        if black.color is not PieceColor.BLACK or white.color is not PieceColor.WHITE:
            raise ValueError("black must play BLACK and white must play WHITE")
        self.players = [black, white]
        self.board = board if board is not None else Board(size)
        self.current_player_index = 0
        self.status = GameStatus.WAITING
        self.forfeited_by = None    # PieceColor or None

    # --- starting -----------------------------------------------------------

    def start(self):
        # set up a new board and give black the first move.
        if self.status is not GameStatus.WAITING:
            raise GameActionError("The game has already started")
        self.board.initialize()
        self.current_player_index = 0
        self.status = GameStatus.IN_PROGRESS
        self.forfeited_by = None
        self._update_scores()

    def resume(self, current_color, status, forfeited_by=None):
        """Continue a saved game: the board was passed to the constructor, this
        restores whose turn it is and the status (used by GameService on
        each request)."""
        self.current_player_index = self._index_of(current_color)
        self.status = status
        self.forfeited_by = forfeited_by
        self._update_scores()

    # queries

    def get_current_player(self):
        return self.players[self.current_player_index]

    def get_player(self, color):
        return self.players[self._index_of(color)]

    def valid_moves(self):
        # legal moves for the player whose turn it is ([] if not in progress).
        if self.status is not GameStatus.IN_PROGRESS:
            return []
        return self.board.get_valid_moves(self.get_current_player().color)

    # playing

    def play_turn(self, row, col, color=None):
        """Play a move for the current player, then pass the turn,
        skip the opponent or end the game.
        color is the color of the player asking to move; if given, it
        must be the current player's. 
        Raises GameOverError, NotYourTurnError,
        GameActionError or InvalidMoveError. 
        On any error nothing changes.
        """
        if self.status is GameStatus.FINISHED:
            raise GameOverError("The game is over")
        if self.status is GameStatus.WAITING:
            raise GameActionError("The game has not started yet")

        mover = self.get_current_player().color
        if color is not None and color is not mover:
            raise NotYourTurnError(f"It is {mover.value}'s turn")

        flipped = self.board.place_piece(row, col, mover)
        result = TurnResult(
            color=mover,
            row=row,
            col=col,
            flipped=[cell.get_position() for cell in flipped],
        )
        self._advance_turn(result)
        self._update_scores()
        return result

    def check_game_over(self):
        """True if the game is finished. Also ends the game if neither player
        can move (e.g. a saved game that was left in that position)."""
        if self.status is GameStatus.FINISHED:
            return True
        if self.status is GameStatus.IN_PROGRESS and not (
            self.board.has_valid_move(PieceColor.BLACK)
            or self.board.has_valid_move(PieceColor.WHITE)
        ):
            self.status = GameStatus.FINISHED
            return True
        return False

    def forfeit(self, color):
        # color gives up so the other player wins.
        if self.status is GameStatus.FINISHED:
            raise GameOverError("The game is already over")
        self.forfeited_by = color
        self.status = GameStatus.FINISHED

    def get_winner(self):
        # the winning Player, or None for a draw or an unfinished game."""
        if self.status is not GameStatus.FINISHED:
            return None
        if self.forfeited_by is not None:
            return self.get_player(self.forfeited_by.opponent())
        black = self.board.count(PieceColor.BLACK)
        white = self.board.count(PieceColor.WHITE)
        if black == white:
            return None
        return self.get_player(PieceColor.BLACK if black > white else PieceColor.WHITE)

    def is_draw(self):
        return self.status is GameStatus.FINISHED and self.get_winner() is None

    # internals

    def _advance_turn(self, result):
        mover = result.color
        opponent = mover.opponent()
        if self.board.has_valid_move(opponent):
            self.current_player_index = self._index_of(opponent)
        elif self.board.has_valid_move(mover):
            result.skipped = opponent
        else:
            self.status = GameStatus.FINISHED
            result.game_over = True

    def _update_scores(self):
        for player in self.players:
            player.update_score(self.board.count(player.color))

    @staticmethod
    def _index_of(color):
        return 0 if color is PieceColor.BLACK else 1
