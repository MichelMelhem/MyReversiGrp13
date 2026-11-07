"""Python Reversi rules for board, pieces, players, and turn logic.

    from game import Game, HumanPlayer, PieceColor

    game = Game(HumanPlayer("Ana", PieceColor.BLACK),
                HumanPlayer("Ben", PieceColor.WHITE))
    game.start()
    result = game.play_turn(2, 3)        # Black plays D3
    result = game.play_turn(2, 2)        # White replies

The API layer works with saved JSON boards, so it uses ``game.engine``
(play_turn, valid_moves, scores) instead of the classes directly.
"""
from . import engine
from .board import Board
from .cell import Cell
from .errors import GameActionError, GameOverError, InvalidMoveError, NotYourTurnError
from .game import Game, GameStatus, TurnResult
from .human_player import HumanPlayer
from .piece import Piece, PieceColor
from .player import Player

__all__ = [
    "Board", "Cell", "Game", "GameActionError", "GameOverError",
    "GameStatus", "HumanPlayer", "InvalidMoveError", "NotYourTurnError", "Piece",
    "PieceColor", "Player", "TurnResult", "engine",
]
