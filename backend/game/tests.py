"""Tests for the game rules.

Plain unittest (no Django needed), so either of these works from backend/:
    python manage.py test game
    python -m unittest game.tests
"""
import unittest

from game import engine
import random

from game import (
    Board, Cell, Game, GameActionError, GameOverError, GameStatus,
    HumanPlayer, InvalidMoveError, NotYourTurnError, Piece, PieceColor,
)

B, W = PieceColor.BLACK, PieceColor.WHITE


CODES = {".": 0, "B": 1, "W": 2}


def grid(*rows):
    """Build a stored board (ints) from readable strings, e.g.
    grid("BW....", "......", ...) -> [[1, 2, 0, 0, 0, 0], [0, ...], ...]."""
    return [[CODES[ch] for ch in row] for row in rows]


def new_game(board=None, size=8):
    return Game(HumanPlayer("Ana", B), HumanPlayer("Ben", W), board=board, size=size)


class PieceAndCellTests(unittest.TestCase):
    def test_opponent(self):
        self.assertIs(B.opponent(), W)
        self.assertIs(W.opponent(), B)

    def test_flip(self):
        piece = Piece(B)
        piece.flip()
        self.assertIs(piece.get_color(), W)

    def test_cell_empty_and_label(self):
        cell = Cell(2, 3)
        self.assertTrue(cell.is_empty())
        self.assertIsNone(cell.get_color())
        self.assertEqual(cell.get_label(), "D3")
        cell.set_piece(Piece(W))
        self.assertIs(cell.get_color(), W)


class BoardTests(unittest.TestCase):
    def test_unsupported_size(self):
        for size in (4, 7, 12):
            with self.assertRaises(ValueError):
                Board(size)

    def test_initialize_all_sizes(self):
        for size in Board.SUPPORTED_SIZES:
            board = Board(size)
            board.initialize()
            m = size // 2
            self.assertEqual(board.count(B), 2)
            self.assertEqual(board.count(W), 2)
            self.assertIs(board.get_cell(m - 1, m - 1).get_color(), W)
            self.assertIs(board.get_cell(m - 1, m).get_color(), B)
            self.assertEqual(len(board.get_valid_moves(B)), 4)

    def test_opening_moves_8x8(self):
        board = Board(8)
        board.initialize()
        self.assertEqual(board.get_valid_moves(B), [(2, 3), (3, 2), (4, 5), (5, 4)])
        self.assertEqual(board.get_valid_moves(W), [(2, 4), (3, 5), (4, 2), (5, 3)])

    def test_place_piece_flips(self):
        board = Board(8)
        board.initialize()
        flipped = board.place_piece(2, 3, B)          # D3
        self.assertEqual([c.get_position() for c in flipped], [(3, 3)])
        self.assertEqual(board.count(B), 4)
        self.assertEqual(board.count(W), 1)

    def test_flips_in_several_directions(self):
        board = Board.from_list(grid(
            "B.B...",
            ".WW...",
            "BW.WB.",
            "......",
            "......",
            "......",
        ))
        flipped = board.place_piece(2, 2, B)
        self.assertCountEqual(
            [c.get_position() for c in flipped], [(1, 1), (1, 2), (2, 1), (2, 3)]
        )
        self.assertEqual(board.count(W), 0)

    def test_does_not_flip_unclosed_line(self):
        board = Board.from_list(grid(
            ".WWW..",
            "......", "......", "......", "......", "......",
        ))
        self.assertFalse(board.is_valid_move(0, 0, B))   # no black piece closes it

    def test_illegal_moves_raise_and_leave_board_unchanged(self):
        board = Board(8)
        board.initialize()
        before = board.to_list()
        for row, col in [(0, 0), (3, 3), (-1, 4), (8, 0)]:
            with self.assertRaises(InvalidMoveError):
                board.place_piece(row, col, B)
        self.assertEqual(board.to_list(), before)

    def test_matches_api_encoding(self):
        # Same starting board as GameService.starting_board on main.
        board = Board(8)
        board.initialize()
        grid8 = board.to_list()
        self.assertEqual(grid8[3][3], 2)
        self.assertEqual(grid8[3][4], 1)
        self.assertEqual(grid8[4][3], 1)
        self.assertEqual(grid8[4][4], 2)
        self.assertEqual(sum(v == 0 for row in grid8 for v in row), 60)

    def test_to_list_from_list_round_trip_and_copy(self):
        board = Board(6)
        board.initialize()
        clone = Board.from_list(board.to_list())
        self.assertEqual(clone.to_list(), board.to_list())
        copy = board.copy()
        copy.place_piece(*copy.get_valid_moves(B)[0], B)
        self.assertNotEqual(copy.to_list(), board.to_list())   # original untouched

    def test_from_list_rejects_bad_grids(self):
        with self.assertRaises(ValueError):
            Board.from_list([[0] * 7 for _ in range(7)])       # size 7
        with self.assertRaises(ValueError):
            Board.from_list([[0] * 6 for _ in range(5)])       # not square
        bad = [[0] * 6 for _ in range(6)]
        bad[0][0] = 3
        with self.assertRaises(ValueError):
            Board.from_list(bad)


