"""Persistence layer: Django models for saved games, moves and players.

Keep game rules in ``game/``; models here only store and load state.
"""
import secrets
import uuid

from django.db import models


def new_token():
    return secrets.token_urlsafe(24)


class PlayerProfile(models.Model):
    """A named player, used for the leaderboard and game history."""
    name = models.CharField(max_length=30, unique=True)
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    draws = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def games_played(self):
        return self.wins + self.losses + self.draws

    def __str__(self):
        return self.name


class GameRecord(models.Model):
    class Mode(models.TextChoices):
        COMPUTER = 'computer'
        ONLINE = 'online'

    class Status(models.TextChoices):
        WAITING = 'waiting'          # online game waiting for an opponent
        IN_PROGRESS = 'in_progress'
        FINISHED = 'finished'
        CANCELLED = 'cancelled'      # left the lobby before an opponent joined

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
    board_state = models.JSONField()
    current_color = models.CharField(max_length=5, default='black')
    status = models.CharField(max_length=12, choices=Status.choices)

    # In a computer game the computer's slot has a null profile and empty token.
    black_player = models.ForeignKey(PlayerProfile, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name='+')
    white_player = models.ForeignKey(PlayerProfile, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name='+')
    black_token = models.CharField(max_length=64, blank=True)
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

    class Meta:
        ordering = ['-created_at']

    def player_name(self, color):
        profile = self.black_player if color == 'black' else self.white_player
        if profile is not None:
            return profile.name
        if self.mode == self.Mode.COMPUTER:
            return f'Computer ({self.difficulty})'
        return None

    def color_for_token(self, token):
        if token and secrets.compare_digest(token, self.black_token):
            return 'black'
        if token and secrets.compare_digest(token, self.white_token):
            return 'white'
        return None


class MoveRecord(models.Model):
    """One move (or forced pass) in a game, kept for history and replay."""
    game = models.ForeignKey(GameRecord, on_delete=models.CASCADE, related_name='moves')
    number = models.PositiveIntegerField()
    color = models.CharField(max_length=5)
    row = models.PositiveSmallIntegerField()
    col = models.PositiveSmallIntegerField()
    flipped_count = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['number']
        constraints = [
            models.UniqueConstraint(fields=['game', 'number'], name='unique_move_number'),
        ]

    @property
    def label(self):
        return f'{chr(ord("A") + self.col)}{self.row + 1}'
