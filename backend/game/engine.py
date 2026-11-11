"""Simple function interface to the rules, for the API layer.

This is the engine interface agreed for GameService in plain JSON-style
Values in (the saved board and "black"/"white"), plain values out. 
Inside, it uses the Game / Board / Player classes from the domain model.

    from game import engine

    result = engine.play_turn(game.board, game.current_turn, row, col)
    {
        "board": [[0, 0, ...], ...],   // updated board, 0 empty / 1 black / 2 white
        "next_turn": "white",          // None once the game is over
        "flipped": [[3, 3]],
        "skipped": None,               // "white" if White had to pass
        "game_over": False,
        "winner": None,                // "black", "white" or "draw" when over
        "scores": {"black": 4, "white": 1},
    }
Illegal moves raise InvalidMoveError and nothing changes.
"""

from .board import Board
from .game import Game, GameStatus
from .human_player import HumanPlayer
from .piece import PieceColor


def _load(board, current_turn):
    # rebuild a running Game from a saved board and whose turn it is.
    game = Game(
        HumanPlayer("black", PieceColor.BLACK),
        HumanPlayer("white", PieceColor.WHITE),
        board=Board.from_list(board),
    )
    game.resume(PieceColor.from_name(current_turn), GameStatus.IN_PROGRESS)
    return game


def _winner_name(game):
    if game.status is not GameStatus.FINISHED:
        return None
    winner = game.get_winner()
    return "draw" if winner is None else winner.color.value


def starting_board(size=8):
    # a new board with the 4 centre pieces as a list of int rows.
    board = Board(size)
    board.initialize()
    return board.to_list()


def valid_moves(board, colour):
    # legal [row, col] squares for black or white on a saved board.
    return [list(m) for m in Board.from_list(board).get_valid_moves(PieceColor.from_name(colour))]


def scores(board):
    b = Board.from_list(board)
    return {"black": b.count(PieceColor.BLACK), "white": b.count(PieceColor.WHITE)}


def play_turn(board, current_turn, row, col):
    """Play (row, col) for current_turn and report what happened.
    Raises InvalidMoveError if the move is illegal, ValueError if the board
    or colour is malformed.
    """
    game = _load(board, current_turn)
    result = game.play_turn(row, col)
    over = game.status is GameStatus.FINISHED
    return {
        "board": game.board.to_list(),
        "next_turn": None if over else game.get_current_player().color.value,
        "flipped": [list(pos) for pos in result.flipped],
        "skipped": result.skipped.value if result.skipped else None,
        "game_over": over,
        "winner": _winner_name(game),
        "scores": {p.color.value: p.score for p in game.players},
    }


def is_game_over(board):
    # True if neither colour can move on this board.
    b = Board.from_list(board)
    return not (b.has_valid_move(PieceColor.BLACK) or b.has_valid_move(PieceColor.WHITE))