class GameTests(unittest.TestCase):
    def test_players_must_match_colours(self):
        with self.assertRaises(ValueError):
            Game(HumanPlayer("Ana", W), HumanPlayer("Ben", B))

    def test_start(self):
        game = new_game()
        self.assertIs(game.status, GameStatus.WAITING)
        game.start()
        self.assertIs(game.status, GameStatus.IN_PROGRESS)
        self.assertIs(game.get_current_player().color, B)
        self.assertEqual([p.score for p in game.players], [2, 2])
        with self.assertRaises(GameActionError):
            game.start()

    def test_cannot_play_before_start(self):
        with self.assertRaises(GameActionError):
            new_game().play_turn(2, 3)

    def test_play_turn_switches_player_and_updates_scores(self):
        game = new_game()
        game.start()
        result = game.play_turn(2, 3, B)
        self.assertEqual(result.flipped, [(3, 3)])
        self.assertIsNone(result.skipped)
        self.assertFalse(result.game_over)
        self.assertIs(game.get_current_player().color, W)
        self.assertEqual(game.get_player(B).score, 4)
        self.assertEqual(game.get_player(W).score, 1)

    def test_not_your_turn(self):
        game = new_game()
        game.start()
        with self.assertRaises(NotYourTurnError):
            game.play_turn(2, 4, W)
        # NotYourTurnError is also an InvalidMoveError
        with self.assertRaises(InvalidMoveError):
            game.play_turn(2, 4, W)

    def test_invalid_move_keeps_turn(self):
        game = new_game()
        game.start()
        with self.assertRaises(InvalidMoveError):
            game.play_turn(0, 0)
        self.assertIs(game.get_current_player().color, B)

    def test_skip_then_game_over(self):
        board = Board.from_list(grid(
            "BW....",
            "......", "......", "......", "......",
            "BW....",
        ))
        game = new_game(board)
        game.resume(B, GameStatus.IN_PROGRESS)

        # After Black takes row 0, White's only piece (F row) cannot move: skip.
        result = game.play_turn(0, 2)
        self.assertIs(result.skipped, W)
        self.assertFalse(result.game_over)
        self.assertIs(game.get_current_player().color, B)

        # Black's next move takes White's last piece: nobody can move.
        result = game.play_turn(5, 2)
        self.assertTrue(result.game_over)
        self.assertIs(game.status, GameStatus.FINISHED)
        self.assertIs(game.get_winner().color, B)
        with self.assertRaises(GameOverError):
            game.play_turn(1, 1)
        self.assertEqual(game.valid_moves(), [])

    def test_draw(self):
        board = Board.from_list(grid(
            "BBBWWW",
            "BBBWWW",
            "BBBWWW",
            "BBBWWW",
            "BBBWWW",
            "BBBWWW",
        ))
        game = new_game(board)
        game.resume(B, GameStatus.IN_PROGRESS)
        self.assertTrue(game.check_game_over())
        self.assertIsNone(game.get_winner())
        self.assertTrue(game.is_draw())

    def test_forfeit(self):
        game = new_game()
        game.start()
        game.forfeit(B)
        self.assertIs(game.status, GameStatus.FINISHED)
        self.assertIs(game.get_winner().color, W)
        with self.assertRaises(GameOverError):
            game.forfeit(W)

    def test_resume_restores_turn(self):
        game = new_game()
        game.start()
        game.play_turn(2, 3)
        saved = game.board.to_list()

        restored = new_game(Board.from_list(saved))
        restored.resume(W, GameStatus.IN_PROGRESS)
        self.assertIs(restored.get_current_player().color, W)
        self.assertEqual(restored.valid_moves(), game.valid_moves())
        self.assertEqual(restored.get_player(B).score, 4)


