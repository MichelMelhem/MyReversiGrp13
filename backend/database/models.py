"""Persistence layer: Django models for saved games, moves and players.

Keep game rules in ``game/``; models here only store and load state.
"""
from django.db import models  # noqa: F401

class Game(models.Model):
    board = models.JSONField()

    current_turn = models.CharField(max_length=10, default='black')
    status = models.CharField(max_length=20, default='waiting')
    black_player = models.CharField(max_length=100, null=True, blank=True)
    white_player = models.CharField(max_length=100, null=True, blank=True)
    def __str__(self):
        return f'Game {self.id} - {self.status}'