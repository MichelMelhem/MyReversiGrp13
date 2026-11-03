"""MyReversi - class skeletons for the server (packages: api, database).

Based on the refined system class diagram (Fig. 2).
In the real code the three record classes are Django models.
"""


class PlayerProfile:
    """A player's name and results, used for the leaderboard."""

    def __init__(self, name):
        self.name = name
        self.wins = 0
        self.losses = 0
        self.draws = 0


class GameRecord:
    """A saved game, so both players see the same board."""

    def __init__(self, mode, board_size):
        self.id = None              # unique game id
        self.mode = mode            # "computer" or "online"
        self.board_size = board_size
        self.board_state = []       # the board as a list of rows
        self.status = "waiting"     # waiting, in_progress, finished, cancelled
        self.black_player = None    # PlayerProfile (None = computer)
        self.white_player = None
        self.black_token = ""       # secret token for each player
        self.white_token = ""
        self.result = ""            # "black", "white" or "draw"
        self.moves = []             # list of MoveRecord

    def color_for_token(self, token):
        """Return "black" or "white" for a valid token, else None."""
        pass


class MoveRecord:
    """One move, kept for the game history and replay."""

    def __init__(self, number, color, row, col):
        self.number = number
        self.color = color
        self.row = row
        self.col = col


class GameService:
    """Runs the games on the server (replaces Server from Phase 1)."""

    def create_computer_game(self, name, board_size, difficulty):
        """Start a game against the computer (UC-05)."""
        pass

    def join_online_game(self, name, board_size):
        """Pair with a waiting player, or wait for one (UC-01)."""
        pass

    def make_move(self, game_id, token, row, col):
        """Check the token, play the move and save the game (UC-02)."""
        pass

    def play_computer_turn(self, game_id, token):
        """Let the computer play its move (UC-05)."""
        pass

    def leave_game(self, game_id, token):
        """The player leaves: they forfeit the game."""
        pass

    def poll_game(self, game_id, token):
        """Return the current game state to the client
        (called every 1.5 s)."""
        pass