class PlayerTests(unittest.TestCase):
    def test_human_pending_move(self):
        human = HumanPlayer("Ana", B)
        self.assertIsNone(human.make_move(None))
        human.select_square(2, 3)
        self.assertEqual(human.make_move(None), (2, 3))
        self.assertIsNone(human.make_move(None))     # used once


class EngineTests(unittest.TestCase):
    """The function interface used by GameService."""

    def test_opening_move(self):
        result = engine.play_turn(engine.starting_board(8), "black", 2, 3)
        self.assertEqual(result["flipped"], [[3, 3]])
        self.assertEqual(result["next_turn"], "white")
        self.assertIsNone(result["skipped"])
        self.assertFalse(result["game_over"])
        self.assertIsNone(result["winner"])
        self.assertEqual(result["scores"], {"black": 4, "white": 1})
        self.assertEqual(result["board"][2][3], 1)
        self.assertEqual(result["board"][3][3], 1)

    def test_input_board_is_not_modified(self):
        board = engine.starting_board(8)
        before = [row[:] for row in board]
        engine.play_turn(board, "black", 2, 3)
        self.assertEqual(board, before)

    def test_illegal_move_raises_value_error(self):
        board = engine.starting_board(8)
        with self.assertRaises(InvalidMoveError):
            engine.play_turn(board, "black", 0, 0)
        with self.assertRaises(ValueError):     # what the API view turns into 400
            engine.play_turn(board, "black", 3, 3)

    def test_bad_colour(self):
        with self.assertRaises(ValueError):
            engine.play_turn(engine.starting_board(8), "red", 2, 3)

    def test_skip_and_win(self):
        board = grid("BW....", "......", "......", "......", "......", "BW....")
        first = engine.play_turn(board, "black", 0, 2)
        self.assertEqual(first["skipped"], "white")
        self.assertEqual(first["next_turn"], "black")
        last = engine.play_turn(first["board"], first["next_turn"], 5, 2)
        self.assertTrue(last["game_over"])
        self.assertIsNone(last["next_turn"])
        self.assertEqual(last["winner"], "black")
        self.assertTrue(engine.is_game_over(last["board"]))

    def test_draw_result(self):
        # Black's last move leaves 3 black and 3 white, nobody can move.
        board = grid("BW.WWW", "......", "......", "......", "......", "......")
        result = engine.play_turn(board, "black", 0, 2)
        self.assertTrue(result["game_over"])
        self.assertEqual(result["winner"], "draw")

    def test_valid_moves_and_scores(self):
        board = engine.starting_board(6)
        self.assertEqual(engine.valid_moves(board, "black"), [[1, 2], [2, 1], [3, 4], [4, 3]])
        self.assertEqual(engine.scores(board), {"black": 2, "white": 2})


class FullGameTests(unittest.TestCase):
    """Play whole games with random legal moves and check the rules hold."""

    def play_out(self, size, seed):
        rng = random.Random(seed)
        game = new_game(size=size)
        game.start()
        moves = 0
        while game.status is GameStatus.IN_PROGRESS:
            before = game.board.count(B) + game.board.count(W)
            result = game.play_turn(*rng.choice(game.valid_moves()))
            moves += 1
            self.assertEqual(game.board.count(B) + game.board.count(W), before + 1)
            self.assertTrue(result.flipped)
        self.assertEqual(game.board.count(B) + game.board.count(W), 4 + moves)
        self.assertFalse(game.board.has_valid_move(B) or game.board.has_valid_move(W))
        return game

    def test_random_games_all_sizes(self):
        for size in Board.SUPPORTED_SIZES:
            for seed in range(5):
                with self.subTest(size=size, seed=seed):
                    game = self.play_out(size, seed)
                    scores = [p.score for p in game.players]
                    self.assertEqual(sum(scores), game.board.count(B) + game.board.count(W))


if __name__ == "__main__":
    unittest.main()
