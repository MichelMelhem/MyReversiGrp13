"""Class skeletons - persistence entities (Django app ``database``).

Phase 2 class design, MyReversi, Group 13.
New since Phase 1: these classes store games so that both browsers see
the same state, and they back the history, replay and leaderboard features.
"""
import uuid

from django.db import models


class PlayerProfile(models.Model):
    """A named player and their totals (leaderboard)."""

    name = models.CharField(max_length=30, unique=True)
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    draws = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def games_played(self) -> int:
        ...


class GameRecord(models.Model):
    """The saved form of one Game.

    Associations:
      * GameRecord "0..*" --> "0..1" PlayerProfile  (black seat / white seat)
        A null seat in a computer game is the computer.
      * GameRecord "1" *-- "0..*" MoveRecord        (records, ordered by number)
    """

    class Mode(models.TextChoices):
        COMPUTER = 'computer'
        ONLINE = 'online'

    class Status(models.TextChoices):
        WAITING = 'waiting'
        IN_PROGRESS = 'in_progress'
        FINISHED = 'finished'
        CANCELLED = 'cancelled'

    class Result(models.TextChoices):
        BLACK = 'black'
        WHITE = 'white'
        DRAW = 'draw'

    class EndReason(models.TextChoices):
        NO_MOVES = 'no_moves'
        FORFEIT = 'forfeit'
        DISCONNECT = 'disconnect'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mode = models.CharField(max_length=10, choices=Mode.choices)
    difficulty = models.CharField(max_length=10, blank=True)
    board_size = models.PositiveSmallIntegerField(default=8)
    board_state = models.JSONField()                 # Board.to_list()
    current_color = models.CharField(max_length=5, default='black')
    status = models.CharField(max_length=12, choices=Status.choices)

    black_player = models.ForeignKey(PlayerProfile, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name='+')
    white_player = models.ForeignKey(PlayerProfile, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name='+')
    black_token = models.CharField(max_length=64, blank=True)   # secret per seat
    white_token = models.CharField(max_length=64, blank=True)
    black_last_seen = models.DateTimeField(null=True, blank=True)
    white_last_seen = models.DateTimeField(null=True, blank=True)

    black_count = models.PositiveSmallIntegerField(default=2)
    white_count = models.PositiveSmallIntegerField(default=2)
    result = models.CharField(max_length=5, choices=Result.choices, blank=True)
    end_reason = models.CharField(max_length=10, choices=EndReason.choices, blank=True)
    last_event = models.CharField(max_length=200, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def player_name(self, color: str) -> str:
        """Name for a seat, 'Computer (normal)' for the computer, or None."""
        ...

    def color_for_token(self, token: str) -> str:
        """'black' / 'white' for a matching token, else None.

        Uses a constant-time comparison so the token cannot be guessed
        from response timing.
        """
        ...


class MoveRecord(models.Model):
    """One played move, kept for the move list, history and replay."""

    game = models.ForeignKey(GameRecord, on_delete=models.CASCADE, related_name='moves')
    number = models.PositiveIntegerField()           # unique per game
    color = models.CharField(max_length=5)
    row = models.PositiveSmallIntegerField()
    col = models.PositiveSmallIntegerField()
    flipped_count = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def label(self) -> str:
        """e.g. 'D3'."""
        ...
