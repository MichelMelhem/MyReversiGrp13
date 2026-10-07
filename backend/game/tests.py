"""Rule tests for the pure-Python game package (no database needed)."""
import random
from unittest import TestCase

from . import (
    Board, ComputerPlayer, Game, GameStatus, HumanPlayer, InvalidMoveError,
    NotYourTurnError, PieceColor,
)

B, W = PieceColor.BLACK, PieceColor.WHITE


def new_game(size=8):
    game = Game(HumanPlayer('Anna', B), HumanPlayer('Tim', W), size=size)
    game.start()
    return game


def board_from(rows):
    """Build a board from strings: 'B', 'W' or '.' per square."""
    lookup = {'B': 'black', 'W': 'white', '.': None}
    return Board.from_list([[lookup[ch] for ch in row] for row in rows])


class BoardTests(TestCase):
    def test_starting_position(self):
        board = Board()
        board.initialize()
        self.assertEqual(board.black_count, 2)
        self.assertEqual(board.white_count, 2)
        self.assertEqual(board.get_cell(3, 3).get_color(), W)
        self.assertEqual(board.get_cell(3, 4).get_color(), B)

    def test_black_has_four_opening_moves(self):
        board = Board()
        board.initialize()
        self.assertEqual(sorted(board.get_valid_moves(B)), [(2, 3), (3, 2), (4, 5), (5, 4)])

    def test_occupied_and_non_flanking_squares_are_illegal(self):
        board = Board()
        board.initialize()
        self.assertFalse(board.is_valid_move(3, 3, B))   # occupied
        self.assertFalse(board.is_valid_move(0, 0, B))   # flanks nothing
        with self.assertRaises(InvalidMoveError):
            board.place_piece(0, 0, B)
        self.assertEqual(board.black_count, 2)            # unchanged

    def test_flips_in_multiple_directions(self):
        board = board_from([
            'B.B.B...',
            '.WWW....',
            'BW.WB...',
            '.WWW....',
            'B.B.B...',
            '........',
            '........',
            '........',
        ])
        flipped = board.place_piece(2, 2, B)
        self.assertEqual(len(flipped), 8)
        self.assertEqual(board.white_count, 0)

    def test_serialisation_round_trip(self):
        board = Board(6)
        board.initialize()
        self.assertEqual(Board.from_list(board.to_list()).to_list(), board.to_list())

    def test_unsupported_size(self):
        with self.assertRaises(ValueError):
            Board(7)


class GameTests(TestCase):
    def test_turn_passes_to_white(self):
        game = new_game()
        result = game.play_turn(2, 3)
        self.assertEqual(result.flipped, [(3, 3)])
        self.assertEqual(game.current_player.get_color(), W)
        self.assertEqual(game.players[0].score, 4)

    def test_wrong_player_rejected(self):
        game = new_game()
        with self.assertRaises(NotYourTurnError):
            game.play_turn(2, 3, color=W)

    def test_skip_when_opponent_has_no_move(self):
        # After Black plays A1, White has no move but Black still does (C6).
        board = board_from([
            '.WB.....',
            '........',
            '........',
            '........',
            '........',
            'BW......',
            '........',
            'W.B.....',
        ])
        game = Game(HumanPlayer('a', B), HumanPlayer('b', W), board=board)
        game.resume(B)
        result = game.play_turn(0, 0)
        self.assertEqual(result.skipped, W)
        self.assertFalse(result.game_over)
        self.assertEqual(game.current_player.get_color(), B)

    def test_game_over_and_winner(self):
        board = board_from(['WWWWWWWW'] * 7 + ['BBBBBBW.'])
        game = Game(HumanPlayer('a', B), HumanPlayer('b', W), board=board)
        game.resume(B)
        result = game.play_turn(7, 7)
        self.assertTrue(result.game_over)
        self.assertEqual(game.status, GameStatus.FINISHED)
        self.assertEqual(game.get_winner().get_color(), W)

    def test_forfeit_overrides_score(self):
        game = new_game()
        game.forfeit(W)
        self.assertEqual(game.get_winner().get_color(), B)

    def test_full_computer_game_terminates(self):
        for size in (6, 8, 10):
            black = ComputerPlayer(B, 'normal', rng=random.Random(1))
            white = ComputerPlayer(W, 'easy', rng=random.Random(2))
            game = Game(black, white, size=size)
            game.start()
            while game.status == GameStatus.IN_PROGRESS:
                row, col = game.current_player.make_move(game.board)
                game.play_turn(row, col)
            self.assertTrue(game.check_game_over())
            self.assertEqual(game.players[0].score + game.players[1].score,
                             sum(1 for r in game.board.to_list() for v in r if v))


class ComputerPlayerTests(TestCase):
    def test_takes_corner_when_available(self):
        board = board_from([
            '.WWB....',
            '........',
            '........',
            '...WB...',
            '...BW...',
            '........',
            '........',
            '........',
        ])
        for level in ('normal', 'hard'):
            move = ComputerPlayer(B, level, rng=random.Random(0)).make_move(board)
            self.assertEqual(move, (0, 0), level)

    def test_returns_none_without_moves(self):
        board = board_from(['BBBBBBBB'] * 8)
        self.assertIsNone(ComputerPlayer(W, 'hard').make_move(board))
