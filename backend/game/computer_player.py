"""Computer opponent with three difficulty levels.

- easy:   picks a random legal move
- normal: greedy, scores each move with a positional weight table
- hard:   alpha-beta minimax over the positional score plus mobility
"""
import random

from .player import Player

DIFFICULTIES = ('easy', 'normal', 'hard')
HARD_SEARCH_DEPTH = 3
# Bigger boards have many more moves per turn; search one ply less so the
# computer still answers within the 2 second target of UC-05.
LARGE_BOARD_SEARCH_DEPTH = 2

CORNER = 100
X_SQUARE = -50   # diagonal neighbour of a corner: tends to give the corner away
C_SQUARE = -20   # orthogonal neighbour of a corner
EDGE = 10


def position_weights(size):
    """Weight table that values corners and edges and avoids corner neighbours."""
    last = size - 1
    weights = [[1] * size for _ in range(size)]
    for r in range(size):
        for c in range(size):
            if r in (0, last) or c in (0, last):
                weights[r][c] = EDGE
    for cr, cc in ((0, 0), (0, last), (last, 0), (last, last)):
        dr = 1 if cr == 0 else -1
        dc = 1 if cc == 0 else -1
        weights[cr][cc] = CORNER
        weights[cr + dr][cc + dc] = X_SQUARE
        weights[cr][cc + dc] = C_SQUARE
        weights[cr + dr][cc] = C_SQUARE
    return weights


class ComputerPlayer(Player):
    is_computer = True

    def __init__(self, color, difficulty='normal', name='Computer', rng=None):
        if difficulty not in DIFFICULTIES:
            raise ValueError(f'Difficulty must be one of {DIFFICULTIES}')
        super().__init__(name, color)
        self.difficulty_level = difficulty
        self._rng = rng or random.Random()

    def make_move(self, board):
        moves = board.get_valid_moves(self.get_color())
        if not moves:
            return None
        if self.difficulty_level == 'easy':
            return self._rng.choice(moves)
        if self.difficulty_level == 'normal':
            return self._best_greedy_move(board, moves)
        return self._calculate_best_move(board, moves)

    def _best_greedy_move(self, board, moves):
        weights = position_weights(board.size)
        color = self.get_color()
        scores = {
            (r, c): weights[r][c] + len(board.pieces_to_flip(r, c, color))
            for r, c in moves
        }
        best = max(scores.values())
        return self._rng.choice([m for m, s in scores.items() if s == best])

    def _calculate_best_move(self, board, moves):
        weights = position_weights(board.size)
        me = self.get_color()
        depth = HARD_SEARCH_DEPTH if board.size <= 8 else LARGE_BOARD_SEARCH_DEPTH
        best_score, best_moves = None, []
        for r, c in moves:
            child = board.copy()
            child.place_piece(r, c, me)
            score = self._minimax(child, depth - 1, float('-inf'),
                                  float('inf'), me.opponent, weights)
            if best_score is None or score > best_score:
                best_score, best_moves = score, [(r, c)]
            elif score == best_score:
                best_moves.append((r, c))
        return self._rng.choice(best_moves)

    def _minimax(self, board, depth, alpha, beta, to_move, weights):
        moves = board.get_valid_moves(to_move)
        if depth == 0 or (not moves and not board.has_valid_move(to_move.opponent)):
            return self._evaluate(board, weights)
        if not moves:
            # to_move must pass; the opponent plays again
            return self._minimax(board, depth - 1, alpha, beta, to_move.opponent, weights)

        maximising = to_move == self.get_color()
        best = float('-inf') if maximising else float('inf')
        for r, c in moves:
            child = board.copy()
            child.place_piece(r, c, to_move)
            score = self._minimax(child, depth - 1, alpha, beta, to_move.opponent, weights)
            if maximising:
                best = max(best, score)
                alpha = max(alpha, best)
            else:
                best = min(best, score)
                beta = min(beta, best)
            if beta <= alpha:
                break
        return best

    def _evaluate(self, board, weights):
        me, them = self.get_color(), self.get_color().opponent
        my_moves = len(board.get_valid_moves(me))
        their_moves = len(board.get_valid_moves(them))
        if my_moves == 0 and their_moves == 0:
            diff = board.count(me) - board.count(them)
            return diff + (10_000 if diff > 0 else -10_000 if diff < 0 else 0)
        positional = 0
        for r in range(board.size):
            for c in range(board.size):
                color = board.get_cell(r, c).get_color()
                if color == me:
                    positional += weights[r][c]
                elif color == them:
                    positional -= weights[r][c]
        return positional + 5 * (my_moves - their_moves)
